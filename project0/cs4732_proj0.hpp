struct vec3 {
    double x;
    double y;
    double z;
    vec3& operator+=(const vec3& delta);
    vec3 operator -(const vec3& other);
    vec3 operator /(const double k);
};

struct cube {
    vec3 cube_color;
    double size;
    double rot;
};

void changeSize( int w, int h );
void initScene( void );
void animateScene( void );
void drawScene( void );