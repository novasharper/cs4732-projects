#!/bin/env python3
"""
Module         : boids.py
Author         : Patrick Long
Email          : pllong@wpi.edu
Course         : CS 4732

Description    : Simulate the interactions between simplistic organisms (Boids)

Date           : 2017/04/14
"""

import cocos
from cocos.sprite import Sprite
from cocos.actions import Action
from cocos.text import Label
from cocos.layer import ColorLayer, Layer
from cocos.scene import Scene
from cocos.director import director
import math
from vector2d import Vector2 as v2d
from vector2d import limit
from random import randint, random
import itertools

# (COLOR, NAME, FLEE, CHASE)
boid_info = (
    ((255, 0, 0), 'RED', 2, 1),
    ((0, 255, 0), 'GREEN', 0, 2),
    ((0, 0, 255), 'BLUE', 1, 0)
)

spawn_padding = 25   # Padding for spawnboxex
obstacle_radius = 96 # Radius of obstacle
cell_size = 64       # Size of cell
arena_size = 900     # Size of "arena"

# Spawn position for each boid is
# (rand(b1, b2), rand(b1, b2)) * bounds[index] + center
box_offsets = (
    (-1, -1),
    (1, -1),
    (-1, 1),
    (1, 1)
)

class BoidController(Action):
    """ Controller for boid """
    # Stuff to ensure action is not removed as terminated
    scheduled_to_remove = False
    _done = False
    _max_f = 60.0        # Maximum force applied to boid
    _speed_cap = 100.0   # Maximum speed
    _sensing_range = 256 # Maximum sensing range
    _min_dist = 48       # Minimum ideal distance b/n boids
    def __init__(self, _id, _type, _start):
        super().__init__()
        # Window + grid dimensions
        self._win_w, self._win_h = director.get_window_size()
        self._grid_w = int(math.ceil(self._win_w / cell_size))
        self._grid_h = int(math.ceil(self._win_h / cell_size))
        # Starting Boid "type"
        self._type = _type
        # Starting position
        self._posn = v2d(*_start)
        self._grid = self.calc_grid()
        # Starting velocity
        self._v = v2d(randint(-10, 10), randint(-10, 10)) * ((2 + self._type) * 2)
        self._a = v2d(0, 0)
        # Boid ID
        self._id = _id
        # Generate list of grid offsets to check
        radius = int(math.ceil(self._sensing_range / cell_size))
        bounds = (-radius, radius + 1)
        self.check = list(itertools.product(range(*bounds), range(*bounds)))

    def set_type(self, _new_type):
        """ Update type of boid """
        # Check to see if type is changing
        if _new_type == self._type:
            return
        # Move from current boid set to boid set for new type
        self.target._grid[self._grid][self._type].discard(self)
        self.target._grid[self._grid][_new_type].add(self)
        # Update type
        self._type = _new_type
    
    def calc_grid(self):
        """ Calculate position on grid """
        return int(self._posn.x / cell_size), int(self._posn.y / cell_size)

    def update_grid(self):
        """ Update the grid of boids """
        # Check to see if we have moved squares
        _new_grid = self.calc_grid()
        if _new_grid == self._grid:
            return
        # Remove from old square and add to new square
        self.target._grid[self._grid][self._type].discard(self)
        self.target._grid[_new_grid][self._type].add(self)
        # Update coordinates
        self._grid = _new_grid
    

    def obstacle_force(self, obs):
        """ Get 'avoidance' force applied by obstacle """
        v = self._v.normalized()
        # Look ahead proportional to velocity
        look_ahead = self._min_dist * 2 * self._v.magnitude() / self._speed_cap
        ahead = self._posn + v.normalized() * look_ahead
        # Force is applied from obstacle in direction to future position
        diff = ahead - obs._posn
        # We won't collide, so it's okay
        if abs(diff) > obs.radius * 1.2:
            return v2d(0, 0)
        # Magnitude of force is maximum force
        return self._max_f * diff.normalize()

    def avoid_obstacles(self):
        """ Get acceleration due to avoiding obstacles """
        _a = v2d(0, 0)
        _count = 0

        # Process all obstacles
        for obs in self.target._obstacles:
            # Vector from target to me
            diff = self._posn - obs._posn
            dist = abs(diff) # Distance
            if 0 < dist < self._sensing_range: # Is it in range?
                # Get force exherted by obstacle
                _f = self.obstacle_force(obs)
                if _f.magnitude() > 1: # Is the force significant?
                    _a += _f
                    _count += 1
        
        if _count > 0:
            _a /= _count
            _a *= self._speed_cap
            #limit(_a, self._max_f)
        
        return _a

    def force(self, targets):
        """ Get acceleration from `targets` """
        _a = v2d(0, 0)
        _count = 0

        # Process targets to determine force
        for target in targets:
            # Vector from target to me
            diff = self._posn - target._posn
            dist = abs(diff) # Distance
            if 0 < dist < self._sensing_range: # Is it in range?
                _count += 1

                # Convert vector to direction
                diff.normalize()
                if dist < self._min_dist:
                    # If we are going to collide, "convert"
                    # target to my species
                    if dist < 16 and diff.dot(self._v.normalized()) < -0.6:
                        target.set_type(self._type)
                    diff /= (dist / self._min_dist)
                
                _a += diff
        
        if _count > 0:
            _a /= _count
            _a *= self._speed_cap
            limit(_a, self._max_f)
        
        return _a

    def flock(self, targets):
        """ Get acceleration due to flocking behavior """
        sep = v2d(0, 0) # Force to separate
        coh = v2d(0, 0) # Force to cohere
        aln = v2d(0, 0) # Force to align
        count = 0

        # Sum forces applied by flock
        for target in targets:
            diff = self._posn - target._posn
            dist = abs(diff)

            if 0 < dist < self._sensing_range:
                count += 1

                diff.normalize()
                # If too close, scale separation factor
                if dist < self._min_dist:
                    diff /= (dist / self._min_dist)
                
                # Separation driven by proximity of flock members
                sep += diff
                # Cohesion is steering towards average flock location
                coh += target._posn
                # Alignment is a force acting in average velocity
                # of the flock
                aln += target._v

        if count > 0:
            # Calculate the average separation vector
            sep.normalize()
            sep *= self._speed_cap
            sep -= self._v
            limit(sep, self._max_f)

            # Calculate the average velocity of the "flock"
            aln.normalize()
            aln *= self._speed_cap
            aln -= self._v
            limit(aln, self._max_f)

            # Calculate the coherence force (flocking attractor)
            coh /= count
            coh = self._steer(coh, True)
            

        return sep * 1.5 + coh + aln

    def _steer(self, dest, damp=False):
        """ Steer towards destination """
        diff = dest - self._posn
        dist = abs(diff)
        if dist > 0: # Not at target
            diff.normalize()
            # Damp coherence when it approaches min dist
            if damp and (dist < self._min_dist):
                diff *= self._speed_cap * 0.1
            else:
                diff *= self._speed_cap
            # Calculate force needed to aim towards destination
            diff -= self._v
            limit(diff, self._max_f)
        else:
            diff = v2d(0, 0)
        return diff

    def think(self):
        """ Determine acceleration """
        # Sets of boids in range (separated by type)
        _boids = [set(), set(), set()]
        # Check all grid squares in reach of radius
        _grid = self._grid
        for dx, dy in self.check:
            _x, _y = (_grid[0] + dx, _grid[1] + dy)
            # If the coordinates are on the grid, add occupants to list of boids
            if 0 <= _x < self._grid_w and 0 <= _y < self._grid_h:
                targets = self.target._grid[_x, _y]
                _boids[0] |= targets[0]
                _boids[1] |= targets[1]
                _boids[2] |= targets[2]
        # Determine forces acting upon boid
        _flee  = self.force(_boids[boid_info[self._type][2]])
        _chase = self.force(_boids[boid_info[self._type][3]])
        _flock = self.flock(_boids[self._type])
        _obs   = self.avoid_obstacles()
        # F = ma, mass = 1
        self._a = _chase - _flee + _flock + _obs
    
    def check_borders(self):
        """ Wrap, we are on a donut """
        # Go Homer!
        # https://en.wikipedia.org/wiki/Torus#Flat_torus
        if self._posn.x < 0:
            self._posn.x += self._win_w
        elif self._posn.x > self._win_w:
            self._posn.x -= self._win_w
        if self._posn.y < 0:
            self._posn.y += self._win_h
        elif self._posn.y > self._win_h:
            self._posn.y -= self._win_h

    def step(self, dt):
        """ Update the Boid controller """

        self.think()

        # Update velocity
        self._v += self._a * dt
        limit(self._v, self._speed_cap)

        # Update position
        self._posn += self._v * dt
        self.check_borders()
        
        # Update Boid (target)
        self.update_grid()
        self.target.rotation = - (self._v.rot(True) - 90)
        self.target.position = (self._posn.x, self._posn.y)
        self.target._type = self._type
    
    def __hash__(self):
        """ The hash of a boid controller is the Boid ID """
        return self._id

