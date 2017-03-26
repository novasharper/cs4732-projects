using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.UI;

public class FollowSpline : MonoBehaviour
{
    private delegate Vector3 SplineFn(float u, int segNum);

    enum SplineType
    {
        CatmullRom,
        Bezier,
        Null
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
        public float speed;
        public int len;
    }

    // Toggle buttons
    public Toggle catmullRomToggle;
    public Toggle bezierToggle;
    public Toggle pauseToggle;

    private List<Spline> splines;
    private List<GameObject> controlPoints;
    private SplineFn doSpline;
    private SplineType sel = SplineType.Null;

    public TextAsset file;
    private float time = 0;
    int splineNum = 0;

    void Start()
    {
        string conf = file.text;

        string[] lines = conf.Split('\n');

        List<string> proc = lines.Where(line => !(string.IsNullOrEmpty(line) || line[0] == '#')).ToList();
        
        int numSplines = int.Parse(proc[0]);

        int o = 1;

        splines = new List<Spline>();
        controlPoints = new List<GameObject>();

        for (int i = 0; i < numSplines; i++)
        {
            int numCoords = int.Parse(proc[o]);
            Spline spline = new Spline();
            spline.segs = new List<ControlPoint>();
            spline.span = float.Parse(proc[o + 1]);
            spline.len = numCoords;
            spline.speed = spline.span / (spline.len);
            for (int p = 0; p < numCoords; p++)
            {
                float[] pt = proc[o + p * 2 + 2].Split(',').Select(float.Parse).ToArray();
                float[] rot = proc[o + p * 2 + 3].Split(',').Select(float.Parse).ToArray();

                ControlPoint cp = new ControlPoint();
                cp.pos = new Vector3(pt[0], pt[1], pt[2]);
                cp.rot = EulerToQuat(rot[0], rot[1], rot[2]);
                spline.segs.Add(cp);
            }
            splines.Add(spline);
            o += 2 * (1 + numCoords);
        }

        LoadSpline(splines[splineNum].segs);

        UseCatmullRom();
    }

    void LoadSpline(List<ControlPoint> pts)
    {
        foreach(GameObject obj in controlPoints)
        {
            Destroy(obj);
        }

        controlPoints.Clear();

        foreach(ControlPoint pt in pts)
        {
            GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            obj.transform.position = pt.pos;
            controlPoints.Add(obj);
        }
    }

    void Update()
    {
        Spline curr = splines[splineNum];

        float adjTime = time / curr.speed;
        int segNum = Mathf.FloorToInt(adjTime);
        float u = adjTime - segNum;

        // Calculate position on spline
        Vector3 loc = doSpline(u, segNum);

        // Interpolate rotation using SLERP
        Vector4 q = Slerp(
            curr.segs[segNum].rot,
            curr.segs[(segNum + 1) % curr.len].rot,
            u);

        transform.position = loc;
        transform.rotation = new Quaternion(q.x, q.y, q.z, q.w);

        if (!pauseToggle.isOn) time += Time.deltaTime * curr.speed;

        if (time > curr.span)
        {
            time -= curr.span;
            splineNum = (splineNum + 1) % splines.Count;
        }
    }

    // Toggle using Catmull-Rom spline
    public void UseCatmullRom()
    {
        if (!catmullRomToggle.isOn || sel == SplineType.CatmullRom) return;
        time = 0;
        doSpline = CatmullRom;
        sel = SplineType.CatmullRom;
    }

    // Toggle using B-Spline
    public void UseBezier()
    {
        if (!bezierToggle.isOn || sel == SplineType.Bezier) return;
        time = 0;
        doSpline = Bezier;
        sel = SplineType.Bezier;
    }

    Vector3 CatmullRom(float u, int segNum)
    {
        float c0 = ((-u + 2f) * u - 1f) * u * 0.5f;
        float c1 = (((3f * u - 5f) * u) * u + 2f) * 0.5f;
        float c2 = ((-3f * u + 4f) * u + 1f) * u * 0.5f;
        float c3 = ((u - 1f) * u * u) * 0.5f;

        Spline spline = splines[splineNum];
        List<ControlPoint> segs = spline.segs;
        int len = spline.len;

        ControlPoint p0;
        if (segNum == 0) p0 = segs[len - 1];
        else p0 = segs[(segNum - 1) % len];
        ControlPoint p1 = segs[(segNum) % len];
        ControlPoint p2 = segs[(segNum + 1) % len];
        ControlPoint p3 = segs[(segNum + 2) % len];

        Vector3 point = p0.pos * c0 + p1.pos * c1 + p2.pos * c2 + p3.pos * c3;

        return point;
    }

    Vector3 Bezier(float u, int segNum)
    {
        Spline spline = splines[splineNum];
        List<ControlPoint> segs = spline.segs;
        int len = spline.len;
        float t = (segNum + u) / 3;
        segNum = Mathf.FloorToInt(t);
        u = t - segNum;

        List<Vector3> a, b;
        
        a = new List<Vector3>();
        for (int i = 0; i < 4; i++)
        {
            a.Add(spline.segs[(segNum * 3 + i) % len].pos);
        }

        while(a.Count > 1)
        {
            b = new List<Vector3>();
            for(int i = 0; i < a.Count - 1; i++)
            {
                b.Add(Lerp(a[i], a[i + 1], u));
            }
            a.Clear();
            a = b;
        }

        return a[0];
    }

    public static Vector4 EulerToQuat(float x, float y, float z)
    {
        return EulerToQuat(new Vector3(x, y, z));
    }

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

    public static Vector4 Slerp(Vector4 a, Vector4 b, float t)
    {
        a.Normalize();
        b.Normalize();

        float dot = Vector4.Dot(a, b);

        const float DOT_THRESHOLD = 0.9995f;
        if (dot > DOT_THRESHOLD)
        {
            Vector4 result = a + t * (b - a);
            result.Normalize();
            return result;
        }

        if (dot < 0)
        {
            b = -b;
            dot = -dot;
        }

        dot = Mathf.Clamp(dot, -1, 1);
        float theta_0 = Mathf.Acos(dot);
        float theta = theta_0 * t;

        Vector4 c = b - a * dot;
        c.Normalize();

        return a * Mathf.Cos(theta) + c * Mathf.Sin(theta);
    }

    public static Vector3 Lerp(Vector3 a, Vector3 b, float t)
    {
        return a * (1 - t) + b * t;
    }
}
