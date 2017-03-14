/* Module      : cs4732_project0
 * Author      : Patrick Long
 * Email       : pllong@wpi.edu
 * Course      : CS 4732
 *
 * Description : A simple hello world cube
 *
 * Date        : 2017/03/14
 *
 * History:
 * Revision      Date          Changed By
 * --------      ----------    ----------
 * 01.00         2017/03/14    pllong
 * First release.
 *
 */

#include <stdlib.h>
#include <GL/gl.h>
#include <GL/glu.h>
#include <GL/glut.h>
#include "cs4732_proj0.hpp"

#define _rand ((double) rand() / (RAND_MAX))

// CONSTANTS

const int numFrames = 9000; // Number of frames to generate.
const int kfInterval = 300; // Interval between keyframes

// LOCAL VARIABLES

cube _cube;
vec3 _c0;
vec3 _c1;
vec3 _delta;
vec3 axis;
double rot_mag;

int toNextKF = 0;

// FUNCTIONS

vec3& vec3::operator+=(const vec3& delta) {
    x += delta.x;
    y += delta.y;
    z += delta.z;
    return *this;
}
vec3 vec3::operator -(const vec3& other) {
    vec3 result;
    result.x = x - other.x;
    result.y = y - other.y;
    result.z = z - other.z;
    return result;
}
vec3 vec3::operator /(const double k) {
    vec3 result;
    result.x = x / k;
    result.y = y / k;
    result.z = z / k;
    return result;
}

// Allow
void changeSize(int w, int h) {

	// Prevent a divide by zero, when window is too short
	// (you cant make a window of zero width).
	if (h == 0)
		h = 1;

	float ratio =  w * 1.0 / h;

	// Use the Projection Matrix
	glMatrixMode(GL_PROJECTION);

	// Reset Matrix
	glLoadIdentity();

	// Set the viewport to be the entire window
	glViewport(0, 0, w, h);

	// Set the correct perspective.
	gluPerspective(45,ratio,1,100);

	// Get Back to the Modelview
	glMatrixMode(GL_MODELVIEW);

  gluLookAt( 0, 0, -3, 0, 0, 0, 0, 1, 0 );
}

// Initialize the scene
void initScene( void ) {
  // Init Scene
  _cube.cube_color = (vec3) { 1.0, 0.0, 0.0 };
  _cube.rot = 0.0;
  _cube.size = 1.0;
  _delta = (vec3) { 0.0, 0.0, 0.0 };
  _c1 = (vec3) { 1.0, 0.0, 0.0 };
}

// Update scene by one frame
void animateScene( void ) {
  _cube.cube_color += _delta;
  if( toNextKF == 0 ) {
    toNextKF = kfInterval;
    _c0 = _c1;
    _c1 = (vec3) { _rand, _rand, _rand };
    _delta = (_c1 - _c0) / kfInterval;
    rot_mag = ((_rand > 0.5) ? -1 : 1) * (45.0 * (1 + _rand));
  }
  else toNextKF--;
  _cube.rot += rot_mag / kfInterval;
  if( _cube.rot > 180 ) _cube.rot -= 360;
  if( _cube.rot < -180 ) _cube.rot += 360;
}

// Render the scene
void drawScene( void ) {

  glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );

  glPushMatrix();
  glColor3dv( reinterpret_cast<double*>(&_cube.cube_color) );
  glRotated( _cube.rot, 0, 1, 1 );
  glutSolidCube( 1.0f );
  glPopMatrix();

  glutSwapBuffers();
}

int main( int argc, char ** argv )  {
  // Initialize window
  glutInit( &argc, argv );
  glutInitDisplayMode( GLUT_DEPTH | GLUT_DOUBLE | GLUT_RGBA );
  glutInitWindowPosition( 100, 100 );
  glutInitWindowSize( 640, 640 );
  glutCreateWindow( "HALLO WORLD!" );
	glutReshapeFunc(changeSize);

  initScene( );
  for( int frame = 0; frame < numFrames; frame++ )  {
    animateScene( );
    drawScene( );
  }
}