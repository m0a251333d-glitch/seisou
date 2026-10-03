using UnityEngine;

public class usezoukin : useTool
{
    public Collider2D myCollider;
    private ContactFilter2D otherColliderFilter;
    private Collider2D[] otherCollider = new Collider2D[10];
    private bool cleaning = false;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    protected override void Start()
    {
        base.Start();
    }

    // Update is called once per frame
    protected override void Update()
    {
        base.Update();
        cleaning = false;
        if (Input.GetMouseButton(0) && thisItemusing)
        {
            cleaning = true;
        }
    }

    private void OnTriggerEnter2D(Collider2D collision)
    {
        if (collision.CompareTag("StickyThing"))
        {
            if (cleaning)
            {
                Vector3 size = collision.transform.localScale;
                collision.transform.localScale = new Vector3(size.x - 1f * size.x * Time.deltaTime, size.y - 1f * size.y * Time.deltaTime, size.z);
                if (collision.transform.localScale.x < 0.1f * size.x && collision.transform.localScale.y < 0.1f * size.y)
                {
                    Destroy(collision.gameObject);
                }
            }
        }
    }
    private void OnTriggerExit2D(Collider2D collision)
    {
        if (collision.CompareTag("StickyThing"))
        {
            if (cleaning)
            {
                Vector3 size = collision.transform.localScale;
                collision.transform.localScale = new Vector3(size.x - 1f * size.x * Time.deltaTime, size.y - 1f * size.y * Time.deltaTime, size.z);
                if (collision.transform.localScale.x < 0.1f * size.x && collision.transform.localScale.y < 0.1f * size.y)
                {
                    Destroy(collision.gameObject);
                }
            }
        }
     }
}