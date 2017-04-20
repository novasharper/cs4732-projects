#!/bin/env python3

from pyglet.gl import *
import ratcave as rc
import random
import math

COLORS = [(1.0,0.5,0.5),(1.0,0.75,0.5),(1.0,1.0,0.5),(0.75,1.0,0.5),
          (0.5,1.0,0.5),(0.5,1.0,0.75),(0.5,1.0,1.0),(0.5,0.75,1.0),
          (0.5,0.5,1.0),(0.75,0.5,1.0),(1.0,0.5,1.0),(1.0,0.5,0.75)]

class Particle(object):
    def __init__(self, particles, add, discard, x, y, z, speed, color):
        self.particles = particles
        self.add = add
        self.discard = discard
        self.life = 1.0
        self.fade = random.random() / 10.0 + 0.003
        self.x = x
        self.y = y
        self.z = z
        self.xi = speed[0]
        self.yi = speed[1]
        self.zi = speed[2]
        self.xg = 0
        self.yg = -0.08
        self.zg = 0
        self.batch = pyglet.graphics.Batch()
        self.img = pyglet.resource.image('Particle.bmp')
        self.group = pyglet.sprite.SpriteGroup(self.img.texture,
            blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE)
        self.vertex_list = self.batch.add(4, GL_TRIANGLE_STRIP, self.group,
            'v3f', 'c3f', ('t2f', (1,1, 0,1, 1,0, 0,0)) )
        self.update_position()
        self.vertex_list.colors[0:12] = color * 4
        self.add.add(self)

    def update(self):
        self.life -= self.fade
        self.x += self.xi/100
        self.y += self.yi/100
        self.z += self.zi/100

        self.xi += self.xg
        self.yi += self.yg
        self.zi += self.zg

    def update_position(self):
        self.vertex_list.vertices[0:12] = [
            self.x + 0.5, self.y + 0.5, self.z, # (1, 1)
            self.x - 0.5, self.y + 0.5, self.z, # (0, 1)
            self.x + 0.5, self.y - 0.5, self.z, # (1, 0)
            self.x - 0.5, self.y - 0.5, self.z  # (0, 0)
        ]

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
    def __init__(self, particles, add, discard):

        x = random.randint(-4,5)
        y = 0
        z = random.randint(-2,1)

        speed = random.randint(5,7)
        theta = (1 - 0.25 * random.random()) * math.pi / 2
        phi = random.random() * math.pi * 2
        yi = math.sin(theta) * speed
        proj_s = math.cos(theta) * speed
        xi = math.cos(phi) * proj_s
        zi = math.sin(phi) * proj_s
        
        color = random.choice(COLORS)

        super().__init__(particles, add, discard, x, y, z, (xi, yi, zi), color)


    def is_alive(self):
        return self.yi >= 0.5

    def die(self):
        color = random.choice(COLORS)
        for i in range(100):
            speed = random.randint(5,10)
            speed = tuple([(random.random()-0.5)*speed for i in range(3)])
            Particle(self.particles, self.add, self.discard, self.x, self.y, self.z, speed, color)
        super().die()

class Window(pyglet.window.Window):
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.set_minimum_size(300,200)
        pyglet.clock.schedule(self.update)
        self.frame = 0
        self.fireworks = set()
        self.f_add = set()
        self.f_discard = set()
        obj_reader = rc.WavefrontReader('launchpad.obj')
        launchpad = obj_reader.get_mesh('Plane')
        launchpad.position = 0, 0, 0
        self.launchpad = rc.Scene(meshes=[launchpad])
        for i in range(4):
            Firework(self.fireworks, self.f_add, self.f_discard)

    def on_draw(self):
        glViewport(0, 0, window.width, window.height)
        glMatrixMode(gl.GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, window.width/window.height, 0.05, 1000)
        glMatrixMode(gl.GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 4.0,
                  0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.frame % 100 == 1:
            Firework(self.fireworks, self.f_add, self.f_discard)
        self.launchpad.draw()
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

if __name__ =='__main__':
    window = Window(width = 800, height = 600, caption = 'fireworks')
    pyglet.app.run()
    
