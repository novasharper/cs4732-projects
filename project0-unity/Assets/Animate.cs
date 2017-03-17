/* Module      : Animate.cs
 * Author      : Patrick Long
 * Email       : pllong@wpi.edu
 * Course      : CS 4732
 *
 * Description : Animate a Cube by rotating it
 *
 * Date        : 2017/03/15
 *
 * History:
 * Revision      Date          Changed By
 * --------      ----------    ----------
 * 01.00         2017/03/15    pllong
 * First release.
 */

using UnityEngine;
using System.Collections;

public class Animate : MonoBehaviour {
	/* Function    : void Update( void )
	 *
	 * Description : Runs once per tick, updates the cube's rotation
	 */
	void Update () {
		// Rotate along the axis (0, sqrt(2)/2, sqrt(2)/2)
		// Rotate 10 degrees per second
		transform.Rotate (new Vector3 (0, 1, 1), 10 * Time.deltaTime);
	}
}
