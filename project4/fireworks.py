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
    [ 0.5,  0.5, 0],
    [-0.5,  0.5, 0],
    [ 0.5, -0.5, 0],
    [-0.5, -0.5, 0]
])

half_side = 0.1
center = np.array([-0.5, 0.0, -1.0])

class Particle(object):
    show_fade = False
    def __init__(self, add, discard, start, v0, color, decay=-1):
        self.add = add
        self.discard = discard
        self.life = 1.0
        if decay > 0:
            self.fade = (0.2 +  0.8 * random.random()) / decay
            self.show_fade = True
        self.X = start # Initial position
        self.V = v0    # Velocity vector
        self.g = np.array([0, -0.08, 0])
        self.batch = pyglet.graphics.Batch()
        self.img = pyglet.resource.image('Particle.bmp')
        self.group = pyglet.sprite.SpriteGroup(self.img.texture,
            blend_src=GL_SRC_ALPHA, blend_dest=GL_DST_ALPHA)
        self.vertex_list = self.batch.add(4, GL_TRIANGLE_STRIP, self.group,
            'v3f', 'c4f', ('t2f', (1,1, 0,1, 1,0, 0,0)) )
        self.update_position()
        self.vertex_list.colors[0:16] = [*color, 1] * 4
        self.add.add(self)

    def update(self):
        if self.show_fade:
            self.life -= self.fade
            self.vertex_list.colors[3::4] = [self.life] * 4
        # Update position using velocity
        self.X += self.V / 100
        # Apply Gravity
        self.V += self.g

    def update_position(self):
        self.vertex_list.vertices[0:12] = (self.X + offset).ravel()

    def is_alive(self):
        return self.life > 0

    def draw(self):
        if self.is_alive():
            self.update_position()
            self.batch.draw()
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


    def is_alive(self):
        return self.X[1] < 2 and self.V[1] >= 1

    def die(self):
        color = random.choice(COLORS)
        for i in range(100):
            speed = random.uniform(3,6)
            decay = 40.0 / speed
            X0 = np.copy(self.X)
            v0 = np.random.uniform(-0.5, 0.5, 3) * speed + self.V
            #print(self.X, v0)
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

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., float(width)/height, 0.05, 1000)
        glMatrixMode(GL_MODELVIEW)
        return True

    def on_draw(self):
        glLoadIdentity()
        gluLookAt(0.0, 0.2, -5.0,
                  0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glLightfv(GL_LIGHT0, GL_POSITION, lightfv(-30, 30, 30, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, lightfv(0.1, 0.2, 0.1, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightfv(0.1, 0.3, 0.1, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, lightfv(0.3, 0.3, 0.3, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        if self.frame % random.randint(30, 51) == 1:
            Firework(self.f_add, self.f_discard)

        self.launchpad.draw()

        glDisable(GL_LIGHTING)
        glDisable(GL_COLOR_MATERIAL)
        glDisable(GL_DEPTH_TEST)
        glShadeModel(GL_FLAT)

        for i in self.fireworks:
            i.draw()

    def update(self,dt):
        self.frame += 1
        self.fireworks |= self.f_add
        self.fireworks -= self.f_discard
        self.f_add.clear()
        self.f_discard.clear()
        for i in self.fireworks:
            i.update()

    def on_key_release(self, symbol, modifiers):
        if symbol == key.F:
            self.fs ^= True
            self.set_fullscreen(self.fs)
        if symbol == key.Q:
            pyglet.app.exit()


if __name__ =='__main__':
    window = Window(width = 800, height = 600, caption = 'fireworks')
    pyglet.app.run()
    
