/* Module      : FollowSpline.cs
 * Author      : Patrick Long
 * Email       : pllong@wpi.edu
 * Course      : CS 4732
 *
 * Description : Animate a Cube to follow a spline.
 *
 * Date        : 2017/03/27
 *
 * History:
 * Revision      Date          Changed By
 * --------      ----------    ----------
 * 01.00         2017/03/27    pllong
 * First release.
 */


using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

public class FollowSpline : MonoBehaviour
{
    // Function pointer type for spline function
    private delegate Vector3 SplineFn(float u, int segNum);

    // List of types
    enum SplineType
    {
        CatmullRom,
        Bezier,
        Null // Neutral starting type
    }

    // Struct to represent a control point on a spline
    private struct ControlPoint
    {
        public Vector3 pos;
        public Vector4 rot;
    }

    // Struct to represent a spline
    private struct Spline
    {
        public List<ControlPoint> segs;
        public float span;
        public int len;
    }

    // Toggle buttons
    public Toggle catmullRomToggle;
    public Toggle bezierToggle;
    public Toggle pauseToggle;
    public Text timeText;

    // Material used for breadcrumbs
    public Material breadCrumbMaterial;

    // Material used for control points
    public Material controlPointMaterial;

    // List of splines
    private List<Spline> splines;
    // List of control point objects
    private List<GameObject> controlPoints;
    // Current spline function
    private SplineFn doSpline;
    // Current spline type
    private SplineType sel = SplineType.Null;

    public TextAsset file;
    private float time = 0;
    int splineNum = 0;

    void Start()
    {
        // Color the cube to allow for orientation reference
        Mesh mesh = GetComponent<MeshFilter>().mesh;
        Vector3[] vertices = mesh.vertices;

        // create new colors array where the colors will be created.
        Color[] colors = new Color[vertices.Length];

        for (int i = 0; i < vertices.Length; i++)
            colors[i] = new Color(vertices[i].x, vertices[i].y, vertices[i].z);

        // assign the array of colors to the Mesh.
        mesh.colors = colors;

        // Load spline config
        string conf = file.text;

        string[] lines = conf.Split('\n');

        // Get rid of empty lines and comments
        List<string> proc = lines.Where(line => !(string.IsNullOrEmpty(line) || line[0] == '#')).ToList();
        
        // Number of splines
        int numSplines = int.Parse(proc[0]);

        // Offset
        int o = 1;

        splines = new List<Spline>(); // Splines
        controlPoints = new List<GameObject>(); // Displayed control points

        // Parse each spline
        for (int i = 0; i < numSplines; i++)
        {
            // Get number of control points in spline
            int numCoords = int.Parse(proc[o]);
            // Create new spline
            Spline spline = new Spline();
            spline.segs = new List<ControlPoint>();
            spline.span = float.Parse(proc[o + 1]);
            spline.len = numCoords;
            // Load spline control points
            for (int p = 0; p < numCoords; p++)
            {
                // Position
                float[] pt = proc[o + p * 2 + 2].Split(',').Select(float.Parse).ToArray();
                // Euler rotation
                float[] rot = proc[o + p * 2 + 3].Split(',').Select(float.Parse).ToArray();

                // Create control point
                ControlPoint cp = new ControlPoint();
                cp.pos = new Vector3(pt[0], pt[1], pt[2]);
                cp.rot = EulerToQuat(rot[0], rot[1], rot[2]);
                spline.segs.Add(cp); // Add point to spline
            }
            // Add spline to list of splines
            splines.Add(spline);
            // Seek to next spline
            o += 2 * (1 + numCoords);
        }

        // Display control points for current spline
        LoadSpline();
    
        // Start by using Catmull-Rom method
        UseCatmullRom();
    }

    // Update control points displayed
    void LoadSpline()
    {
        List<ControlPoint> pts = splines[splineNum].segs;
        // Clear control points
        foreach (GameObject obj in controlPoints)
        {
            Destroy(obj);
        }

        controlPoints.Clear();

        // Display control points
        foreach(ControlPoint pt in pts)
        {
            GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            obj.transform.position = pt.pos;
            obj.GetComponent<Renderer>().material = controlPointMaterial;
            controlPoints.Add(obj);
        }
    }


    private List<GameObject> path = new List<GameObject>();
    Vector3 last = Vector3.zero;
    void Update()
    {
        // Get current spline
        Spline curr = splines[splineNum];

        // Display time in current iteration of spline
        timeText.text = string.Format("{0:00.00}%", 100 * time / curr.span);

        // Get progress along spline
        float adjTime = Mathf.Clamp(time * curr.len / curr.span, 0, curr.len);
        int segNum = Mathf.FloorToInt(adjTime);
        float u = adjTime - segNum;

        // Calculate position on spline
        Vector3 loc = doSpline(u, segNum);

        // Interpolate rotation using SLERP
        Vector4 q = Slerp(
            curr.segs[segNum].rot,
            curr.segs[(segNum + 1) % curr.len].rot,
            u);

        // Update transform
        transform.position = loc;
        transform.rotation = new Quaternion(q.x, q.y, q.z, q.w);

        // Leave breadcrumbs
        if ((loc - last).magnitude > 0.6f)
        {
            GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            obj.transform.localScale = new Vector3(0.5f, 0.5f, 0.5f);
            obj.transform.position = loc;
            obj.GetComponent<Renderer>().material = breadCrumbMaterial;
            path.Add(obj);
            last = loc;
        }

        // Move if not paused
        if (!pauseToggle.isOn) time += Time.deltaTime;

        // Should we start over?
        if (time >= curr.span)
        {
            // Go back to beginning
            time = 0;
            // Move to next spline
            splineNum = (splineNum + 1) % splines.Count;
            // Clear breadcrumbs
            foreach (GameObject o in path) Destroy(o);
            path.Clear();
            // Update control points displayed
            LoadSpline();
            last = loc;
        }
    }

