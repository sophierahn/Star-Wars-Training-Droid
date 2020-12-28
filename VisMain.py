import cv2
import pyzed.sl as sl 
import numpy as np
import os
import math
import time
import sys
import board
import busio
import adafruit_lidarlite
from VisZed import Viszedmain
from adafruit_servokit import ServoKit
from command_or_passthrough import SBUSmain
from Navigates import Navigate
from multiprocessing import Process, Pipe, Queue
import random

debug = True

#----------------------------------------------------------
#Gun setup
kit = ServoKit(channels=16)

#Servo set up
kit.servo[2].actuation_range = 90
kit.servo[2].set_pulse_width_range(1000,2000)

#First motor setup
kit.servo[0].actuation_range = 100
kit.servo[0].set_pulse_width_range(1000,2000)

#Second motor setup
kit.servo[1].actuation_range = 100
kit.servo[1].set_pulse_width_range(1000,2000)


#gotta tune this
def shoot_projectile(kit):
    #Gun actuation, servo has not yet been included
    #x = 0
    kit.servo[2].angle  = 80
   # while x < 30:# ramp up, figure out how to make this longer
        #kit.servo[0].angle = x
        #kit.servo[1].angle = x
        #x += 1
    kit.servo[0].angle = 30
    kit.servo[1].angle = 30



def turn_off_gun(kit):
    x = 29
    kit.servo[2].angle = 0
    #while x > 0: # ramp down
        #kit.servo[0].angle = (30-x)
        #kit.servo[1].angle = (30-x)
        #x -= 1
    kit.servo[0].angle = 0
    kit.servo[1].angle = 0



#---------------------------------------------------
#Init Lidar

# Create library object using our Bus I2C port
i2c = busio.I2C(board.SCL, board.SDA)

# Default configuration, with only i2c wires
sensor = adafruit_lidarlite.LIDARLite(i2c)

def CheckLidar(sensor, height):
    try:
        height = sensor.distance
        return height

    except RuntimeError as e:
        # If we get a reading error, just print it and keep truckin'
        print("Lidar Error: ",e)
        return height
    

#units are cm and degrees
navi = Navigate(pp=(-2),pi=0,pd=0,yp=2,yi=0,yd=0,tp=2,ti=0,td=0,rp=2, ri=0, rd=0, radius=100, time=0.01, allowedError=10, orbitSpeed=100, hover=100, hoverThrottle=1200)


#----------------------------------
#Zed Process Start up
if debug:
    print(F"Initializing the processes")

zed_conn, mainzed_conn = Pipe() # Set up communuication queue
object_find = Process(target= Viszedmain, args = (zed_conn,)) #create process object for ZED code
object_find.start() # start the ZED process


#SBUS Process Startup
sbus_conn, main_conn = Pipe()
SBUS_script = Process(target= SBUSmain, args= (sbus_conn,))
SBUS_script.start()

if debug:
    print("Process inited")

#--------------------------------------


def SBUScheck(main_conn, buffer):

    taranis = main_conn.recv() # blocks until there is something to receive
    #Pop the first entry to the list and append most recent commands to the end
    buffer.pop(0)
    buffer.append(taranis)

    return taranis, buffer

#------------------------------------------------------------
#Variable init
time_updated = 0
time_left = 0
garbo_time = 0
garbol_time = 0
position = []
framesLost = 0
height_comm = 100
run_time = 0.3
wait_ended = 0
gun_ready = True
failed_unsafely = 0
height = 0
buffer = [[0]*16]*10 # 10 entries of 16 entry lists
time_shooting = 0
readyToShoot = False
navi_end = 0
navi_start = 0
commands = []
last_auto = False
cool_time = 1
gun_cooling = False
gun_ready = False
off_time = 0
random.seed()
#--------------------------------------------------------------


