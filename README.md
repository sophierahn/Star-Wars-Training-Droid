# Star-Wars-Training-Droid

So, you want to build an autonoumous drone to train yourself in the ways of the force?

Have fun. Alot about this repo is highly specific. The SBUS library is a bit more versatile, but even then theres alot of gunk in there that only works for my unique application
Read the code, understand it, ask questions, and get ready for a long project. 

But also HAVE FUN YOU'RE LEARNING HOW TO BECOME A JEDI

Made with:
Jetson Xavier,
Garmin Lidar V3,
Tmotor 2208 1750KV Motors,
Gemfan 5147 Props,
Tmotor F4 FC + 60A ESC Pro 2, 
FrSky X8R Receiver,
FrSky Taranis Controller,
ZED 2 Camera,
blood, sweat, and tears


The SBUS library was based on the c++ library written by Bolderflight: https://github.com/bolderflight/SBUS
The Lidar library was taken from Adafruit: https://github.com/adafruit/Adafruit_CircuitPython_LIDARLite
The ZED code was taken from their tutorials: https://github.com/stereolabs/zed-examples

This repo requires multiprocessing, cython, numpy, open cv, servokit, and lots else

# BEWARE MEMORY LEAKS
