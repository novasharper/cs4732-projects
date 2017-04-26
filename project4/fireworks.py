#!/bin/env python3

from pyglet.gl import *
from pyglet.window import key
from pyglet.sprite import SpriteGroup
import pywavefront as wf
import numpy as np
import random
import math
import ctypes

COLORS = [(1.0,0.5,0.5),(1.0,0.75,0.5),(1.0,1.0,0.5),(0.75,1.0,0.5),
          (0.5,1.0,0.5),(0.5,1.0,0.75),(0.5,1.0,1.0),(0.5,0.75,1.0),
          (0.5,0.5,1.0),(0.75,0.5,1.0),(1.0,0.5,1.0),(1.0,0.5,0.75)]

lightfv = ctypes.c_float * 4

offset = np.array([
    [-1, -1, 0],
    [ 1, -1, 0],
    [ 1,  1, 0],
    [-1,  1, 0]
])
offset_l = np.copy(offset)

half_side = 0.1
center = np.array([-0.5, 0.0, -1.0])
unit = 50.0
cam_h = 0.75
cam_r = 4.0
rotation = 0

def update_rot():
    global offset_l, rotation_m
    rotation_m = np.matrix([
        [ math.cos(rotation), 0, math.sin(rotation) ],
        [ 0,                  1, 0                  ],
        [-math.sin(rotation), 0, math.cos(rotation) ]
    ])
    offset_l = (rotation_m * offset.T).T.A
update_rot()

class Particle:
    def __init__(self, img, batch):
        # Physics
        self._x    = np.array([0.0,   0.0, 0.0])
        self._vel  = np.array([0.0,   0.0, 0.0])
        self._grav = np.array([0.0, -15.0, 0.0])

        # Simulation
        self._life  = 0.0
        self._drag  = 0.98
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

    def init_particle(self, x0, v0, color, is_alive=None, decay=0.0, scale=0.1):
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
        self._life = 0.0
        self._x    = np.array([0.0, 0.0, 0.0])
        self._vel  = np.array([0.0, 0.0, 0.0])
        self._update_position()
        self._update_color()

    def _update_position(self):
        if self._life > 0:
            scale = self._scale
            if self._decay:
                scale *= self._life
            self._vertex_list.vertices[:] = (self._x / unit + offset_l * scale).flatten()
        else:
            self._vertex_list.vertices[:] = (0, 0, 0) * 4
        

    def _update_color(self):
        r, g, b = self._rgb
        self._vertex_list.colors[:] = [r, g, b, self._life] * 4

    def update(self, dt):
        if self.is_alive(self._x, self._vel, self._life):
            # Update position using velocity
            self._x += self._vel * dt
            if self._decay:
                # Apply drag
                self._vel *= (1 - self._drag * dt)
                self._life -= dt / self._fade
            # Apply Gravity
            self._vel += self._grav * dt
        else:
            self._life = 0.0
            self.is_alive = Particle._is_alive
        self._update_position()
        self._update_color()
    
    @staticmethod
    def _is_alive(x, vel, life):
        return life > 0.01



class Firework:
    def __init__(self, particles):
        # Generate
        start = np.array([
            random.uniform(-half_side, half_side),
            0,
            random.uniform(-half_side, half_side)
        ]) + center
        start *= unit

        # Generate launch vector
        # Spherical coordinates
        rho = random.uniform(40, 70)
        theta = 0.35 * random.random() * math.pi / 2
        phi = random.random() * math.pi * 2
        # Rho projected onto the xz plane
        proj_r = math.sin(theta) * rho
        # Launch vector in cartesian coordinates
        v0 = np.array([
            math.cos(phi) * proj_r,
            math.cos(theta) * rho,
            math.sin(phi) * proj_r
        ])
        
        color = random.choice(COLORS)

        self.particles = particles
        # Figure out way to do callback
        def is_alive(x, vel, life):
            return x[1] < 60 and vel[1] > 10
        self.particles[0].init_particle(start, v0, color, is_alive, scale=0.05)
        self.exploded = False
        self.done = False
        self.timeout = -1
    
    def firework_fizzle(self):
        self.particles_done += 1
        if self.num_particles == self.particles_done:
            self.timeout = 2
    
    def firework_explode(self):
        x   = self.particles[0]._x
        vel = self.particles[0]._x
        # Choose a random explosion color
        color = random.choice(COLORS)
        # Firework explodes into 100 particles
        self.num_particles = random.randint(30, 71)
        self.particles_done = 0
        decay = random.uniform(0.4, 1.2)
        for i in range(self.num_particles):
            # Generate random particle speed
            speed = random.uniform(20, 60) / decay
            # Start at same x position as firework
            x0 = np.copy(x)
            # Initial velocity is random ve
            vel0 = np.random.uniform(-0.5, 0.5, 3) * speed + vel * 0.15
            self.particles[i].init_particle(x0, vel0, color, decay=decay, scale=0.075)
        self.exploded = True

    def update(self, dt):
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
        if self.timeout > 1:
            self.timeout -= dt
        elif self.timeout > 0:
            self.done = True


