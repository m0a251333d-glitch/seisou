using UnityEngine;
using UnityEngine.SceneManagement;
using static timer;
using static gabagespawner;
public class playerStatus : MonoBehaviour
{
    public bool usingItem;
    public string itemName;
    public static int score;
    public int clearScore;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (timer.time<=0.0f)
        {
            SceneManager.LoadScene("result", LoadSceneMode.Single);
        }
        if(gabageCount <= 0)
        {
            SceneManager.LoadScene("result", LoadSceneMode.Single);
        }
    }
}
