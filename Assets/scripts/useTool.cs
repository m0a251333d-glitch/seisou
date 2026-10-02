using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
public class useTool : MonoBehaviour
{
    public playerStatus PlayerStatus;
    private Vector3 farstPosition;
    private Vector3 mousePos, worldPos;
    public bool thisItemusing = false;
    public string itemName;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    protected virtual void Start()
    {
        farstPosition = transform.position;
    }

    // Update is called once per frame
    protected virtual void Update()
    {
        if (thisItemusing)
        {
            mousePos = Input.mousePosition;
            worldPos = Camera.main.ScreenToWorldPoint(new Vector3(mousePos.x, mousePos.y, 5f));
            transform.position = worldPos;

            if (Input.GetMouseButtonDown(1)&& thisItemusing)
            {
                PlayerStatus.usingItem = false;
                thisItemusing = false;
                transform.position = farstPosition;
            }


        }

    }
    private void OnMouseDown()
    {
        if (!PlayerStatus.usingItem)
        {
            PlayerStatus.usingItem = true;
            thisItemusing = true;
            PlayerStatus.itemName = itemName;
        }
    }
}
