import cv2
import pyzed.sl as sl 
import numpy as np
import os
import math
import time
import sys
from zedtest import zedmain
from adafruit_servokit import ServoKit
from command_or_passthrough import SBUSmain
from Navigates import Navigate
from PyLidar import LidarMain
from multiprocessing import Process, Pipe, Queue

debug = True

#----------------------------------------------------------
#shooter functions
def init_shooter():
    kit = ServoKit(channels=16)
    kit.servo[1].actuation_range = 100
    kit.servo[1].set_pulse_width_range(1000,2000)

    kit.servo[2].actuation_range = 100
    kit.servo[2].set_pulse_width_range(1000,2000)
    return kit

#gotta tune this
def shoot_projectile(kit):
    #Gun actuation, servo has not yet been included
    kit.servo[1].angle = 100
    kit.servo[2].angle = 100

def turn_off_gun(kit):
    kit.servo[1].angle = 0
    kit.servo[2].angle = 0


def calibrate_shooter(kit):

    input("press Enter to set high")
    kit.servo[1].angle = 100
    kit.servo[2].angle = 100
    input("now plug in the motors and hit enter")
    time.sleep(1)
    kit.servo[1].angle = 0
    kit.servo[2].angle = 0
    print("Calibrated!")




#---------------------------------------------------

#------------------------------------------
#init shooter
kit = init_shooter()

#---------------------------------------------



#null value is 992

navi = Navigate(pp=0.1,pi=0.001,pd=0,yp=0.1,yi=0.001,yd=0,tp=0.1,ti=0.001,td=0, radius=100, time=0.01, allowedError=10, allowedAngle=5, orbitSpeed=1100, _hover=100)


#however many we can fit in there
#num_bullets = 20
#----------------------------------
#Zed Process Start up
if debug:
    print("Initializing the processes")

zed_conn, mainzed_conn = Pipe() # Set up communuication queue
object_find = Process(target= zedmain, args = (zed_conn,)) #create process object for ZED code
object_find.start() # start the ZED process

#time.sleep(5)

#SBUS Process Startup
sbus_conn, main_conn = Pipe()
SBUS_script = Process(target= SBUSmain, args= (sbus_conn,))
SBUS_script.start()
old_input = [0]*16 # at the start, we'd prefer the drone not to move unless given input


#Lidar Setup
lidar_conn, mainlidar_conn = Pipe()
Lidar_script = Process(target= LidarMain, args=(lidar_conn,))
Lidar_script.start()

if debug:
    print("started")

#--------------------------------------

#main.py is looping way quicker than PySBUS but hopefully its still fine
def SBUScheck(main_conn):

    while not main_conn.poll():
        #print("waiting for data")
        pass

    taranis = main_conn.recv()


    
    return taranis

#------------------------------------------------------------
#Variable init
update_time = 0
empty_time = 0
garbo_time = 0
garbol_time = 0
position = []
framesLost = 0
height_comm = 100
run_time = 0.5
wait_ended = 0
ready = True
#--------------------------------------------------------------


