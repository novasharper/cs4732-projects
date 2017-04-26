#!/bin/env python3

from pyglet.gl import *
import numpy as np
import random

import time

COLORS = [(1.0,0.5,0.5),(1.0,0.75,0.5),(1.0,1.0,0.5),(0.75,1.0,0.5),
          (0.5,1.0,0.5),(0.5,1.0,0.75),(0.5,1.0,1.0),(0.5,0.75,1.0),
          (0.5,0.5,1.0),(0.75,0.5,1.0),(1.0,0.5,1.0),(1.0,0.5,0.75)]

offset = np.array([
    [-1, -1, 0],
    [ 1, -1, 0],
    [ 1,  1, 0],
    [-1,  1, 0]
]) * 0.15
r = 1
coords = ((-r, r, r), (r, -r, -r))


width = 800
height = 600

window = pyglet.window.Window(width = 800, height = 600, caption = 'fireworks')
camera_loc = [ 0.0,  0.0, -7.0 ]
up         = [ 0.0,  1.0,  0.0 ]
center     = [ 0.0,  0.0,  0.0 ]

sprite = pyglet.image.load('Particle.png')
tex = sprite.get_texture()
sprite_group = pyglet.sprite.SpriteGroup(tex, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
renders = []
for x,y,z in coords:
    batch = pyglet.graphics.Batch()
    particles = [batch.add(4, GL_QUADS, sprite_group, 'v3f', 'c4f', 't3f') for i in range(1000)]
    for vtx in particles:
        color          = random.choice(COLORS)
        X              = np.array([random.uniform(-r, r)+x, random.uniform(-r, r)+y, random.uniform(-r, r)+z])
        vtx.colors     = [*color, 1.0] * 4
        vtx.vertices   = (X + offset).flatten()
        vtx.tex_coords = tex.tex_coords
    renders.append([batch, particles])

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
    start = time.time()
    for batch,_ in renders:
        batch.draw()
    end = time.time()
    print((end - start) * 1000)

pyglet.app.run()
    
