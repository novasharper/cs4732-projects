using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Controller : MonoBehaviour {
    
	// Use this for initialization
	void Start () {
        Mesh mesh = GetComponent<MeshFilter>().mesh;
        Vector3[] vertices = mesh.vertices;

        // create new colors array where the colors will be created.
        Color[] colors = new Color[vertices.Length];

        for (int i = 0; i < vertices.Length; i++)
            colors[i] = new Color(vertices[i].x, vertices[i].y, vertices[i].z);

        // assign the array of colors to the Mesh.
        mesh.colors = colors;
    }
	
	// Update is called once per frame
	void Update () {
		
	}
}
