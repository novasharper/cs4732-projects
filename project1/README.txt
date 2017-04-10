Patrick Long (pllong@wpi.edu)
CS 4732
Project 1

Follow My Spline!

For this project I used Unity, specifically Unity 5.4.3, so this or a later version will definitely work.
I think earlier versions will work as well. Basically, what I did was add a Cube, then add the script
FollowSpline to the Cube. This script does two things. First, it controls the Cubes rotation using Slerp.
Second, it moves the cube along a pre-defined spline.

To open the program, just go to the Assets folder and open "main.unity" with Unity Editor.
To run, just play the game/simulation (press the play button).

Video: https://youtu.be/prcePXgPOXo



Catmull-Rom
===========

A0 = (0 - t) * P0 + (t + 1) * P1
A1 = (1 - t) * P1 + (t + 0) * P2
A2 = (2 - t) * P2 + (t - 1) * P3

From here on out, representing values as vectors with P_i as axes

B0 = 0.5 * (1 - t) * A0 + 0.5 * (t + 1) * A1
B1 = 0.5 * (2 - t) * A1 + 0.5 * (t + 0) * A2

B0 = 0.5 * [ (1-t) * < -t, t+1, 0, 0 > + (t+1) * < 0, 1-t, t+1, 0 > ]
   = 0.5 * < t^2-t, -2t^2+2, t^2+t, 0 >

B1 = 0.5 * [ (2-t) * < 0, 1-t, t+1, 0 > + (t+0) * < 0, 0, 2-t, t-1 > ]
   = 0.5 * < 0, t^2-3t+2, -2t^2+4t, t^2-t >

C  = (1 - t) * B0 + t * B1

C  = 0.5 * [ (1-t) * < t^2-t, -2t^2+2, t^2+t, 0 > + t * < 0, t^2-3t+2, -2t^2+4t, t^2-t > ]
   = 0.5 * [ < -t^3+2t^2-t, 2t^3-2t^2-2t+2, -t^3+t, 0 > + < 0, t^3-3t^2+2t, -2t^3+4t^2, t^3-t^2 > ]
   = 0.5 * < -t^3+2t^2-t, 3t^3-5t^2+2, -3t^3+4t^2+t, t^3-t^2 >

c0 =  -t^3 + 2t^2 - t
c1 =  3t^3 - 5t^2     + 2
c2 = -3t^3 + 4t^2 + t
c3 =   t^3 -  t^2