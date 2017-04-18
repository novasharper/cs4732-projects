#!/bin/env python3

from pyglet.gl import *
import random

COLORS = [(1.0,0.5,0.5),(1.0,0.75,0.5),(1.0,1.0,0.5),(0.75,1.0,0.5),
          (0.5,1.0,0.5),(0.5,1.0,0.75),(0.5,1.0,1.0),(0.5,0.75,1.0),
          (0.5,0.5,1.0),(0.75,0.5,1.0),(1.0,0.5,1.0),(1.0,0.5,0.75)]

class Particle(object):
    def __init__(self,x,y,z,speed,color):
        self.life = 1.0
        self.fade = random.random()/10.0 + 0.003
        self.x = x
        self.y = y
        self.z = z
        self.xi = (random.random()-0.5)*speed
        self.yi = (random.random()-0.5)*speed
        self.zi = (random.random()-0.5)*speed
        self.xg = 0
        self.yg = -0.08
        self.zg = 0
        self.batch = pyglet.graphics.Batch()
        self.img = pyglet.resource.image('Particle.bmp')
        self.group = pyglet.sprite.SpriteGroup(self.img.texture,
            blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE)
        self.vertex_list = self.batch.add(4, GL_TRIANGLE_STRIP, self.group,
            'v3f', 'c3f', ('t2f',(1,1,0,1,1,0,0,0)))
        self.vertex_list.vertices[0:12] = [self.x+0.5,self.y+0.5, self.z,self.x-0.5,self.y+0.5,self.z,self.x+0.5,self.y-0.5,self.z,self.x-0.5,self.y-0.5,self.z] 
        self.vertex_list.colors[0:12] = color * 4

    def update(self):
        self.life -= self.fade
        self.x += self.xi/100
        self.y += self.yi/100
        self.z += self.zi/100

        self.xi += self.xg
        self.yi += self.yg
        self.zi += self.zg


    def draw(self):
        if self.life >0:
            self.vertex_list.vertices[0:12] = [self.x+0.5,self.y+0.5, self.z,self.x-0.5,self.y+0.5,self.z,self.x+0.5,self.y-0.5,self.z,self.x-0.5,self.y-0.5,self.z]
            self.batch.draw()


class Fireworks(object):
    def __init__(self):
        x = random.randint(-4,5)
        y = random.randint(-2,4)
        z = random.randint(-2,1)
        speed = random.randint(5,10)
        color = random.choice(COLORS)
        self.fireworks = [Particle(x,y,z,speed,color) for i in range(100)]
        
    def draw(self):
        for i in self.fireworks:
            i.draw()

    def update(self):
        for i in self.fireworks:
            i.update()        

class Window(pyglet.window.Window):
    def __init__(self, *args,**kwargs):
        super(Window, self).__init__(*args,**kwargs)
        self.set_minimum_size(300,200)
        pyglet.clock.schedule(self.update)
        self.frame = 0
        self.fireworks = [Fireworks() for i in range(4)]

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
        if self.frame % 17 == 1:
            self.fireworks.pop(0)
            self.fireworks.append(Fireworks())
        for i in self.fireworks:
            i.draw()

    def update(self,dt):
        self.frame += 1
        for i in self.fireworks:
            i.update()

if __name__ =='__main__':
    window = Window(width = 800,height = 600, caption = 'fireworks',resizable = True)
    pyglet.app.run()
    
