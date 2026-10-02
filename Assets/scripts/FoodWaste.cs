using UnityEngine;

public class FoodWaste : MonoBehaviour
{
    public GameObject Dust;
    public Tongs tongs;
    int spawnedDust = 0;
    public int spawnDustLimit = 3;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {

    }
    private void Awake()
    {
        tongs = GameObject.Find("pan_tongs_0").GetComponent<Tongs>();
    }

    // Update is called once per frame
    void Update()
    {

    }
    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("TrashBox"))
        {
            if (tongs.targetObject != null)
            {
                tongs.targetObject = null;
            }
                Destroy(gameObject);
        }
        else
        {
            float random = Random.value;
            if (random < 0.3f&& spawnedDust <= spawnDustLimit)
            {
                Instantiate(Dust, transform.position, Quaternion.identity);
                spawnedDust++;
            }

        }
    }
}
