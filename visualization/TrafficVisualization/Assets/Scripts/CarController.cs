/*
Script to control the car's and wheel's transforms -> rotation and translation

Mariel Gómez 
Santiago Rodríguez
2023-11-23
*/

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CarController : MonoBehaviour
{
    [SerializeField] float angularVelocity = 90f;
    [SerializeField] GameObject wheel;
    [SerializeField] public Vector3 from;
    [SerializeField] public Vector3 to;
    // time the movement takes
    [SerializeField] float movementTime = 1f;
    [SerializeField] Vector3[] wheelPositions;

    bool firstUpdate = true;

    float timer = 0f;

    // gameobject list for the wheels
    GameObject[] wheels = new GameObject[4];

    // meshes and vertices for the car
    Mesh mesh;
    Vector3[] baseVertices;
    Vector3[] newVertices;

    // meshes and vertices for the wheels
    Mesh[] wheelMeshes = new Mesh[4];
    Vector3[][] wheelBaseVertices = new Vector3[4][];
    Vector3[][] wheelNewVertices = new Vector3[4][];

    // Start is called before the first frame update
    void Start()
    {
        // instantiate the wheels
        for (int i = 0; i < 4; ++i)
        {
            // add the wheels in position, relative to where the car was instantiated
            wheels[i] = Instantiate(wheel, wheelPositions[i] + gameObject.transform.position, Quaternion.identity);
        }

        // get the meshes and vertices for the car
        mesh = GetComponentInChildren<MeshFilter>().mesh;
        baseVertices = mesh.vertices;

        // Copy the vertices to a new array
        newVertices = new Vector3[baseVertices.Length];
        for (int i = 0; i < baseVertices.Length; i++)
        {
            newVertices[i] = baseVertices[i];
        }

        // get the meshes and vertices for the wheels
        for (int i = 0; i < 4; ++i)
        {
            wheelMeshes[i] = wheels[i].GetComponentInChildren<MeshFilter>().mesh;

            wheelBaseVertices[i] = wheelMeshes[i].vertices;

            // Copy the vertices to a new array
            wheelNewVertices[i] = new Vector3[wheelBaseVertices[i].Length];
            for (int j = 0; j < wheelBaseVertices[i].Length; j++)
            {
                wheelNewVertices[i][j] = wheelBaseVertices[i][j];
            }
        }
    }

    // Update is called once per frame
    void Update()
    {
        // if the car has reached the current waypoint, move to the next one
        timer += Time.deltaTime;

        if (timer < movementTime)
        {
            DoTransform();
        }

    }

    void DoTransform()
    {
        Vector3 direction = Vector3.Lerp(from, to, timer / movementTime);

        Matrix4x4 move = HW_Transforms.TranslationMat(direction.x,
                                                      direction.y,
                                                      direction.z);

        float angle = Vector3.SignedAngle(Vector3.forward, to - from, Vector3.down);

        Matrix4x4 rotate = HW_Transforms.RotateMat(angle, AXIS.Y);
        Matrix4x4 composite = move * rotate;

        for (int i = 0; i < baseVertices.Length; i++)
        {
            Vector4 tmp = new Vector4(baseVertices[i].x, baseVertices[i].y, baseVertices[i].z, 1);

            newVertices[i] = composite * tmp;
        }

        // Assign the new vertices to the mesh
        mesh.vertices = newVertices;
        mesh.RecalculateNormals();

        // rotate the wheels
        Matrix4x4 spin = HW_Transforms.RotateMat(angularVelocity * Time.time, AXIS.X);
        Matrix4x4 spinComp = spin;

        for (int i = 0; i < 4; i++)
        {
            Matrix4x4 pivot = HW_Transforms.TranslationMat(wheelPositions[i].x, wheelPositions[i].y, wheelPositions[i].z);
            Matrix4x4 pivotBack = HW_Transforms.TranslationMat(-wheelPositions[i].x, -wheelPositions[i].y, -wheelPositions[i].z);

            for (int j = 0; j < wheelBaseVertices[i].Length; j++)
            {
                Vector4 tmp = new Vector4(wheelBaseVertices[i][j].x, wheelBaseVertices[i][j].y, wheelBaseVertices[i][j].z, 1);

                wheelNewVertices[i][j] = move * pivotBack * rotate * pivot * spinComp * tmp;
            }

            wheelMeshes[i].vertices = wheelNewVertices[i];
            wheelMeshes[i].RecalculateNormals();
        }
    }

    public void SetNextWaypoint(Vector3 next)
    {
        from = to;

        // if the car is just starting, set the from to the next
        if (firstUpdate)
        {
            firstUpdate = false;
            from = next;
        }

        to = next;
        timer = 0f;
    }

    public void SetMovementTime(float time)
    {
        movementTime = time;
    }

    public void DeleteSelf()
    {
        // delete the wheels
        for (int i = 0; i < 4; ++i)
        {
            Destroy(wheels[i]);
        }

        Destroy(gameObject);
    }
}