try:
    #wait until zed module has finished loading
    if debug:
        print("about to wait for Zed")
    while not mainzed_conn.poll():
        pass

    position = mainzed_conn.recv()

    if debug:
        print("about to wait for SBUS")
    start = time.time()


    taranis = main_conn.recv()
    main_conn.send(taranis)

    while taranis[0] == 1:
        taranis = main_conn.recv()
        main_conn.send(taranis)


    height = CheckLidar(sensor, height)


    height_comm = taranis[0] # Presetting first set of commands
    roll_comm = taranis[1]
    pitch_comm = taranis[2]
    yaw_comm = taranis[3]
    fire = taranis[4] # don't even think about firing unless this is high #SG
    python_exit = taranis[5] # SE
    safety = taranis[6] #SD
    arm_disarm = taranis[7] #code never changes this, high means armed  #SC
    auto_mode = taranis[8] # deadmans switch, high means manual and low means auto #SH
    fail_safe = taranis[9] # if there are 10 of these, bad things
    frame_lost = taranis[11] # Just an indicator


    if debug:
        print("starting")

    #just making it harder to close the program
    while python_exit > 1500:
        #print(F"Disarmed, flip switch SE to exit program")
        while arm_disarm > 1500:

            #Step One: Poll ------------------------------------------------------------------------------
            curr_time = time.time()
            taranis, buffer = SBUScheck(main_conn, buffer) # Polling SBUS

            if taranis[0]!= 1: # only update modes if the data was meaningful, all 1s means nothing good
                height_comm = taranis[0]
                roll_comm = taranis[1]
                pitch_comm = taranis[2]
                yaw_comm = taranis[3]
                fire = taranis[4] # don't even think about firing unless this is high #SG
                python_exit = taranis[5] # SE
                safety = taranis[6] #SD
                arm_disarm = taranis[7] #code never changes this, high means armed  #SC
                auto_mode = taranis[8] # deadmans switch, high means manual and low means auto #SH
                fail_safe = taranis[9] # if there are 10 of these, bad things
                frame_lost = taranis[11] # Just an indicator

            if mainzed_conn.poll(): # Poll Zed
                position = mainzed_conn.recv()
                time_updated += 1
            else:
                time_left += 1

            height = CheckLidar(sensor, height) # Poll Lidar

            shots = random.randint(1,5)

            #--------------------------------------------------------------------------------------------


            #Step Two:Process -----------------------------------------------------------------------------
            if frame_lost > 1500:
                framesLost += 1
            if fail_safe > 1500:
                failed_unsafely += 1
                if buffer[0][9] == 1800: # if every entry in the rolling buffer has a failsafe flag, its time to land
                    pass #what do we do if its too many failsafes now?
            
            if fire > 1500: #adjust for cooldown
                readyToShoot = True #indicator we want a commanded shot
            

            #This section will only update the commands if its automatic mode or there is no desync
            if auto_mode > 1500: # need to assign some values to the comm
                if not last_auto:
                    navi.setHoverThrottle(taranis[0])
                navi_start = time.time()
                height_comm, yaw_comm, roll_comm , pitch_comm = navi.tick(position[0], position[2], height, orbit= False )
                navi_end = time.time()
                readyToShoot = navi.readyToShoot()
                last_auto = True
                #if (-15 <= position[0] <= 15) and (80<= position[2] <= 120):
                    #readyToShoot = True
            
            else:
                last_auto = False



            #-----------------------------------------------------------------------------------------------



            #Step Three: Send----------------------------------------------------------------------------
            if readyToShoot and gun_ready: # shoot because close enough or because we want to 
                #grab current time
                curr_time = time.time()
                off_time = curr_time + run_time
                wait_ended = curr_time + cool_time + run_time
                time_shooting += 1
                
                gun_ready = False #Can't shoot again till its done shooting
                readyToShoot = False #reset random shot bit

                #shoot
                #x = 0
                kit.servo[2].angle  = 80
                # while x < 30:# ramp up, figure out how to make this longer
                    #kit.servo[0].angle = x
                    #kit.servo[1].angle = x
                    #x += 1
                kit.servo[0].angle = 50
                kit.servo[1].angle = 50
                

            #turn off motors and return servo once its been long enough
            if curr_time >= off_time: # off mode
                turn_off_gun(kit)
                if curr_time >= wait_ended:# only reset wait end time if we hit it - otherwise its a continuously moving goal post
                    gun_ready = True

            #Send package and send flight commands
            commands = [int(height_comm), int(roll_comm), int(pitch_comm), int(yaw_comm), taranis[4], taranis[5],taranis[6], taranis[7], taranis[8], taranis[9], 992, taranis[11], taranis[12], taranis[13], taranis[14], taranis[15]]
            main_conn.send(commands)


            #------------------------------------------------------------------------------------------------
        
        
        
        #------------------------------------------------------------------------------------
        #To let us leave the larger loop
        taranis, buffer = SBUScheck(main_conn, buffer) # Polling SBUS

        if taranis[0]!= 1: # only update modes if the data was meaningful, all 1s means nothing good
            height_comm = taranis[0]
            roll_comm = taranis[1]
            pitch_comm = taranis[2]
            yaw_comm = taranis[3]
            fire = taranis[4] # don't even think about firing unless this is high #SG
            python_exit = taranis[5] # SE
            safety = taranis[6] #SD
            arm_disarm = taranis[7] #code never changes this, high means armed  #SC
            auto_mode = taranis[8] # deadmans switch, high means manual and low means auto #SH
            fail_safe = taranis[9] # if there are 10 of these, bad things
            frame_lost = taranis[11] # Just an indicator
        if mainzed_conn.poll(): # Poll Zed
            position = mainzed_conn.recv()
        
        #Send package and send flight commands
        commands = [int(height_comm), int(roll_comm), int(pitch_comm), int(yaw_comm), taranis[4], taranis[5],taranis[6], taranis[7], taranis[8], taranis[9], 992, taranis[11], taranis[12], taranis[13], taranis[14], taranis[15]]
        main_conn.send(commands)    


        #---------------------------------------------------------------------------
    

except Exception as e:
    print("Fatal Errors:", e)

finally:

    end = time.time()
    #shut off everything
    try:
        if debug:
            print("time spent updating zed: ", time_updated)
            print("time zed left as it: ", time_left)
            print("time naviagting: ", navi_end - navi_start)
            print("Frames lost is ", framesLost)
            print("time spent being unsafe is ", failed_unsafely)
            print("Last channel pack was: ", taranis)
            print("Last position was: ", position)
            print("Last height reading was: ", height)
            print("Last command pack was: ", commands)
            print("Time shooting was: ", time_shooting)
            print("Buffer was: ", buffer)
    except Exception as e:
        print("something went wrong in the debug prints: ", e)
    finally:
        turn_off_gun(kit)


        #graceful exits
        mainzed_conn.send(True)

        commands = [0]*16
        main_conn.send(commands)

        while SBUS_script.is_alive():
            if main_conn.poll():
                garbo = main_conn.recv()
        if debug:
            print(F"sbus program closed")


        while object_find.is_alive():
            if mainzed_conn.poll():
                garbo = mainzed_conn.recv()
        if debug:
            print(F"ZED program closed")


        object_find.terminate()
        SBUS_script.terminate()
