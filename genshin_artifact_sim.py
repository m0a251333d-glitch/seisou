#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原神 聖遺物シミュレータ（モンテカルロ）
==========================================
「現在の5部位 → 目標ステータスを満たす5部位構成になるまで何日かかるか」を
多数回シミュレートし、平均・中央値・パーセンタイルを出力する。

実装範囲
  - 聖遺物生成（セット/部位/メインOP/サブOP重み付き非復元抽選/3or4OP/初期値4段階）
  - 強化（+4,+8,+12,+16,+20。3OPは+4で新規OP追加、4OPは5回とも強化）
  - 廃棄ルール（初期条件・途中チェックポイント）
  - 廻聖（不要★5×3 → 指定セット1個）
  - 聖遺物の定義（エリクシル）/ 聖啓の塵（再構築）… 任意（デフォルト無効）
  - 5部位の全組み合わせ評価（numpyで一括）＋ 4セット+オフピース判定
  - 樹脂 180/日、秘境 20樹脂/周、★5 平均1.06個/周

未実装（簡略化）
  - 強化経験値の収支（EXP素材は無限にある前提）
  - 聖啓の塵の Advanced/Decreed の段階（保証回数は一定値で扱う）
  - ★4以下の聖遺物、ダメージ計算

使い方
  python artifact_sim.py                       # デフォルト設定で実行
  python artifact_sim.py --sims 20000 --seed 1
  python artifact_sim.py --config my.json      # DEFAULT_CONFIG を上書き(JSON)
  python artifact_sim.py --dump-config > my.json
