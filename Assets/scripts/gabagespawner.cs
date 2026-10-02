using UnityEngine;

public class gabagespawner : MonoBehaviour
{
    public GameObject[] gabage;
    private Vector2 spawnPoint;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        for(int i = 0; i < gabage.Length; i++)
        {
            for (int j = 0; j < 3; j++)
            {
                float vectorx = (Random.value-0.5f)*0.9f*18;
                float vectory = (Random.value-0.5f)*0.9f*10;
                spawnPoint.x = vectorx;
                spawnPoint.y = vectory;
                Instantiate(gabage[i], spawnPoint, Quaternion.identity);
            }
        }
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
