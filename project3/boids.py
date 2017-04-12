#!/bin/env python3
"""
Module         : test.py
Author         : Patrick Long
Email          : pllong@wpi.edu
Course         : CS 4732

Description    : Simulate the interactions between simplistic organisms (Boids)

Date           : 2017/04/12
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
import itertools

# (COLOR, NAME, FLEE, CHASE)
boid_info = (
    ((255, 0, 0), 'RED', 2, 1),
    ((0, 255, 0), 'GREEN', 0, 2),
    ((0, 0, 255), 'BLUE', 1, 0)
)

spawn_padding = 50
sensing = (64, 3, 128)
bounds = (-int(math.floor(sensing[1] / 2)), int(math.ceil(sensing[1] / 2)))
check = list(itertools.product(range(*bounds), range(*bounds)))

class BoidController(Action):
    scheduled_to_remove = False
    _done = False
    _drag = 0.1
    _force = 5
    _cohesion = 10
    _separation = 10
    def __init__(self, _id, _type, _start):
        super().__init__()
        # Window dimensions
        self._win_w, self._win_h = director.get_window_size()
        # Starting Boid "type"
        self._type = _type
        # Startubg position
        self._x, self._y = _start
        self._grid = self.get_grid()
        # Starting velocity
        self._vx = randint(-10, 10) * (2 + self._type) * 2
        self._vy = randint(-10, 10) * (2 + self._type) * 2
        # Boid ID
        self._id = _id

    def get_grid(self):
        return int(self._x / sensing[0]), int(self._y / sensing[0])

    def set_type(self, _new_type):
        if _new_type == self._type:
            return
    
    def force(self, targets):
        _dvx, _dvy = (0, 0)
        for target in targets:
            dx = (self._x - target._x)
            dy = (self._y - target._y)
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist > sensing[2]:
                continue
            _dvx += dx * self._force / sensing[0]
            _dvy += dy * self._force / sensing[0]
        return _dvx, _dvy

    def flock(self, targets):
        _dvx, _dvy = (0, 0)
        for target in targets:
            if hash(target) == hash(self):
                continue
            dx = (self._x - target._x)
            dy = (self._y - target._y)
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist < 1:
                continue
            # Separation
            if dist < 2 * sensing[0]:
                _dvx += dx * (1.5 - self._separation / sensing[0])
                _dvx += dy * (1.5 - self._separation / sensing[0])
            # Cohesion
            if dist > 2 * sensing[0]:
                _dvx += dx * self._cohesion / sensing[0]
                _dvx += dy * self._cohesion / sensing[0]
        
        return _dvx, _dvy

    def step(self, dt):
        """Update the Boid

        dt = Delta time between updates (seconds)
        """
        
        _grid = self.get_grid()
        for di, dj in check:
            targets = self.target._grid[_grid]
            _flee = self.force(targets[boid_info[self._type][2]])
            _chase = self.force(targets[boid_info[self._type][3]])
            _flock = self.flock(targets[self._type])
            self._vx += _chase[0] - _flee[0] + _flock[0]
            self._vy += _chase[1] - _flee[1] + _flock[1]
        self._vx *= 1 - self._drag
        self._vy *= 1 - self._drag

        # Update position
        self._x += self._vx * dt
        self._y += self._vy * dt
        # Wrap, we are on a donut
        # Go Homer!
        while self._x < 0:
            self._x += self._win_w
        while self._x > self._win_w:
            self._x -= self._win_w
        while self._y < 0:
            self._y += self._win_h
        while self._y > self._win_h:
            self._y -= self._win_h
        # Find new grid cell
        _grid = self.get_grid()
        if self not in self.target._grid[_grid][self._type]:
            self.target._grid[self._grid][self._type].discard(self)
            self.target._grid[_grid][self._type].add(self)
            self._grid = _grid
        self.target.position = (self._x, self._y)
        self.target._type = self._type
    
    def __hash__(self):
        """ The hash of a boid controller is the Boid ID """
        return self._id

class Boid(Sprite):
    """ This is the base class for defining a Boid """
    def __init__(self, _id, _start):
        super().__init__('boid2.png', scale=0.5)
        self._type = _id % 3
        self.do(BoidController(_id, self._type, _start))

    def draw(self):
        self.color = boid_info[self._type][0]
        super().draw()
    
    def on_enter(self):
        self._grid = self.parent._grid
        super().on_enter()

class Obstacle(Sprite):
    """ This will be the obstacle in the center """
    def __init__(self, location=(320,240), radius=5):
        super().__init__('boid.png', color=(0, 0, 0), scale=radius)
        self.position = location

class BoidLayer(ColorLayer):
    """ The main layer that holds all the Boids """
    def __init__(self):
        super().__init__(255, 255, 255, 255)

        self._grid = {}

        win_sz = director.get_window_size()

        for i in range(int(win_sz[0] / sensing[0])):
            for j in range(int(win_sz[1] / sensing[0])):
                self._grid[i,j] = (set(), set(), set())

        bounds = (spawn_padding, spawn_padding, win_sz[0] - spawn_padding, win_sz[1] - spawn_padding)

        for i in range(100):
            start = (randint(bounds[0], bounds[2]), randint(bounds[1], bounds[3]))
            boid = Boid(i, start)
            self.add(boid)

# Only run as script if run directly
if __name__ == '__main__':
    director.init(caption='Boids of a Feather!!', width=1024, height=576)
    director.run(Scene(BoidLayer()))