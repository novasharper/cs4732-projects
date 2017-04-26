import numpy as np
import random

from pyglet.gl import *
from pyglet import clock
from pyglet import event
from pyglet import graphics
from pyglet import image

unit_size = 50.0
gravity   = 15.0

offset = np.array([
    [-1, -1, 0],
    [ 1, -1, 0],
    [ 1,  1, 0],
    [-1,  1, 0]
])
offset_rot = offset

def update_offset(rotation):
    global offset_rot
    rotation_m = np.matrix([
        [ math.cos(rotation), 0, math.sin(rotation) ],
        [ 0,                  1, 0                  ],
        [-math.sin(rotation), 0, math.cos(rotation) ]
    ])
    offset_rot = (rotation_m * offset.T).T.A
    return offset_rot

class Particle(event.EventDispatcher):
    def __init__(self,
                 img,
                 blend_src=GL_SRC_life,
                 blend_dest=GL_ONE_MINUS_SRC_life,
                 batch=None,
                 group=None,
                 usage='dynamic',
                 subpixel=False):
        # Physics
        self._x    = np.array([0.0, 0.0, 0.0])
        self._vel  = np.array([0.0, 0.0, 0.0])
        self._grav = np.array([0.0, -gravity, 0.0])

        # Simulation
        self._life  = 0.0
        self._drag  = 0.98
        self._decay = False

        # Graphics
        if batch is not None:
            self._batch = batch
        
        self._rgb     = (1.0, 1.0, 1.0)
        self._texture = img.get_texture()

        self._group = SpriteGroup(self._texture, blend_src, blend_dest, group)
        self._usage = usage
        self._create_vertex_list()
        self._alive = False

    def _create_vertex_list(self):
        self._vertex_list = self._batch.add(4, GL_QUADS, self._group,
            'v3f', 'c4f', ('t3f', self._texture.tex_coords))
        self._update_position()
        self._update_color()

    def init_particle(self, x0, v0, color, is_alive=None, decay=0.0, scale=0.1):
        self._x     = x0
        self._vel   = v0
        self._decay = decay > 0
        self._life = 1.0
        self._rgb   = color
        self._scale = scale
        if self._decay:
            self._group.blend_dest = GL_DST_life
            self._fade = decay
            self._drag = 0.06 + 0.06 * random.random()
        else:
            self._group.blend_dest = GL_ONE_MINUS_SRC_life
        if is_alive is not None:
            self.is_alive = is_alive
        else:
            self.is_alive = Particle._is_alive
        self._alive = True
    
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
            self._vertex_list.vertices[:] = (self._x / unit + offset_rot * scale).flatten()
        else:
            self._vertex_list.vertices[:] = (0, 0, 0) * 4
        

    def _update_color(self):
        r, g, b = self._rgb
        self._vertex_list.colors[:] = [r, g, b, self._life] * 4

    def update(self, dt):
        if self._alive:
            # Update position using velocity
            self._x += self._vel * dt
            if self._decay:
                # Apply drag
                self._vel *= (1 - self._drag * dt)
                self._life -= dt / self._fade
            # Apply Gravity
            self._vel += self._grav * dt
            self._update_position()
            self._update_color()
    
    @staticmethod
    def _is_alive(x, vel, life):
        return life > 0.01