"""
import argparse
import json
import math
import os
import random
import sys
import time
from multiprocessing import Pool

try:
    import numpy as np  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:
    raise SystemExit("このスクリプトには NumPy が必要です。`pip install numpy` を実行してください。") from exc

# ---------------------------------------------------------------------------
# 1. ゲームデータ（確率表）。Ver.7.1時点の有志統計ベース。変更時はここだけ直す
# ---------------------------------------------------------------------------
SLOTS = ["flower", "plume", "sands", "goblet", "circlet"]
SLOT_JA = {"flower": "花", "plume": "羽", "sands": "時計", "goblet": "杯", "circlet": "冠"}

# 最終ステータス軸。DMG=元素/物理ダメージバフ, HEAL=治療効果
STAT_KEYS = ["HP", "ATK", "DEF", "HP%", "ATK%", "DEF%", "EM", "ER", "CR", "CD", "DMG", "HEAL"]
IDX = {k: i for i, k in enumerate(STAT_KEYS)}
NS = len(STAT_KEYS)

# サブOP重み / ★5の最大値（=4段階の最高値）
SUB_WEIGHT = {"HP": 6, "ATK": 6, "DEF": 6, "HP%": 4, "ATK%": 4, "DEF%": 4,
              "ER": 4, "EM": 4, "CR": 3, "CD": 3}
SUB_MAX = {"HP": 298.75, "ATK": 19.45, "DEF": 23.15, "HP%": 5.83, "ATK%": 5.83,
           "DEF%": 7.29, "ER": 6.48, "EM": 23.31, "CR": 3.89, "CD": 7.77}
SUB_KEYS = list(SUB_WEIGHT)
ROLL_MULT = (0.7, 0.8, 0.9, 1.0)          # 各25%
ENHANCE_LEVELS = (4, 8, 12, 16, 20)

ELEMENTS = ["PYRO", "HYDRO", "ELECTRO", "CRYO", "DENDRO", "ANEMO", "GEO"]

# スロット別メインOP: {名前: (重み, Lv20値)}
MAIN_TABLE = {
    "flower": {"HP": (100, 4780)},
    "plume": {"ATK": (100, 311)},
    "sands": {"HP%": (26.68, 46.6), "ATK%": (26.66, 46.6), "DEF%": (26.66, 58.3),
              "EM": (10, 187), "ER": (10, 51.8)},
    "goblet": {"HP%": (19.25, 46.6), "ATK%": (19.25, 46.6), "DEF%": (19.0, 58.3),
               "EM": (2.5, 187), "PHYS": (5, 58.3), **{e: (5, 46.6) for e in ELEMENTS}},
    "circlet": {"HP%": (22, 46.6), "ATK%": (22, 46.6), "DEF%": (22, 58.3),
                "CR": (10, 31.1), "CD": (10, 62.2), "HEAL": (10, 35.9), "EM": (4, 187)},
}
MAIN_NAMES = {s: list(t) for s, t in MAIN_TABLE.items()}
MAIN_W = {s: [MAIN_TABLE[s][n][0] for n in MAIN_NAMES[s]] for s in SLOTS}

ELIXIR_COST = {"flower": 1, "plume": 1, "sands": 2, "goblet": 4, "circlet": 3}
DUST_COST = {"flower": 1, "plume": 1, "sands": 2, "goblet": 2, "circlet": 2}

# ---------------------------------------------------------------------------
# 2. 設定（--config でJSON上書き可）。数値は例なので必ず自分の環境に合わせて編集
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    # --- キャラクター（例: 胡桃。数値は仮。要編集）---
    "element": "PYRO",                       # 杯の元素。"PHYS"も可
    "base": {"HP": 15552, "ATK": 0, "DEF": 0},          # 基礎値(%の掛け算対象)
    # 聖遺物以外の合計(キャラ突破/武器/バフ)。HP/ATK/DEFは実数、他は%やEMそのまま
    "extra": {"HP%": 20, "ER": 100, "CR": 5, "CD": 154.6},
    # 目標(下限)。キー: HP,ATK,DEF,EM,ER,CR,CD,DMG,HEAL,HP%,ATK%,DEF%
    "targets": {"HP": 30000, "CR": 55, "CD": 190},
    "require_set_pieces": 4,                 # 目標セットの最低装備数 (4セット+1オフ)
    "set_bonus_2": {},                       # 例 {"HP%": 20}  ← 2セット効果のステ加算
    "set_bonus_4": {},                       # 例 {"CR": 36}   ← 4セット効果で常時加算する分
    # 現在の装備(0〜5個)。例:
    # {"slot":"flower","is_target":true,"main":"HP",
    #  "subs":{"CR":10.1,"CD":14.0,"HP%":5.8,"ATK":19}}
    "equipped": [],

    # --- 入手 ---
    "resin_per_day": 180,
    "initial_resin": 0,
    "max_days": 3650,                        # 打ち切り日数
    "set_rate": 0.5,                         # 秘境で目的セットが出る確率
    "domain_four_rate": 0.20,                # 秘境の初期4OP率(統計値)
    "strongbox_four_rate": 0.33,             # 廻聖の初期4OP率(統計値)
    "extra_drop_rate": 0.06,                 # 1周あたり追加★5(平均1.06個)
    "strongbox": True,                       # 廻聖を使う
    "strongbox_use_leveled": True,           # 強化済み聖遺物も廻聖素材にできる前提(要確認)
    "elixir_per_day": 0.0,                   # 1日あたり獲得エリクシル(0=無効)
    "dust_per_day": 0.0,                     # 1日あたり獲得聖啓の塵(0=無効)
    "define_four_rate": 0.20,                # 定義聖遺物の初期4OP率(仮定)
    "define_plan": {},                       # 例 {"goblet":{"main":"PYRO","subs":["CR","CD"]}}
    "reshape_guarantee": 2,                  # 再構築: 選択2OPへの合計保証回数
    "reshape_slots": [],                     # 再構築対象部位 例 ["goblet","circlet"]

    # --- 厳選ルール ---
    "skip_slots": [],                        # 全部廃棄する部位(更新しない)
    "offset_slots": [],                      # 他セットも拾う部位(4+1のオフピース)
    "main_allow": {"sands": ["HP%", "EM"], "goblet": ["PYRO"], "circlet": ["CR", "CD"]},
    "useful_substats": ["CR", "CD"],         # 有効サブOP
    "min_useful_initial": 1,                 # 初期OPに有効サブが最低いくつ
    # レベル到達時点での「有効サブへの当たり回数(新規追加含む)」下限。外れたら廃棄
    "checkpoints": {"8": 1, "20": 3},

    # --- 保管・評価 ---
    "keep_per_slot": 3,                      # 部位ごと(セット内/外別)の保管上限
    "score_weights": {"CR": 2.0, "CD": 1.0, "EM": 0.1, "HP%": 0.5, "HP": 0.01},
}

# ---------------------------------------------------------------------------
# 3. 聖遺物
# ---------------------------------------------------------------------------
def main_key(main, element):
    """メインOP名 → STAT_KEYS上のキー(None=今回のキャラに無関係)"""
    if main in ELEMENTS or main == "PHYS":
        return "DMG" if main == element else None
    return main


class Artifact:
    __slots__ = ("is_target", "slot", "main", "subs", "vec", "score")

    def __init__(self, slot, is_target, main, subs, vec, score):
        self.slot = slot
        self.is_target = is_target
        self.main = main
        self.subs = subs        # {stat: [初期倍率, 強化倍率...]} / 手入力は None
        self.vec = vec
        self.score = score


def pick_subs(rng, exclude, n):
    """重み付き非復元抽選"""
    pool = [k for k in SUB_KEYS if k not in exclude]
    out = []
    for _ in range(n):
        tot = sum(SUB_WEIGHT[k] for k in pool)
        r = rng.random() * tot
        acc = 0.0
        idx = len(pool) - 1
        for i, k in enumerate(pool):
            acc += SUB_WEIGHT[k]
            if r < acc:
                idx = i
                break
        out.append(pool.pop(idx))
    return out


def sub_value(stat, mults):
    return SUB_MAX[stat] * sum(mults)


# ---------------------------------------------------------------------------
# 4. シミュレータ
# ---------------------------------------------------------------------------
class Sim:
    def __init__(self, cfg, rng):
        self.cfg = cfg
        self.rng = rng
        self.element = cfg["element"]
        self.useful = set(cfg["useful_substats"])
        self.checkpoints = {int(k): v for k, v in cfg["checkpoints"].items()}
        self.K = cfg["keep_per_slot"]
        self.wvec = np.zeros(NS)
        for k, v in cfg["score_weights"].items():
            self.wvec[IDX[k]] = v
        self.ext = self._to_vec(cfg["extra"])
        self.b2 = self._to_vec(cfg["set_bonus_2"])
        self.b4 = self._to_vec(cfg["set_bonus_4"])
        b = cfg["base"]
        self.base = (b.get("HP", 0), b.get("ATK", 0), b.get("DEF", 0))
        self.targets = [(k, v) for k, v in cfg["targets"].items()]
        self.req_set = cfg["require_set_pieces"]
        self.inv = {(s, t): [] for s in SLOTS for t in (True, False)}
        self._cache = {s: None for s in SLOTS}
        self.fodder = 0
        self.elixir = 0.0
        self.dust = 0.0
        self.last_slot = None
        self.boxes = 0
        for e in cfg["equipped"]:
            self._equip_manual(e)

    # ---- ベクトル化 ----
    @staticmethod
    def _to_vec(d):
        v = np.zeros(NS)
        for k, x in d.items():
            v[IDX[k]] = x
        return v

    def _equip_manual(self, e):
        slot = e["slot"]
        main = e["main"]
        v = np.zeros(NS)
        mk = main_key(main, self.element)
        if mk:
            v[IDX[mk]] += MAIN_TABLE[slot][main][1]
        for k, x in e["subs"].items():
            v[IDX[k]] += x
        art = Artifact(slot, bool(e.get("is_target", True)), main, None, v, float(v @ self.wvec))
        self.inv[(slot, art.is_target)].append(art)
        self.inv[(slot, art.is_target)].sort(key=lambda a: -a.score)
        self._cache[slot] = None

    def _make(self, slot, is_target, main, subs):
        v = np.zeros(NS)
        mk = main_key(main, self.element)
        if mk:
            v[IDX[mk]] += MAIN_TABLE[slot][main][1]
        for k, m in subs.items():
            v[IDX[k]] += sub_value(k, m)
        return Artifact(slot, is_target, main, subs, v, float(v @ self.wvec))

    # ---- 強化 ----
    def _enhance(self, subs, main, checkpoints):
        """subsを破壊的に強化。checkpoints違反なら False"""
        rng, useful = self.rng, self.useful
        hits = 0
        for lvl in ENHANCE_LEVELS:
            if len(subs) < 4:
                k = pick_subs(rng, set(subs) | {main}, 1)[0]
                subs[k] = [rng.choice(ROLL_MULT)]
            else:
                k = rng.choice(list(subs))
                subs[k].append(rng.choice(ROLL_MULT))
            if k in useful:
                hits += 1
            need = checkpoints.get(lvl)
            if need and hits < need:
                return False
        return True

    # ---- 保管 ----
    def _accept(self, art):
        lst = self.inv[(art.slot, art.is_target)]
        lst.append(art)
        lst.sort(key=lambda a: -a.score)
        self._cache[art.slot] = None
        if len(lst) > self.K:
            dropped = lst.pop()
            if dropped is not art:
                self.fodder += 1 if self.cfg["strongbox_use_leveled"] else 0
            else:
                return False
        self.last_slot = art.slot
        return True

    # ---- 目標判定（5部位の全組み合わせ）----
    def _slot_arrays(self, s):
        c = self._cache[s]
        if c is None:
            items = self.inv[(s, True)] + self.inv[(s, False)]
            if items:
                V = np.array([a.vec for a in items])
                F = np.array([1 if a.is_target else 0 for a in items])
            else:
                V, F = np.zeros((1, NS)), np.zeros(1, dtype=int)
            c = self._cache[s] = (V, F)
        return c

    def goal_met(self):
        arrs = [self._slot_arrays(s) for s in SLOTS]
        tot, fl = arrs[0]
        for V, F in arrs[1:]:
            tot = tot[..., None, :] + V
            fl = fl[..., None] + F
        tot = tot + self.ext
        tot = tot + (fl >= 2)[..., None] * self.b2 + (fl >= 4)[..., None] * self.b4
        ok = fl >= self.req_set
        for k, need in self.targets:
            if k == "HP":
                val = self.base[0] * (1 + tot[..., IDX["HP%"]] / 100) + tot[..., IDX["HP"]]
            elif k == "ATK":
                val = self.base[1] * (1 + tot[..., IDX["ATK%"]] / 100) + tot[..., IDX["ATK"]]
            elif k == "DEF":
                val = self.base[2] * (1 + tot[..., IDX["DEF%"]] / 100) + tot[..., IDX["DEF"]]
            else:
                val = tot[..., IDX[k]]
            ok = ok & (val >= need)
            if not ok.any():
                return False
        return bool(ok.any())

    # ---- 入手処理 ----
    def _handle(self, slot, is_target, four_rate):
        """1個の★5を生成→厳選。目標達成なら True"""
        cfg, rng = self.cfg, self.rng
        res = self._process(slot, is_target, four_rate)
        if res == "clean":
            self.fodder += 1
        elif res == "leveled":
            self.fodder += 1 if cfg["strongbox_use_leveled"] else 0
        elif res == "kept":
            return self.goal_met()
        return False

    def _process(self, slot, is_target, four_rate):
        cfg, rng = self.cfg, self.rng
        if slot in cfg["skip_slots"]:
            return "clean"
        if not is_target and slot not in cfg["offset_slots"]:
            return "clean"
        main = rng.choices(MAIN_NAMES[slot], MAIN_W[slot])[0]
        allow = cfg["main_allow"].get(slot)
        if allow and main not in allow:
            return "clean"
        n = 4 if rng.random() < four_rate else 3
        init = pick_subs(rng, {main}, n)
        if sum(1 for k in init if k in self.useful) < cfg["min_useful_initial"]:
            return "clean"
        subs = {k: [rng.choice(ROLL_MULT)] for k in init}
        if not self._enhance(subs, main, self.checkpoints):
            return "leveled"
        art = self._make(slot, is_target, main, subs)
        return "kept" if self._accept(art) else "leveled"

    def _strongboxes(self):
        cfg, rng = self.cfg, self.rng
        if not cfg["strongbox"]:
            return False
        while self.fodder >= 3:
            self.fodder -= 3
            self.boxes += 1
            if self._handle(rng.choice(SLOTS), True, cfg["strongbox_four_rate"]):
                return True
        return False

    # ---- エリクシル(定義) / 塵(再構築) ----
    def _craft(self, slot):
        cfg, rng = self.cfg, self.rng
        plan = cfg["define_plan"][slot]
        main, chosen = plan["main"], list(plan["subs"])
        n = 4 if rng.random() < cfg["define_four_rate"] else 3
        init = chosen + pick_subs(rng, {main} | set(chosen), n - len(chosen))
        base = {k: [rng.choice(ROLL_MULT)] for k in init}
        while True:   # 選択2OPに合計2回以上の保証(棄却サンプリング)
            subs = {k: list(v) for k, v in base.items()}
            self._enhance(subs, main, {})
            if sum(len(subs[k]) - 1 for k in chosen) >= 2:
                break
        return self._accept(self._make(slot, True, main, subs))

    def _reshape(self, slot):
        rng = self.rng
        cands = [a for a in self.inv[(slot, True)]
                 if a.subs and len(a.subs) == 4
                 and sum(1 for k in a.subs if k in self.useful) >= 2]
        if not cands:
            return None
        a = cands[0]
        keys = list(a.subs)
        n_up = sum(len(v) - 1 for v in a.subs.values())
        chosen = [k for k in keys if k in self.useful][:2]
        g = self.cfg["reshape_guarantee"]
        while True:
            cnt = {k: 0 for k in keys}
            for _ in range(n_up):
                cnt[rng.choice(keys)] += 1
            if sum(cnt[k] for k in chosen) >= g:
                break
        subs = {k: [a.subs[k][0]] + [rng.choice(ROLL_MULT) for _ in range(cnt[k])] for k in keys}
        new = self._make(slot, True, a.main, subs)
        if new.score > a.score:           # 良くなった時だけ置換(確認画面で選べる想定)
            lst = self.inv[(slot, True)]
            lst[lst.index(a)] = new
            lst.sort(key=lambda x: -x.score)
            self._cache[slot] = None
            self.last_slot = slot
            return True
        return False

    def _use_resources(self):
        cfg = self.cfg
        plan = cfg["define_plan"]
        while plan and self.elixir > 0:
            opts = [s for s in plan if ELIXIR_COST[s] <= self.elixir]
            if not opts:
                break

            def best(s):
                l = self.inv[(s, True)]
                return l[0].score if l else -1.0
            s = min(opts, key=best)
            self.elixir -= ELIXIR_COST[s]
            if self._craft(s) and self.goal_met():
                return True
        for s in cfg["reshape_slots"]:
            while self.dust >= DUST_COST[s]:
                r = self._reshape(s)
                if r is None:
                    break
                self.dust -= DUST_COST[s]
                if r and self.goal_met():
                    return True
        return False

    # ---- メインループ ----
    def run(self):
        cfg, rng = self.cfg, self.rng
        rpd = cfg["resin_per_day"]
        init_resin = cfg["initial_resin"]
        max_resin = cfg["max_days"] * rpd + init_resin
        if self.goal_met():
            return dict(days=0, resin=0, runs=0, last=None, boxes=0)
        spent = 0
        runs = 0
        per_run_e = cfg["elixir_per_day"] * 20 / rpd
        per_run_d = cfg["dust_per_day"] * 20 / rpd
        while spent < max_resin:
            spent += 20
            runs += 1
            self.elixir += per_run_e
            self.dust += per_run_d
            n = 2 if rng.random() < cfg["extra_drop_rate"] else 1
            done = False
            for _ in range(n):
                is_t = rng.random() < cfg["set_rate"]
                if self._handle(rng.choice(SLOTS), is_t, cfg["domain_four_rate"]):
                    done = True
                    break
            if not done:
                done = self._strongboxes()
            if not done and (per_run_e or per_run_d):
                done = self._use_resources()
            if done:
                days = max(1, math.ceil((spent - init_resin) / rpd))
                return dict(days=days, resin=spent, runs=runs, last=self.last_slot, boxes=self.boxes)
        return dict(days=None, resin=spent, runs=runs, last=None, boxes=self.boxes)


def _worker(args):
    cfg, seed = args
    return Sim(cfg, random.Random(seed)).run()


# ---------------------------------------------------------------------------
# 5. 集計・出力
# ---------------------------------------------------------------------------
def pctl(sorted_vals, p):
    if not sorted_vals:
        return None
    i = min(len(sorted_vals) - 1, max(0, math.ceil(p / 100 * len(sorted_vals)) - 1))
    return sorted_vals[i]


def report(results, cfg):
    n = len(results)
    reached = sorted(r["days"] for r in results if r["days"] is not None)
    fail = n - len(reached)
    print("=" * 60)
    print(f" 試行 {n:,} 回 / 打ち切り {cfg['max_days']} 日 / 未達 {fail:,} 回 ({fail / n:.2%})")
    print("=" * 60)
    if not reached:
        print("全試行が打ち切り日数までに目標へ到達しませんでした。目標を下げるか max_days を延ばしてください。")
        return
    allv = reached + [float("inf")] * fail   # 未達は無限大扱い（パーセンタイル用）
    mean = sum(reached) / len(reached)
    note = "（未達を除く）" if fail else ""
    print(f"\n【到達日数】")
    print(f"  平均 {note:<8}: {mean:8.1f} 日")
    for label, p in [("中央値", 50), ("75%", 75), ("90%", 90), ("95%", 95), ("99%", 99), ("99.9%", 99.9)]:
        v = pctl(allv, p)
        s = f"{v:8d} 日" if v != float("inf") else f"   >{cfg['max_days']} 日"
        print(f"  {label:<10}: {s}")
    # ヒストグラム
    print("\n【分布】")
    hi = pctl(allv, 95)
    hi = hi if hi != float("inf") else cfg["max_days"]
    bins = 10
    w = max(1, math.ceil(hi / bins))
    cnt = [0] * (bins + 1)
    for d in reached:
        cnt[min(bins, (d - 1) // w)] += 1
    mx = max(cnt) or 1
    for i, c in enumerate(cnt):
        lo = i * w + 1
        label = f"{lo:>5}〜{(i + 1) * w:<5}" if i < bins else f"{lo:>5}〜      "
        print(f"  {label} {'#' * int(40 * c / mx):<40} {c / n:6.1%}")
    # 消費
    rs = sorted(r["resin"] for r in results if r["days"] is not None)
    print(f"\n【消費】 樹脂 平均 {sum(rs) / len(rs):,.0f}  "
          f"秘境 平均 {sum(r['runs'] for r in results if r['days'] is not None) / len(rs):,.0f} 周  "
          f"廻聖 平均 {sum(r['boxes'] for r in results if r['days'] is not None) / len(rs):,.0f} 回")
    # 最後に更新が入った部位
    from collections import Counter
    c = Counter(r["last"] for r in results if r["days"] is not None and r["last"])
    tot = sum(c.values())
    if tot:
        print("\n【達成の決め手になった部位（最後に入手/更新された部位）】")
        for s in SLOTS:
            print(f"  {SLOT_JA[s]:<3}: {c.get(s, 0) / tot:6.1%}")
    print()


def main():
    ap = argparse.ArgumentParser(description="原神 聖遺物シミュレータ")
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--config", type=str, help="DEFAULT_CONFIGを上書きするJSON")
    ap.add_argument("--max-days", type=int)
    ap.add_argument("--dump-config", action="store_true", help="設定をJSONで出力して終了")
    a = ap.parse_args()

    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if a.config:
        with open(a.config, encoding="utf-8") as f:
            cfg.update(json.load(f))
    if a.max_days:
        cfg["max_days"] = a.max_days
    if a.dump_config:
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        return

    t0 = time.time()
    jobs = [(cfg, a.seed + i) for i in range(a.sims)]
    if a.workers > 1 and a.sims >= 50:
        with Pool(a.workers) as p:
            results = p.map(_worker, jobs, chunksize=max(1, a.sims // (a.workers * 8)))
    else:
        results = [_worker(j) for j in jobs]
    report(results, cfg)
    print(f"実行時間: {time.time() - t0:.1f} 秒")


if __name__ == "__main__":
    main()
    