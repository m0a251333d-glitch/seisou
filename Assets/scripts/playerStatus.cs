using UnityEngine;
using UnityEngine.SceneManagement;

public class playerStatus : MonoBehaviour
{
    public bool usingItem;
    public string itemName;
    public int score;
    public int clearScore;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if(score >= clearScore)
        {
            SceneManager.LoadScene("result",LoadSceneMode.Single);
        }
    }
}
