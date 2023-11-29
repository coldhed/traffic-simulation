using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SColorLight : MonoBehaviour
{
    // Interpolate light color between two colors back and forth
    Color RedLight = Color.red;
    Color GreenLoight = Color.green;

    Light lt;

    void Start()
    {
        lt = GetComponent<Light>();
    }

    public void SetLightColor(Color StopLightColor)
    {
        lt.color = StopLightColor;
    }

}
