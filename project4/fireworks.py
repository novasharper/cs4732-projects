#!/bin/env python3

from pyglet.gl import *
from pyglet.window import key
from pyglet.sprite import SpriteGroup
import pywavefront as wf
from numpy import array, matrix, copy
from numpy.random import uniform as rand_array
import random
import math
import ctypes

# Firework colors
COLORS = [(1.0,0.5,0.5),(1.0,0.75,0.5),(1.0,1.0,0.5),(0.75,1.0,0.5),
          (0.5,1.0,0.5),(0.5,1.0,0.75),(0.5,1.0,1.0),(0.5,0.75,1.0),
          (0.5,0.5,1.0),(0.75,0.5,1.0),(1.0,0.5,1.0),(1.0,0.5,0.75)]

# Floating Point vector type used for glLightfv functions
lightfv = ctypes.c_float * 4

# Offsets for particle vertices
offset = array([
    [-0.5, -0.5, 0.0],
    [ 0.5, -0.5, 0.0],
    [ 0.5,  0.5, 0.0],
    [-0.5,  0.5, 0.0]
])
# Offsets rotated so particle can face camera
offset_l = copy(offset)

# 1/2 the side length of launch pad
half_side = 0.1
# Firework launch pad location
center = array([-0.5, 0.0, -1.0])
# Up vector (for camera)
up = [0.0, 1.0, 0.0]
# Size of one 'unit' in OpenGL space (1 opengl unit = 50 firework units)
unit = 50.0
# Camera Y position
cam_h = 0.75
# Camera distance from center along XZ-plane
cam_r = 4.0
# Camera rotation around the Y-axis
rotation = 0
# Update rotation matrix for camera position and particle vertex offsets
def update_rot():
    global offset_l, rotation_m
    rotation_m = matrix([
        [ math.cos(rotation), 0, math.sin(rotation) ],
        [ 0,                  1, 0                  ],
        [-math.sin(rotation), 0, math.cos(rotation) ]
    ])
    offset_l = (rotation_m * offset.T).T.A
update_rot()

