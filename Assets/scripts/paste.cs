using UnityEngine;

public class paste : MonoBehaviour
{

    private Vector3 defaultSize;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {

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
}
