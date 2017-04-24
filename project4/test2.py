#!/bin/env python3

from pyglet.gl import *
import numpy as np
import random

COLORS = [(1.0,0.5,0.5),(1.0,0.75,0.5),(1.0,1.0,0.5),(0.75,1.0,0.5),
          (0.5,1.0,0.5),(0.5,1.0,0.75),(0.5,1.0,1.0),(0.5,0.75,1.0),
          (0.5,0.5,1.0),(0.75,0.5,1.0),(1.0,0.5,1.0),(1.0,0.5,0.75)]

offset = np.array([
    [ 1,  1, 0],
    [-1,  1, 0],
    [ 1, -1, 0],
    [-1, -1, 0]
])
texture_coords = [
    1, 1,
    0, 1,
    1, 0,
    0, 0
]
r = 1.5

width = 800
height = 600

window = pyglet.window.Window(width = 800, height = 600, caption = 'fireworks')
camera_loc = [0.0, 0.0,  -5.0]
up         = [0.0, 1.0,  0.0]
center     = [0.0, 0.0,  0.0]

sprite = pyglet.resource.image('Particle.png')
sprite_group = pyglet.sprite.SpriteGroup(sprite.texture, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
batch = pyglet.graphics.Batch()
particles = [batch.add(4, GL_TRIANGLE_STRIP, sprite_group, 'v3f', 'c3f', 't2f') for i in range(2)]
for vtx in particles:
    color          = random.choice(COLORS)
    X              = np.array([random.uniform(-r, r), random.uniform(-r, r), 0])
    vtx.colors     = color * 4
    vtx.vertices   = (X + offset).flatten()
    vtx.tex_coords = texture_coords

@window.event
def on_draw():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., float(width)/height, 0.05, 1000)
    glMatrixMode(GL_MODELVIEW)

    glLoadIdentity()
    gluLookAt(*camera_loc, *center, *up)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Render particles
    batch.draw()

pyglet.app.run()
    