try:
    sbus_start = time.time()
    taranis = SBUScheck(main_conn)
    sbus_end = time.time()




    while taranis[0] == 1:
        taranis = SBUScheck(main_conn)


    #wait until zed module has finished loading
    if debug:
        print("about to wait for Zed")
    while not mainzed_conn.poll():
        pass
    zed_start = time.time()
    position = mainzed_conn.recv()
    zed_end = time.time()

    while not mainlidar_conn.poll():
        pass
    lidar_start = time.time()
    height = mainlidar_conn.recv()
    lidar_end = time.time()

    land = taranis[7]
    auto_mode = taranis[6]
    fire = taranis[8]
    python_exit = taranis[4]
    frame_lost = taranis[11]


    while python_exit > 1500:

        curr_time = time.time()

        #step one: check for RC input
        taranis = SBUScheck(main_conn)

        # I chose a channel that should never have any reason AT ALL to change, so if its not default - something is wrong
        #this is kind of a jank work around but it provides one more layer of protection
        if taranis[0]!= 1 and taranis[10] == 992 and taranis[12] == 992: # only update modes if the data was meaningful, all 1s means nothing good
            land = taranis[7]
            auto_mode = taranis[6]
            fire = taranis[8]
            python_exit = taranis[4]
            frame_lost = taranis[11]

        if debug:
            print("inputs: ",taranis)

        if frame_lost > 1500:
            framesLost += 1


        #if its been indicated its time to land, ignore everything else until instructed otherwise
        if land > 1500:
            navi.hover = 20 # measure this
            height = mainlidar_conn.recv()

            if debug:
                print("Current height: ", height)

            height_comm = navi.heightTick(height)

            #keep emptying the zed pipe
            if mainzed_conn.poll():
                garbo = mainzed_conn.recv()
                garbo_time += 1

            if height <= 20:
                #if we reach low height in land mode, cut power
                if debug:
                    print("Close to ground, cut power")
                python_exit = 992
            
            #load commands and send them out
            #everything except thrust should be neutral
            commands = [int(height_comm), 992, 992, 992, taranis[4], taranis[5],taranis[6], taranis[7], taranis[8], taranis[9], 992, taranis[11], taranis[12], taranis[13], taranis[14], taranis[15]] 
            main_conn.send(commands)


        #if we don't need to land, continue on
        #if autonmous mode, start doing the autonomous thing
        elif auto_mode > 1500:
            navi.hover = 100
            #step two: check for ZED input
            if mainzed_conn.poll():
                position = mainzed_conn.recv()
                update_time += 1
            else:
                empty_time += 1
            if debug:
                print("position: ", position)

            #step three: check for Lidar input
            height = mainlidar_conn.recv()

            #Step four: run PID loop
            yaw_comm, pitch_comm, roll_comm = navi.tick(position[0], position[2])
            height_comm = navi.heightTick(height)

            #Step 5: shoot if we're at the destination
            #reset no change number
            if yaw_comm == 992 and pitch_comm == 992 and roll_comm == 992 and ready:
                #grab current time
                curr_time = time.time()
                wait_ended = curr_time + run_time
                
                #don't start function till its finished
                ready = False

                #shoot
                shoot_projectile(kit)
                #num_bullets -= 1

            #if num_bullets =< 0:
                #print("reload plz")
                #add in some sort of indicator here

            #Step 6: load commands into a list
            #only send if its auto_mode bc SBUS knows to passthrough if there are no commands
            commands = [int(height_comm), int(roll_comm), int(pitch_comm), int(yaw_comm), taranis[4], taranis[5],taranis[6], taranis[7], taranis[8], taranis[9], 992, taranis[11], taranis[12], taranis[13], taranis[14], taranis[15]]
            if debug:
                print("commands: ", commands)

            #Step 7: Send the commands
            main_conn.send(commands)

        #Garbage collection if its not autonomous mode or landing mode

        if mainzed_conn.poll():
            garbo = mainzed_conn.recv()
            garbo_time += 1
        if mainlidar_conn.poll():
            garbo = mainlidar_conn.recv()
            garbol_time += 1

        if fire > 1500 and ready:
            #grab current time
            curr_time = time.time()
            wait_ended = curr_time + run_time

            ready = False

            shoot_projectile(kit)
            #num_bullets -= 1
        
        #turn off the gun once it's been on long enough
        if curr_time >= wait_ended:
            turn_off_gun(kit)
            ready = True

        

except Exception as e:
    print("Fatal Errors:", e)

finally:

    #shut off everything
    if debug:
        print("Times updated directions is ", update_time)
        print("Times left as is ", empty_time)
        print("Time spent emptying zedq is ", garbo_time)
        print("Frames lost is ", framesLost)
        print("Sbus function time is ", (sbus_end - sbus_start))
        print("Zed function time is ", (zed_end - zed_start))
        print("Lidar function time is ", (lidar_end - lidar_start))
        print("Time spend emptying lidar is ", garbol_time)


    #graceful exits
    mainzed_conn.send(True)

    commands = [0]*16
    main_conn.send(commands)

    mainlidar_conn.send(True)



    while object_find.is_alive():
        if mainzed_conn.poll():
            garbo = mainzed_conn.recv()
    if debug:
        print(F"ZED program closed")

    while SBUS_script.is_alive():
        if main_conn.poll():
            garbo = main_conn.recv()
    if debug:
        print(F"sbus program closed")
    
    x=0
    while Lidar_script.is_alive():
        if mainlidar_conn.poll():
            garbo = mainlidar_conn.recv()
    if debug:
        print(F"Lidar program closed")
    

    object_find.terminate()
    turn_off_gun(kit)
    SBUS_script.terminate()
    Lidar_script.terminate()
