using UnityEngine;
using UnityEngine.Rendering.UI;

public class Tongs : useTool
{
    public Collider2D myCollider;
    private ContactFilter2D otherColliderFilter;
    private Collider2D[] otherCollider = new Collider2D[10];
    private bool objectPicking = false;
    public GameObject targetObject;
    Vector3 deviation;
    Vector3 oldPosition;
    float distance;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    protected override void Start()
    {
        base.Start();
    }

    // Update is called once per frame
    protected override void Update()
    {
        base.Update();
        if (Input.GetMouseButton(0) && thisItemusing && !objectPicking)
        {
            int hitCount = myCollider.Overlap(otherColliderFilter, otherCollider);
            for (int i = 0; i < hitCount; i++)
            {
                float minidistance = float.MaxValue;
                if (otherCollider[i] != null && (otherCollider[i].CompareTag("FoodWaste") || otherCollider[i].CompareTag("Gabage")))
                {
                    distance = Vector3.Distance(transform.position, otherCollider[i].transform.position);
                    if (distance < minidistance)
                    {
                        minidistance = distance;
                        targetObject = otherCollider[i].gameObject;
                        objectPicking = true;
                    }
                }

            }
        }
        if (objectPicking && targetObject != null)
        {
            deviation = oldPosition - transform.position;
            targetObject.transform.position -= deviation;
        }
        else if(targetObject == null)
        {
            objectPicking = false;
        }
            oldPosition = transform.position;
        if(Input.GetMouseButtonUp(0))
        {
            objectPicking = false;
            targetObject = null;
        }
    }
}
