#!/bin/env python3

from pyglet.gl import *
from pyglet.window import key
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
    [ 1,  1, 0],
    [-1,  1, 0],
    [ 1, -1, 0],
    [-1, -1, 0]
]) * 0.4
texture_coords = (
    1, 1,
    0, 1,
    1, 0,
    0, 0
)
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

sprite = pyglet.resource.image('Particle.png')
groups = [
    pyglet.sprite.SpriteGroup(sprite.texture, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA),
    pyglet.sprite.SpriteGroup(sprite.texture, GL_SRC_ALPHA, GL_DST_ALPHA)
]


class Particle(object):
    """Base particle class, used to show a shining particle
    
    Parameters:

    add     (set)         : Set of all particles to add this turn
    discard (set)         : Set of all particles to delete this turn
    start   (numpy.Array) : Initial position
    v0      (numpy.Array) : Initial velocity
    color   (tuple)       : Particle color (RGB)
    decay   (float)       : Scaling factor for rate of decay
    """
    show_fade = False
    def __init__(self, add, discard, start, v0, color, decay=-1):
        self.add = add
        self.discard = discard
        self.life = 1.0
        self.drag_c = 1.0
        if decay > 0:
            self.fade = (0.2 +  0.8 * random.random()) * decay
            self.drag_c = 0.9 + 0.06 * random.random()
            self.show_fade = True
            self.scale = 0.5
        self.X = start # Initial position
        self.V = v0    # Velocity vector
        self.g = np.array([0, -0.08, 0])
        self.batch = pyglet.graphics.Batch()
        if self.show_fade:
            self.group = groups[1]
        else:
            self.group = groups[0]
        self.vertex_list = self.batch.add(4, GL_TRIANGLE_STRIP, self.group,
            'v3f', 'c4f', ('t2f', texture_coords) )
        self.update_position()
        self.vertex_list.colors[0:16] = [*color, 1] * 4
        self.add.add(self)

    def update(self):
        # Update position using velocity
        self.X += self.V / 100
        if self.show_fade:
            # Apply drag
            self.V *= self.drag_c
            self.life -= self.fade
            self.vertex_list.colors[3::4] = [self.life] * 4
        # Apply Gravity
        self.V += self.g

    def update_position(self):
        self.vertex_list.vertices[0:12] = (self.X + offset_l).flatten()

    def is_alive(self):
        return self.life > 0

    def draw(self):
        if self.is_alive():
            self.update_position()
            if self.show_fade:
                glDisable(GL_DEPTH_TEST)
            self.batch.draw()
            if self.show_fade:
                glEnable(GL_DEPTH_TEST)
        else:
            self.die()
    
    def die(self):
        self.discard.add(self)


class Firework(Particle):
    def __init__(self, add, discard):
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

        super().__init__(add, discard, start, v0, color)

    # Determine if firework is still alive
    def is_alive(self):
        return self.X[1] < 2 and self.V[1] >= 1

    def die(self):
        # Choose a random explosion color
        color = random.choice(COLORS)
        # Firework explodes into 100 particles
        num_particles = random.randint(15, 71)
        for i in range(num_particles):
            # Generate random particle speed
            speed = random.uniform(3,6)
            # Rate of particle decay is proportional to particle speed
            decay = speed / 40.0
            # Start at same x position as firework
            X0 = np.copy(self.X)
            # Initial velocity is random ve
            v0 = np.random.uniform(-0.5, 0.5, 3) * speed + self.V
            Particle(self.add, self.discard, X0, v0, color, decay)
        super().die()

class Window(pyglet.window.Window):
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.set_minimum_size(300, 200)
        pyglet.clock.schedule(self.update)
        self.frame = 0
        self.fireworks = set()
        self.f_add = set()
        self.f_discard = set()
        self.launchpad = wf.Wavefront('launchpad.obj')
        self.fs = False
        self.camera_loc = np.array([[0.0], [1.0], [-7.0]])
        self.up = [0.0, 1.0, 0.0]
        self.rate = 30.0 * (math.pi / 180)
        self.X0 = np.array([[0.0], [cam_h], [-cam_r]])
        self.center = center.tolist()

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., float(width)/height, 0.05, 1000)
        glMatrixMode(GL_MODELVIEW)
        return True

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
            Firework(self.f_add, self.f_discard)

        # Draw the landscape
        self.launchpad.draw()

        # Setup to render fireworks
        glShadeModel(GL_FLAT)
        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)

        # Render particles
        for i in self.fireworks:
            i.draw()

    def update(self,dt):
        global rotation
        global rotation_m
        self.frame += 1
        self.fireworks |= self.f_add
        self.fireworks -= self.f_discard
        self.f_add.clear()
        self.f_discard.clear()
        for i in self.fireworks:
            i.update()
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
    
