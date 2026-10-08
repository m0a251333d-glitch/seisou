using UnityEngine;
using static gabagespawner;
using static playerStatus;
public class water : MonoBehaviour
{
    public GameObject PasteObject;
    private Rigidbody2D rb;
    private float fallSpeed = 0.03f;
    private Vector3 defaultSize;
    public int Score;
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
            gabageCount--;

            score += Score;
            Destroy(gameObject);
        }

    }
    private void OnCollisionEnter2D(Collision2D other)
    {
        if (other.gameObject.CompareTag("breadkuzu"))
        {
            if(GetInstanceID()>other.gameObject.GetInstanceID())
            {
                Quaternion spawnRotation = Quaternion.identity;
                Vector3 centerPosition = (transform.position + other.gameObject.transform.position) * 0.5f;
                Debug.Log("bread fusioned with bread");
                GameObject newPaste = Instantiate(PasteObject, centerPosition, Quaternion.identity);
                var pasteScript = newPaste.GetComponent<paste>();
                pasteScript.Score = Score;
                gabageCount--;
                
                Destroy(other.gameObject);
                Destroy(gameObject);
            }
        }
    }
}
