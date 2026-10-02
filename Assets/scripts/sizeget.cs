using UnityEngine;

public class sizeget : MonoBehaviour
{
    private Vector3 originalScale;
    public int Score;
    public playerStatus PlayerStatus;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Awake()
    {
        originalScale = transform.localScale;
        PlayerStatus = GameObject.Find("gameControler").GetComponent<playerStatus>();
    }

    // Update is called once per frame
    void Update()
    {
        if(this.transform.localScale.x < 0.1f * originalScale.x&& this.transform.localScale.y < 0.1f * originalScale.y)
        {
            PlayerStatus.score += Score;
            this.gameObject.SetActive(false);
        }
    }
}
