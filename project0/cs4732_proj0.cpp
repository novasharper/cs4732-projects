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

/* -- INCLUDE FILES ------------------------------------------------------ */

#include <GL/gl.h>
#include <GL/glu.h>
#include <GL/glut.h>

/* -- DATA STRUCTURES ---------------------------------------------------- */

struct qube {

};

/* -- GLOBAL VARIABLES --------------------------------------------------- */

const int numFrames = 300; // Number of frames to generate.

/* -- LOCAL VARIABLES ---------------------------------------------------- */

/* -- FUNCTIONS ---------------------------------------------------------- */

/* Function    : type name( type name, type name, etc. )
 *
 * Description : Description
 *
 * Parameters  : type name : Description
 *
 * Returns     : type : Values and Description
 */

void animateScene( void ) {
    //
}

void drawScene( void ) {
    //
}

int main( int argc, char ** argv )  {
  for( int frame = 0; frame < numFrames; frame++ )  {
    animateScene( );
    drawScene( );
  }
}