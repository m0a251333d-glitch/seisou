using UnityEngine;
using static playerStatus;
public class sizeget : MonoBehaviour
{
    private Vector3 originalScale;
    public int Score;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Awake()
    {
        originalScale = transform.localScale;
    }

    // Update is called once per frame
    void Update()
    {
        if(this.transform.localScale.x < 0.1f * originalScale.x&& this.transform.localScale.y < 0.1f * originalScale.y)
        {
            score += Score;
            this.gameObject.SetActive(false);
        }
    }
}