    // Toggle using Catmull-Rom spline
    public void UseCatmullRom()
    {
        if (!catmullRomToggle.isOn || sel == SplineType.CatmullRom) return;
        time = 0;
        foreach (GameObject o in path) Destroy(o);
        path.Clear();
        doSpline = CatmullRom;
        sel = SplineType.CatmullRom;
    }

    // Toggle using B-Spline
    public void UseBezier()
    {
        if (!bezierToggle.isOn || sel == SplineType.Bezier) return;
        time = 0;
        foreach (GameObject o in path) Destroy(o);
        path.Clear();
        doSpline = Bezier;
        sel = SplineType.Bezier;
    }

    // Catmull-Rom spline function
    Vector3 CatmullRom(float u, int segNum)
    {
        Spline spline = splines[splineNum];
        List<Vector3> segs = spline.segs.Select(seg => seg.pos).ToList();
        int len = spline.len;

        float usq = u * u;
        float ucb = usq * u;

        // Get Control Points
        Vector3 p0 = segs[(segNum + len - 1) % len];
        Vector3 p1 = segs[(segNum) % len];
        Vector3 p2 = segs[(segNum + 1) % len];
        Vector3 p3 = segs[(segNum + 2) % len];

        // Calculate coefficients
        // See README.txt for source of polynomials
        float c0 =      -ucb + 2f * usq - u     ;
        float c1 =  3f * ucb - 5f * usq     + 2f;
        float c2 = -3f * ucb + 4f * usq + u     ;
        float c3 =       ucb -      usq         ;

        // Calculate point
        return (p0 * c0 + p1 * c1 + p2 * c2 + p3 * c3) / 2f;
    }

    // B-Spline (generalized Bezier) function
    Vector3 Bezier(float u, int segNum)
    {
        Spline spline = splines[splineNum];
        List<Vector3> segs = spline.segs.Select(seg => seg.pos).ToList();
        int len = spline.len;

        float v = 1 - u;
        float usq = u * u;
        float ucb = usq * u;

        // Get Control points
        Vector3 p0 = segs[segNum];
        Vector3 p1 = segs[(segNum + 1) % len];
        Vector3 p2 = segs[(segNum + 2) % len];
        Vector3 p3 = segs[(segNum + 3) % len];
        
        // Calculate coefficients
        float c0 =     v*v*v                         ;
        float c1 =  3f * ucb - 6f * usq          + 4f;
        float c2 = -3f * ucb + 3f * usq + 3f * u + 1f;
        float c3 =       ucb                         ;

        // Calculate point
        return (p0 * c0 + p1 * c1 + p2 * c2 + p3 * c3) / 6f;
    }

    // Generate quaterion from Euler angles
    public static Vector4 EulerToQuat(float x, float y, float z)
    {
        return EulerToQuat(new Vector3(x, y, z));
    }

    // Generate quaterion from Euler angles
    // See https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    public static Vector4 EulerToQuat(Vector3 e)
    {
        float t0 = Mathf.Cos(e.z * 0.5f);
        float t1 = Mathf.Sin(e.z * 0.5f);
        float t2 = Mathf.Cos(e.x * 0.5f);
        float t3 = Mathf.Sin(e.x * 0.5f);
        float t4 = Mathf.Cos(e.y * 0.5f);
        float t5 = Mathf.Sin(e.y * 0.5f);

        float x_ = t0 * t3 * t4 - t1 * t2 * t5;
        float y_ = t0 * t2 * t5 + t1 * t3 * t4;
        float z_ = t1 * t2 * t4 - t0 * t3 * t5;
        float w_ = t0 * t2 * t4 + t1 * t3 * t5;
        return new Vector4(x_, y_, z_, w_);
    }

    // Interpolate using Slerp
    public static Vector4 Slerp(Vector4 a, Vector4 b, float t)
    {
        // Only unit quaternions are valid rotations
        // Normalize to avoid problems
        a.Normalize();
        b.Normalize();

        // Compute the cosine of the angle between the two vectors
        float dot = Vector4.Dot(a, b);

        const float DOT_THRESHOLD = 0.9995f;
        if (dot > DOT_THRESHOLD)
        {
            // If the inputs are very close, lerp then normalize
            Vector4 result = a + t * (b - a);
            result.Normalize();
            return result;
        }

        // If the dot product is negative, the quaternions have
        // Opposite handed-ness and slerp will not take the shorter
        // pat. Avoid issue by reversing one quaternion
        if (dot < 0)
        {
            b = -b;
            dot = -dot;
        }

        // Ensure dot product is in domain of acos()
        dot = Mathf.Clamp(dot, -1, 1);
        float theta_0 = Mathf.Acos(dot); // Angle between input vectors
        float theta = theta_0 * t;       // Angle between a and the result

        Vector4 c = b - a * dot;
        c.Normalize(); // { a, c } is now an orthonormal basis

        return a * Mathf.Cos(theta) + c * Mathf.Sin(theta);
    }
}
