using UnityEngine;

public class water : MonoBehaviour
{
    public GameObject paste;
    private Rigidbody2D rb;
    private float fallSpeed = 0.03f;
    private Vector3 defaultSize;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        rb.linearVelocity = Vector2.down * fallSpeed;
    }
    void Awake()
    {
        defaultSize = transform.localScale;
    }

    // Update is called once per frame
    void Update()
    {
        if(transform.localScale.x < defaultSize.x * 0.3f)
        {
            Destroy(gameObject);
        }

    }
    private void OnCollisionEnter2D(Collision2D other)
    {
        if (other.gameObject.CompareTag("breadkuzu"))
        {
            Quaternion spawnRotation = Quaternion.identity;
            Vector3 centerPosition = (transform.position + other.gameObject.transform.position) * 0.5f;
            Debug.Log("bread fusioned with bread");
            Instantiate(paste, centerPosition, Quaternion.identity);
            Destroy(other.gameObject);
            Destroy(gameObject);
        }
    }
}
