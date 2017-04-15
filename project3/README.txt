Patrick Long (pllong@wpi.edu)
CS 4732
Project 3

Boids of a Feather!

For this project, I used cocos2d, a 2d Python game library.

To open the program, execute `boids.py` using Python 3 (This script will not run in Python 2).

I included the necessary libraries to run In order to run this project, but if it does
not run, you should to install pygame and cocos2d.

   pip install --user pygame cocos2d

This project simulates a bunch of actors and how they move around the flat torus. There are
three "species" of actor: Red, Green, and Blue. These species have a predator/prey relationship
similar to Rock-Paper-Scisors. In addition to the traditional Boid behavior, each species has
one type that they hunt and another that hunts them (they run away from this).

Video: https://youtu.be/uAHZdPjEi1k