class Particle:
    """Particle Controller

    This class controls particles. It computes updates to the particle's state
    and updates the Vertex List associated with the particle.
    """
    def __init__(self, img, batch):
        # Physics
        self._x    = array([0.0,   0.0, 0.0])
        self._vel  = array([0.0,   0.0, 0.0])
        self._grav = array([0.0, -20.0, 0.0])

        # Simulation
        self._life  = 0.0
        self._drag  = 0.95
        self._decay = False

        # Graphics
        self._rgb     = (1.0, 1.0, 1.0)
        self._batch = batch
        self._texture = img.get_texture()
        self._group = SpriteGroup(self._texture, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._create_vertex_list()
        self.callback = None
        self.is_alive = Particle._is_alive

    def _create_vertex_list(self):
        self._vertex_list = self._batch.add(4, GL_QUADS, self._group,
            'v3f', 'c4f', ('t3f', self._texture.tex_coords))
        self._update_position()
        self._update_color()

    def init_particle(self, x0, v0, color, is_alive=None, decay=0.0, scale=0.2):
        """Initialize particle
        
        Args:
            x0 (numpy.array 1x3): Initial particle location
            v0 (numpy.array 1x3): Initial particle velocity
            color      (3-tuple): RGB Particle color
            is_alife  (function): Static function used to determine if particle is still alive
            decay        (float): Rate at which particle decays
            scale        (float): Size of particle
        """

        self._x = x0
        self._vel = v0
        self._decay = decay > 0
        self._life = 1.0
        self._rgb = color
        self._scale = scale
        if self._decay:
            self._group.blend_dest = GL_DST_ALPHA
            self._fade = decay
            self._drag = 0.06 + 0.06 * random.random()
        else:
            self._group.blend_dest = GL_ONE_MINUS_SRC_ALPHA
        if is_alive is not None:
            self.is_alive = is_alive
        else:
            self.is_alive = Particle._is_alive
    
    def reset(self):
        """Reset particle back to initial position"""

        self._life = 0.0
        self._x    = array([0.0, 0.0, 0.0])
        self._vel  = array([0.0, 0.0, 0.0])
        self._update_position()
        self._update_color()

    def _update_position(self):
        """Update vertex positions"""

        if self._life > 0: # Particle is alive
            scale = self._scale
            if self._decay:
                scale *= self._life
            self._vertex_list.vertices[:] = (self._x / unit + offset_l * scale).flatten()
        else: # Particle is dead, so it is a point
            self._vertex_list.vertices[:] = (0, 0, 0) * 4
        

    def _update_color(self):
        """Update vertex colors, alpha = life"""

        r, g, b = self._rgb
        self._vertex_list.colors[:] = [r, g, b, self._life] * 4

    def update(self, dt):
        """Update particle state

        Args:
            dt (float): Time since last update (in seconds)
        """

        if self.is_alive(self._x, self._vel, self._life):
            # Update position using velocity
            self._x += self._vel * dt
            if self._decay:
                # Apply drag
                self._vel *= (1 - self._drag * dt)
                self._life -= dt / self._fade
            # Apply Gravity
            self._vel += self._grav * dt
        else: # Particle is dead
            self._life = 0.0
            self.is_alive = Particle._is_alive
        # Update vertex list
        self._update_position()
        self._update_color()
    
    @staticmethod
    def _is_alive(x, vel, life):
        return life > 0.01



class Firework:
    """Firework controller

    This class controls individual fireworks. It work by generating a random start position
    within a small square arount the center point. The launch vector of the firework is
    generated using spherical coordinates. First it chooses the launch speed (rho) in the
    range [44, 70] Then, it chooses a theta <= 31.5 degrees from vertical. Finally, it
    chooses a phi in [0, 2pi) and converts to cartesian coordinates.

    The firework explodes when it reaches a height >= 60 or a vertical velocity <= 30/s.

    When the firework explodes, it chooses a random number of particles in [10, _max_particles]
    Each particle starts at the current firework location and initialized to a random velocity
    that is influenced by the current firework velocity. As the explosion expands, the particles
    gradually fades.

    As each particle fades, it "fizzles".

    When all the particles have "fizzled", the firework waits one second before self-destructing
    """

    def __init__(self, particles):
        # Generate
        start = array([
            random.uniform(-half_side, half_side),
            0,
            random.uniform(-half_side, half_side)
        ]) + center
        start *= unit

        # Generate launch vector
        # Spherical coordinates
        rho = random.uniform(55, 70)
        theta = 0.35 * random.random() * math.pi / 2
        phi = random.random() * math.pi * 2
        # Rho projected onto the xz plane
        proj_r = math.sin(theta) * rho
        # Launch vector in cartesian coordinates
        v0 = array([
            math.cos(phi) * proj_r,
            math.cos(theta) * rho,
            math.sin(phi) * proj_r
        ])
        
        # Choose firework launch color
        color = random.choice(COLORS)

        self.particles = particles
        
        # Initalize firework particle (launch)
        def is_alive(x, vel, life):
            return x[1] < 60 and vel[1] > 30
        self.particles[0].init_particle(start, v0, color, is_alive, scale=0.05)

        # Has the firework exploded
        self.exploded = False

        # Is the firework done?
        self.done = False
        self.timeout = -1
    
    def firework_fizzle(self):
        """Handle particles finishing the explosion and fading"""

        # Increment number of particles that have faded
        self.particles_done += 1

        # When all particles have faded, start timeout
        if self.num_particles == self.particles_done:
            self.timeout = 2
    
    def firework_explode(self):
        """Simulate the firework explosion"""

        x   = self.particles[0]._x
        vel = self.particles[0]._x
        # Choose a random explosion color
        color = random.choice(COLORS)
        # Firework explodes into 100 particles
        self.num_particles = random.randint(10, Window._max_particles)
        self.particles_done = 0
        decay = random.uniform(0.4, 1.2)
        for i in range(self.num_particles):
            # Generate random particle speed
            speed = random.uniform(20, 60) / decay
            # Start at same x position as firework
            x0 = copy(x)
            # Initial velocity is random ve
            vel0 = rand_array(-0.5, 0.5, 3) * speed + vel * 0.35
            scale = 4 / self.num_particles
            self.particles[i].init_particle(x0, vel0, color, decay=decay, scale=scale)
        self.exploded = True

    def update(self, dt):
        """Update firework state

        Args:
            dt (float): Time since last update (in seconds)
        """

        # Firework is still running
        if not self.done:
            if not self.exploded:
                self.particles[0].update(dt)
                if self.particles[0]._life <= 0.0:
                    self.firework_explode()
            else:
                for i in range(self.num_particles):
                    self.particles[i].update(dt)
                    if self.particles[i]._life <= 0.0:
                        self.firework_fizzle()
        
        # Timeout has started
        if self.timeout > 1:
            self.timeout -= dt
        
        # Timed out, firework is ready for destruction
        elif self.timeout > 0:
            self.done = True


class Window(pyglet.window.Window):
    """Fireworks simulation application

    Attributes:
        _max_fireworks (int): The maximum number of fireworks that can be displayed at one time
        _max_particles (int): The maximum number of particles used per firework
    """
    
    _max_fireworks = 10
    _max_particles = 70
    
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        pyglet.clock.schedule(self.update)                   # Initialize update loop
        self.frame = 0                                       # Frame starts at 0
        self.inactive = set()                                # Set of inactive particle group ids
        self.launchpad = wf.Wavefront('launchpad.obj')       # Landscape model
        self.fs = False                                      # Is the window fullscreen
        self.camera_loc = array([[0.0], [cam_h], [-cam_r]])  # Initial camer
        self.rate = 6.0 * (math.pi / 180)                    # Rotation rate
        self.X0 = array([[0.0], [cam_h], [-cam_r]])          # Camera offset

        # Initialize particles
        self.fireworks = [None] * Window._max_fireworks      # List of particle sets
        self.sprite = pyglet.image.load('Particle.png')      # Particle sprite

        for i in range(Window._max_fireworks):
            batch = pyglet.graphics.Batch()                  # Batch renderer for particle group
            particles = [                                    # Allocate list of particles
                Particle(self.sprite, batch)
                for i in range(Window._max_particles)
            ]
            self.fireworks[i] = [batch, particles, None]
            self.inactive.add(i)
        self._setup_lighting()

    def _setup_lighting(self):
        """Add the 'sun' to illuminate the landscape."""

        # Light position
        glLightfv(GL_LIGHT0, GL_POSITION, lightfv(-4.0, 1.0, 6.0, 1.0 ))

        # Light colors (shading)
        glLightfv(GL_LIGHT0, GL_AMBIENT,  lightfv( 0.2, 0.4, 0.2, 1.0 ))
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  lightfv( 0.3, 0.9, 0.3, 1.0 ))
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightfv( 0.5, 0.5, 0.5, 1.0 ))

        # Parameters for light attenuation
        # att = 1 / (kc + kl * d + kq * d^2)
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION,  2.5  )
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION,    0.75 )
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.1  )

        # Enable the light
        glEnable(GL_LIGHT0)

    def on_resize(self, width, height):
        """Handle the window resizing

        Args:
            width  (int): The new width
            height (int): The new height
        """

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., float(width)/height, 0.05, 1000)
        glMatrixMode(GL_MODELVIEW)
        return True

    def new_firework(self):
        """Create a new firework"""

        try:
            i = self.inactive.pop()                     # Choose a currently inactive firework

            _, particles, _ = self.fireworks[i]         # Get the list of particles allocated
                                                        # for the firework

            self.fireworks[i][2] = Firework(particles)  # Create a new firework
            return True
        except Exception as e:                          # Return false in the case of any errors
            return False

    def on_draw(self):
        """Render Scene"""

        # Reset view
        glLoadIdentity()

        # Setup camera
        gluLookAt(*self.camera_loc, *center, *up)

        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Render launchpad
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glShadeModel(GL_SMOOTH)

        # Draw the landscape
        self.launchpad.draw()

        # Setup to render fireworks
        glShadeModel(GL_FLAT)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)

        # Render particles
        for i in range(Window._max_fireworks):
            if i not in self.inactive:
                batch, _, fw = self.fireworks[i]  # Get firework

                # Firework in explosion state does not use depth test
                if fw.exploded:
                    glDisable(GL_DEPTH_TEST)
                batch.draw()                      # Draw firework
                if fw.exploded:
                    glEnable(GL_DEPTH_TEST)

    def update(self, dt):
        """Update application state

        Args:
            dt (float): Time since last update (in seconds)
        """

        global rotation
        global rotation_m
        self.frame += 1

        # Update all fireworks
        for i in range(Window._max_fireworks):
            if i not in self.inactive:                    # Check to see if firework is active
                self.fireworks[i][2].update(dt)

                if self.fireworks[i][2].done:             # Firework is done, so reset it
                    for particle in self.fireworks[i][1]: # Reset all particles
                        particle.reset()
                    self.inactive.add(i)                  # Add to list of inactive fireworks
                    self.fireworks[i][2] = None           # Delete firework controller

        # Randomly spawn fireworks
        if self.frame % random.randint(40, 61) == 1:
            self.new_firework()
        
        # Camera is gradually rotating around center point
        rotation += self.rate * dt
        if rotation > 2 * math.pi:
            rotation -= 2 * math.pi
        
        # Update rotation matrix and unit offsets for particles
        update_rot()

        # Update camera location (rotate around center point)
        self.camera_loc = ((rotation_m * self.X0).T + center).tolist()[0]

    def on_key_release(self, symbol, modifiers):
        """Handle keyboard input

        Args:
            symbol    (int): The key that was pressed
            modifiers (int): Any modifiers applied (ie. CTRL, ALT, SHIFT)
        """
        
        if symbol == key.F:              # Toggle Fullscreen
            self.fs ^= True
            self.set_fullscreen(self.fs)
        if symbol == key.Q:              # Exit application
            pyglet.app.exit()


if __name__ =='__main__':
    window = Window(caption = 'fireworks', width=1280, height=720)
    pyglet.app.run()
    
