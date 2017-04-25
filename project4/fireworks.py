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
]) * 0.4
offset_l = np.copy(offset)

half_side = 0.1
center = np.array([-0.5, 0.0, -1.0])
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
        self._x = np.array([0, 0, 0])
        self._vel = np.array([0, 0, 0])
        self._grav = np.array([0, -0.98, 0])

        # Simulation
        self._life  = 0.0
        self._drag  = 1.0
        self._decay = False

        # Graphics
        self._rgb     = (1.0, 1.0, 1.0)
        self._opacity = 0.0
        self._batch = batch
        self._texture = img.get_texture()
        self._group = SpriteGroup(self._texture, GL_SRC_ALPHA, GL_DST_ALPHA)
        self._create_vertex_list()
        self.callback = None
        self.is_alive = Particle._is_alive

    def _create_vertex_list(self):
        self._vertex_list = self._batch.add(4, GL_QUADS, self._group,
            'v3f/dynamic', 'c4f', ('t3f', self._texture.tex_coords))
        self._update_position()
        self._update_color()

    def init_particle(self, x0, v0, color, is_alive=None, decay=False):
        self._x = x0
        self._vel = v0
        self._decay = decay
        self._opacity = 1.0
        if decay:
            self._fade = 0.2  +  0.8 * random.random()
            self._drag = 0.04 + 0.06 * random.random()
        if is_alive is not None:
            self.is_alive = is_alive
        else:
            self.is_alive = Particle._is_alive

    def _update_position(self):
        self._vertex_list.vertices[:] = (self._x + offset_l).flatten()

    def _update_color(self):
        r, g, b = self._rgb
        self._vertex_list.colors[:] = [r, g, b, self._opacity] * 4

    def update(self, dt):
        if self.is_alive(self._x, self._vel, self._life):
            # Update position using velocity
            self._x += self._vel * dt
            if self._decay:
                # Apply drag
                self._vel *= (1 - self._drag * dt)
                self._life -= self._fade * dt
                self._opacity = self._life
            # Apply Gravity
            self._vel += self._grav * dt
            self._update_position()
            self._update_color()
        else:
            self._life = 0.0
            self._opacity = 0.0
            self._update_color()
            self.is_alive = Particle._is_alive
    
    @staticmethod
    def _is_alive(x, vel, life):
        return life > 0


class Firework:
    def __init__(self, id, particles):
        # Generate
        start = np.array([
            random.uniform(-half_side, half_side),
            0,
            random.uniform(-half_side, half_side)
        ]) + center

        # Generate launch vector
        # Spherical coordinates
        rho = random.uniform(5,6)
        theta = 0.25 * random.random() * math.pi / 2
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
        self.id = id
        # Figure out way to do callback
        def is_alive(X, V, life):
            return X[1] < 2.5
        self.particles[0].init_particle(start, v0, color, is_alive, self.gen_callback())
        self.exploded = False
        self.done = False

    def gen_callback(self):
        def firework_fizzle(self):
            self.num_particles -= 1
            if self.num_particles <= 0:
                self.done = True

        def firework_explode(self):
            # Choose a random explosion color
            color = random.choice(COLORS)
            # Firework explodes into 100 particles
            self.num_particles = random.randint(15, 71)
            for i in range(self.num_particles):
                # Generate random particle speed
                speed = random.uniform(3,6)
                # Rate of particle decay is proportional to particle speed
                decay = speed / 40.0
                # Start at same x position as firework
                X0 = np.copy(self.X)
                # Initial velocity is random ve
                v0 = np.random.uniform(-0.5, 0.5, 3) * speed + self.V
                self.particles[i].init_particle(X0, v0, color, lambda: firework_fizzle(self), True)
            self.exploded = True
        return lambda: firework_explode(self)
    
    def update(self, dt):
        if not self.done:
            if not self.exploded:
                self.particles[0].update(dt)
            else:
                for i in range(self.num_particles):
                    self.particles[i].update(dt)


class Window(pyglet.window.Window):
    __max_fireworks = 10
    __max_particles = 100
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.set_minimum_size(300, 200)
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
            self.particles[i][2] = Firework(i, particles)
            return True
        except Exception as e:
            return False

    def on_draw(self):
        glLoadIdentity()
        gluLookAt(*self.camera_loc, *self.center, *self.up)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glLightfv(GL_LIGHT0, GL_POSITION, lightfv(-30, 30, 30, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, lightfv(0.1, 0.2, 0.1, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightfv(0.1, 0.3, 0.1, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightfv(0.3, 0.3, 0.3, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glShadeModel(GL_SMOOTH)

        # Randomly spawn fireworks
        if self.frame % random.randint(30, 51) == 1:
            self.new_firework()
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        # Draw the landscape
        self.launchpad.draw()

        # Setup to render fireworks
        glShadeModel(GL_FLAT)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        # Render particles
        for i in range(self.__max_fireworks):
            if i not in self.inactive:
                self.particles[i][0].draw()

    def update(self, dt):
        global rotation
        global rotation_m
        self.frame += 1
        for i in range(self.__max_fireworks):
            if i not in self.inactive:
                self.particles[i][2].update(dt)
                if self.particles[i][2].done:
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
    window = Window(width = 800, height = 600, caption = 'fireworks')
    pyglet.app.run()
    
