using UnityEngine;
using TMPro;
public class timer : MonoBehaviour
{
    public float time = 60.0f;
    public TextMeshProUGUI timerUI;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        time -= Time.deltaTime;
        timerUI.text = "Time: " + time.ToString("F1");
    }
}
