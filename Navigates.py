#docs: https://simple-pid.readthedocs.io/en/latest/
#Written by Benjamin Macdonell
from simple_pid import PID
import math
import random
import time

class Navigate:
    #orbit radius in centimeters
    _radius = 200

    #still need to calculate
    _thrustP = 0
    _thrustI = 0
    _thrustD = 0

    _hover = 100

    #still need to calculate
    _pitchP = 0
    _pitchI = 0
    _pitchD = 0

    #still need to calculate
    _yawP = 0
    _yawI = 0
    _yawD = 0
    
    #still need to calculate
    _rollP = 0
    _rollI = 0
    _rollD = 0

    #seconds
    _time = 0.01

    _roll = PID(_rollP, _rollI, _rollD, sample_time= 0.01, setpoint = 0)
    _pitch = PID(_pitchP, _pitchI, _pitchD, sample_time= 0.01, setpoint = _radius)
    _yaw = PID(_yawP, _yawI, _yawD, sample_time = 0.01, setpoint = 0)
    _thrust = PID(_thrustP, _thrustI, _thrustD, sample_time = 0.01, setpoint = _hover)

    #units centimeters
    _allowedError = 10

    #orbit power either positive or negative from 1000 - 2000
    _orbitSpeed = 1050
    _atOrbit = False
    _maxVal = 1811
    _minVal = 173
    _centerVal = 992

    _minSaneVal = 1000
    _maxSaneVal = 2000
    _midSaneVal = (_minSaneVal + _maxSaneVal) / 2

    _rotateClock = True

    _hoverThrottle = 1100

    _readyToShoot = False

    def __init__(self, pp, pi, pd, yp, yi, yd, tp, ti, td, rp, ri, rd, radius = 200, time = 0.01, allowedError = 30, orbitSpeed = 1100, hover = 100, hoverThrottle = 1200):
        self._radius = radius

        self._pitchP = pp
        self._pitchI = pi
        self._pitchD = pd

        self._pitch.tunings = (pp,pi,pd)

        self._yawP = yp
        self._yawI = yi
        self._yawD = yd

        self._yaw.tunings = (yp,yi,yd)

        self._thrustP = tp
        self._thrustI = ti
        self._thrustD = td

        self._thrust.tunings = (tp,ti,td)

        self._rollP = rp
        self._rollI = ri
        self._rollD = rd

        self._roll.tunings = (rp,ri,rd)

        self._time = time

        self._pitch.sample_time = time
        self._pitch.setpoint = radius

        self._yaw.sample_time = time
        self._yaw.setpoint = 0

        self._roll.sample_time = time
        self._roll.setpoint = 0
        
        self._hover = hover
        self._thrust.sample_time = time
        self._thrust.setpoint = hover

        self._hoverThrottle = hoverThrottle

        self._allowedError = allowedError

        self._orbitSpeed = orbitSpeed

    def changeRadius(self, radius = 100):
        self._radius = radius
        self._pitch.setpoint = radius

    def setOrbitSpeed(self, speed = 1100):
        self._orbitSpeed = speed

    def setLoopTime(self, time):
        self._time = time
        self._pitch.sample_time = time
        self._yaw.sample_time = time
        self._thrust.sample_time = time

    def _getAngle(self, x, y):
        return (math.atan(x/y) * 180/math.pi)

    def _map(self, val):
        return (val - self._minSaneVal) * (self._maxVal - self._minVal) / (self._maxSaneVal - self._minSaneVal) + self._minVal

    def _unMap(self, val):
        return (val - self._minVal) * (self._maxSaneVal - self._minSaneVal) / (self._maxVal - self._minVal) + self._minSaneVal
    
    def setDirection(self, dir):
        self._rotateClock = dir

    def setHoverThrottle(self, throttle):
        self._hoverThrottle = self._unMap(throttle)
        print(self._hoverThrottle)

    def setHoverHeight(self, height):
        self._hover = height    
        self._thrust.setpoint = height

    def readyToShoot(self):
        return self._readyToShoot

    def tick(self, currX, currY, currH, orbit = False):
        self.Fire = False
        atX = False
        atY = False
        atHeight = False

        if (abs(currH - self._hover) <= self._allowedError):
            atHeight = True
        else:
            atHeight = False

        if (abs(currX) <= self._allowedError):
            atX = True
        else:
            atX = False

        if (abs(currY-self._radius) <= self._allowedError):
            atY = True
        else:
            atY = False

        shouldOrbit = atY and atX #and atHeight

        if orbit and shouldOrbit:
            if self._rotateClock:
                yawCommand = self._midSaneVal - self._orbitSpeed
            else:
                yawCommand = self._midSaneVal + self._orbitSpeed
            pitchCommand = self._pitch(currY) + self._midSaneVal
            rollCommand = self._roll(currX) + self._midSaneVal
            thrustCommand = self._thrust(currH) + self._hoverThrottle

        else:
            yawCommand = self._midSaneVal
            pitchCommand = self._pitch(currY) + self._midSaneVal
            rollCommand = self._roll(currX) + self._midSaneVal
            thrustCommand = self._thrust(currH) + self._hoverThrottle

        self._readyToShoot = shouldOrbit

        if yawCommand < 1000:
            yawCommand = 1000
        elif yawCommand  > 2000:
            yawCommand = 2000

        if pitchCommand < 1000:
            pitchCommand = 1000
        elif pitchCommand  > 2000:
            pitchCommand = 2000

        if rollCommand < 1000:
            rollCommand = 1000
        elif rollCommand  > 2000:
            rollCommand = 2000

        if thrustCommand < 1000:
            thrustCommand = 1000
        elif thrustCommand  > 2000:
            thrustCommand = 2000
        
        return self._map(thrustCommand), self._map(yawCommand), self._map(rollCommand), self._map(pitchCommand)


    '''
        yawCommand = self._yaw(angle) + self.neutral
        pitchCommand = self._pitch(currY) + self.neutral
        rollCommand = self._roll(currX) + self.neutral



        if (orbit and atRadius and atAngle):
            self._atOrbit = True

        if not orbit:
            self._atOrbit = False

        if orbit and not self._atOrbit: # if we want to orbit but arent there
            if atAngle:
                return self.neutral , pitchCommand, self.neutral 
            elif atAngle and atRadius:
                self.Fire = True
                return self.neutral , self.neutral , self.neutral 
            else:
                return yawCommand, pitchCommand , rollCommand
        elif orbit and self._atOrbit: # if we want to orbit and are there
            self.Fire = True # orbit and also fire

            self.cur_time = time.time()

            if self.cur_time >= (self.interval + self.last_switch):
                self.last_switch = self.cur_time
                self._orbitSpeed = self._orbitSpeed * rand_roll # this adds the randomization element

            return yawCommand, self.neutral, self._orbitSpeed # if orbiting, yaw compensates for drift on its own

        if atAngle:
            return self.neutral, pitchCommand, self.neutral 
        elif atAngle and atRadius: # if at target but not orbiting, fire
            self.Fire = True
            return self.neutral , self.neutral , self.neutral 
        else:
            return yawCommand, pitchCommand , rollCommand

            #return order is established as yawcommand, pitchcommand, rollcommand
    '''  
    '''  
    def heightTick(self, currH):

        atHeight = False
        if currH == self._hover:
            atHeight = True
        
        thrustCommand = self._thrust(currH) + self.hover_neutral #this will change alot depending on waht we find the nuetral hover level to be

        if atHeight:
            return self.hover_neutral
        else:
            return thrustCommand
    '''