class Window(pyglet.window.Window):
    __max_fireworks = 10
    __max_particles = 100
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.set_minimum_size(640, 480)
        #pyglet.clock.set_fps_limit(60)
        pyglet.clock.schedule(self.update)
        self.frame = 0
        self.inactive = set()
        self.launchpad = wf.Wavefront('launchpad.obj')
        self.fs = False
        self.camera_loc = np.array([[0.0], [1.0], [-7.0]])
        self.up = [0.0, 1.0, 0.0]
        self.rate = 6.0 * (math.pi / 180)
        self.X0 = np.array([[0.0], [cam_h], [-cam_r]])
        self.center = center.tolist()
        self.particles = [None] * self.__max_fireworks
        self.sprite = pyglet.image.load('Particle.png')
        for i in range(self.__max_fireworks):
            batch = pyglet.graphics.Batch()
            particles = [Particle(self.sprite, batch) for i in range(self.__max_particles)]
            self.particles[i] = [batch, particles, None]
            self.inactive.add(i)

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., float(width)/height, 0.05, 1000)
        glMatrixMode(GL_MODELVIEW)
        return True

    def new_firework(self):
        try:
            i = self.inactive.pop()
            batch, particles, _ = self.particles[i]
            self.particles[i][2] = Firework(particles)
            return True
        except Exception as e:
            return False

    def on_draw(self):
        glLoadIdentity()
        gluLookAt(*self.camera_loc, *self.center, *self.up)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glLightfv(GL_LIGHT0, GL_POSITION, lightfv(-4.0, 1.0, 6.0, 1.0 ))
        glLightfv(GL_LIGHT0, GL_AMBIENT,  lightfv( 0.2, 0.4, 0.2, 1.0 ))
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  lightfv( 0.3, 0.9, 0.3, 1.0 ))
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightfv( 0.5, 0.5, 0.5, 1.0 ))
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION,  2.5  )
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION,    0.75 )
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.1  )
        glEnable(GL_LIGHT0)

        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glShadeModel(GL_SMOOTH)

        # Randomly spawn fireworks
        if self.frame % random.randint(40, 61) == 1:
            self.new_firework()

        # Draw the landscape
        self.launchpad.draw()

        # Setup to render fireworks
        glShadeModel(GL_FLAT)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)

        # Render particles
        for i in range(self.__max_fireworks):
            if i not in self.inactive:
                batch, _, fw = self.particles[i]
                if fw.exploded:
                    glDisable(GL_DEPTH_TEST)
                batch.draw()
                if fw.exploded:
                    glEnable(GL_DEPTH_TEST)

    def update(self, dt):
        global rotation
        global rotation_m
        self.frame += 1
        for i in range(self.__max_fireworks):
            if i not in self.inactive:
                self.particles[i][2].update(dt)
                if self.particles[i][2].done:
                    for particle in self.particles[i][1]:
                        particle.reset()
                    self.inactive.add(i)
                    self.particles[i][2] = None
        rotation += self.rate * dt
        if rotation > 2 * math.pi:
            rotation -= 2 * math.pi
        update_rot()
        self.camera_loc = ((rotation_m * self.X0).T + center).tolist()[0]

    def on_key_release(self, symbol, modifiers):
        if symbol == key.F:
            self.fs ^= True
            self.set_fullscreen(self.fs)
        if symbol == key.Q:
            pyglet.app.exit()


if __name__ =='__main__':
    window = Window(caption = 'fireworks', width=1280, height=720)
    pyglet.app.run()
    
