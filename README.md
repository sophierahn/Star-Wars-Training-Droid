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
It was also very handy to reference this breakdown of FrSky SBUS in making the library: https://os.mbed.com/users/Digixx/notebook/futaba-s-bus-controlled-by-mbed/

The Lidar library was taken from Adafruit: https://github.com/adafruit/Adafruit_CircuitPython_LIDARLite
The ZED code was taken from their tutorials: https://github.com/stereolabs/zed-examples

The Navigates file was written by Benjamin Macdonell for use in this project, it handles the PID loop

This repo requires multiprocessing, cython, numpy, open cv, servokit, and lots else

# SBUS.py Function Descriptions

__init__(self, _SBUS_PACKET_SIZE = 25,_SBUS_DESYNC_END = 2,_SBUS_DESYNC_HDR = 1,_SBUS_HEADER = 0b00001111,_SBUS_END = 0b00000000,_nextRead = 50,SBUS_OPT_C17 = 0b0001,SBUS_OPT_C18 = 0b0010,SBUS_OPT_FL = 0b0100,SBUS_OPT_FS = 0b1000, _NUM_CHANNELS = 16, INSTALL_ERROR = False)

Class object constructor - variables should remain unchanged. If the communication protocol requires different parameters from those described in the constructor, the decoder and encoder functions will need to be rewritten as well.

__install__(self)

This function installs the serial port with settings specifically for the FrSky SBUS protocol and returns an object used to perform actions with this port. This includes the serial port “/dev/ttyUSB0”, baudrate of 100000, eight bit sized bytes, even parity, and two stop bits. If your hardware requires different port settings, be sure to alter the function accordingly

__read__(self, serial_port_object)

This function reads 50 bytes and decodes a full SBUS packet into a list representing 16 input channels. If this packet is fully valid, it returns this 16 entry list. If it fails validation (a desync event), the packet is set to [1,1,1,1,1800,1,1,1,1,1,1,1800,1,1,1,1]. These values were chosen to act as flags in the main program and it is intended that the program using this library implements error checking accordingly. 

__buildPacket__(self, 16_entry_list, digitalchannel_boolean, digitalchannel_boolean, failsafe_boolean, frameLost_boolean)

This function takes in a 16 entry list (the RC commands) as well as boolean values for the error flags, and places them in an output list that should be given directly to the write function. In most cases, the boolean flags should all be set to true.

__write__(self, output_list, serial_port_object)

This function writes the output list to the indicated serial port.


# Program Descriptions

__Zed.py__

This program is responsible for controlling the ZED 2 camera and handling all computer vision operations. As it is called in Main.py, it should return the coordinates to the target. An alternate version of this program exists, VisZed.py, that can only be called by VisMain.py. Together, it opens a window to stream video from the ZED 2 camera. It is useful for debugging but increases CPU usage. 

__command_or_passthrough.py__ 

This program works in tandem with Main.py by handling the sending and receiving of SBUS packets which are passed through queues to Main.py.

__Main.py__

This program is the hub of the operation. It begins all of the processes that run simultaneously and runs as a state machine for the different operation modes. It also calls the Navigates library for PID loops and the Lidar functions for Lidar measurements. An alternate version, VisMain.py, to run the data and open a window to stream video from the ZED 2 camera.
