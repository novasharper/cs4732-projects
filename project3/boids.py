#!/bin/env python3
"""
Module         : test.py
Author         : Patrick Long
Email          : pllong@wpi.edu
Course         : CS 4732

Description    : Simulate the interactions between simplistic organisms (Boids)

Date           : 2017/04/11
"""

import cocos
from cocos.sprite import Sprite
from cocos.actions import Action
from cocos.text import Label
from cocos.layer import ColorLayer, Layer
from cocos.scene import Scene
from cocos.director import director
from enum import Enum
import math
from random import randint

boid_info = (
    ((255, 0, 0), 'RED', 2, 1),
    ((0, 255, 0), 'GREEN', 0, 2),
    ((0, 0, 255), 'BLUE', 1, 0)
)

spawn_padding = 50
sensing = (5, 20)

class Rule:
    """ This is the base class for establishing a rule """
    def __init__(self):
        return

class BoidController(Action):
    scheduled_to_remove = False
    _done = False
    def __init__(self, _id, _type, _start):
        super().__init__()
        self.win_sz = director.get_window_size()
        self._type = _type
        self._x, self._y = _start
        #self._ctrl = self.target.
        self._vel = (randint(-10, 10) * (1 + self._type), randint(-10, 10) * (1 + self._type))
        self._id = _id
    
    def step(self, dt):
        i0 = self._x / sensing[1]
        j0 = self._y / sensing[1]
        self._x += self._vel[0] * dt
        self._y += self._vel[1] * dt
        if self._x < 0:
            self._x += self.win_sz[0]
        elif self._x > self.win_sz[0]:
            self._x -= self.win_sz[0]
        if self._y < 0:
            self._y += self.win_sz[1]
        elif self._y > self.win_sz[1]:
            self._y -= self.win_sz[1]
        i = self._x / sensing[1]
        j = self._y / sensing[1]
        #if self not in self._ctrl.grid[i,j]:
        #    self._ctrl.grid[i0,j0].discard(self)
        #    self._ctrl.gird[i,j].add(self)
        self.target.position = (self._x, self._y)
        self.target._type = self._type
    
    def __hash__(self):
        return self._id

class Boid(Sprite):
    """ This is the base class for defining a Boid """
    def __init__(self, _id, _start):
        super().__init__('boid.png', scale=0.5)
        self._type = _id % 3
        self.do(BoidController(_id, self._type, _start))

    def draw(self):
        self.color = boid_info[self._type][0]
        super().draw()

class Obstacle(Sprite):
    def __init__(self, location=(320,240), radius=5):
        super().__init__('boid.png', color=(0, 0, 0), scale=radius)
        self.position = location

class BoidLayer(ColorLayer):
    def __init__(self):
        super().__init__(255, 255, 255, 255)

        self._grid = {}

        win_sz = director.get_window_size()

        for i in range(int(win_sz[0] / sensing[1])):
            for j in range(int(win_sz[1] / sensing[1])):
                self._grid[i,j] = set()

        bounds = (spawn_padding, spawn_padding, win_sz[0] - spawn_padding, win_sz[1] - spawn_padding)

        for i in range(100):
            start = (randint(bounds[0], bounds[2]), randint(bounds[1], bounds[3]))
            boid = Boid(i, start)
            self.add(boid)


# Only run as script if run directly
if __name__ == '__main__':
    director.init(caption='Boids of a Feather!!', width=960, height=540)
    director.run(Scene(BoidLayer()))