class Boid(Sprite):
    """ This is the base class for defining a Boid """
    def __init__(self, _id, _start):
        super().__init__('boid2.png', scale=0.5)
        # Type is a hash of ID
        self._type = _id % 3
        # Add Controller
        self.do(BoidController(_id, self._type, _start))

    def draw(self):
        # Update color
        self.color = boid_info[self._type][0]
        super().draw()
    
    def on_enter(self):
        """ Handle parent scene entered """
        # Obtain pointer to Parent Grid + Obstacles
        self._grid      = self.parent._grid
        self._obstacles = self.parent._obstacles
        super().on_enter()

class Obstacle(Sprite):
    """ This will be the obstacle in the center """
    def __init__(self, location=(arena_size/2,arena_size/2), radius=obstacle_radius):
        super().__init__('rock.png') # Sprite is a rock (Unlimited Stock Art)
        # Set draw position
        self.position = location
        # Set position for use in collision detection
        self._posn = v2d(*location)
        # Set radius, scale derives from radius
        self.radius = radius
        self.scale = 2 * radius / self.width
    
    def on_enter(self):
        """ Handle parent scene entered """
        # Add self to list of obstacles
        self.parent._obstacles.add(self)
        super().on_enter()

class BoidLayer(ColorLayer):
    """ The main layer that holds all the Boids """
    def __init__(self, num_boids):
        super().__init__(255, 255, 255, 255)

        win_sz = director.get_window_size()

        # Create and initialize grid for storing boids
        self._grid = {}
        cell_nums = range(int(math.ceil(arena_size / cell_size)))
        for i in cell_nums:
            for j in cell_nums:
                self._grid[i,j] = (set(), set(), set())
        
        # Set of obstacles
        self._obstacles = set()

        # Bounds for spawning boids
        box_sz = (obstacle_radius + spawn_padding,
            arena_size / 2 - spawn_padding)

        # Only one obstace
        obstacle = Obstacle()
        self.add(obstacle)

        # Spawn boids
        for i in range(num_boids):
            box_id = randint(0, 99) % 4
            start = (
                randint(*box_sz) * box_offsets[box_id][0] + arena_size / 2,
                randint(*box_sz) * box_offsets[box_id][1] + arena_size / 2
            )
            boid = Boid(i, start)
            self.add(boid)

# Only run as script if run directly
if __name__ == '__main__':
    director.init(caption='Boids of a Feather!!', width=arena_size, height=arena_size)
    director.set_show_FPS(True)
    director.run(Scene(BoidLayer(100)))