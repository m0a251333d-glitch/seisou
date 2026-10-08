using UnityEngine;

public class result : MonoBehaviour
{
    public GameObject resultText;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            resultText.gameObject.SetActive(true);   
        }
    }
}
