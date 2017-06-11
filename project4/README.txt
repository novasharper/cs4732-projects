Patrick Long (pllong@wpi.edu)
CS 4732
Final Project

Fireworks Simulator

For this project, I used 3 external libraries:
    - pyglet = graphics library
    - PyWavefront = Load + render "launchpad" (Wavefront .OBJ file)
    - numpy = fast matrix/vector math library

To open the program, execute `fireworks.py` using Python 3 (This script will not run in Python 2).

In order to run this project, you need to install pyglet, PyWavefront, and numpy (in addition to Python 3).

   pip install --user pyglet PyWavefront numpy

This project simulates a fireworks show. Fireworks are spawned at random intervals within a small square.
The fireworks are then launched upwards at randomized velocities. When they reach a certain altitude or
their vertical speed falls below a certain threshold, the fireworks explode. The explosion creates an
expanding cloud of particles that fade away as it expands.


Video: https://youtu.be/cTBWuUpyNCQ

WARNING: For some reason, this does not render properly on all computers/operating systems.
It ran perfectly on linux on both my desktop and laptop and on windows on my desktop. However,
the explosion particles did not render properly on windows on my laptop.