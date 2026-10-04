using UnityEngine;

public class useSoujiki : useTool
{
    public Collider2D myCollider;
    private ContactFilter2D otherColliderFilter;
    private Collider2D[] otherCollider = new Collider2D[10];
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    protected override void Start()
    {
        base.Start();
    }

    // Update is called once per frame
    protected override void Update()
    {
        base.Update();
        if (Input.GetMouseButton(0)&& thisItemusing)
        {
            int hitCount = myCollider.Overlap(otherColliderFilter, otherCollider);
            for (int i = 0; i < otherCollider.Length; i++)
            {
                if (otherCollider[i] != null && otherCollider[i].CompareTag("breadkuzu"))
                {
                    Vector3 size = otherCollider[i].transform.localScale;
                    otherCollider[i].transform.localScale = new Vector3(size.x - 1f * size.x * Time.deltaTime, size.y - 1f * size.y * Time.deltaTime, size.z);
                }
            }
        }
    }
}
