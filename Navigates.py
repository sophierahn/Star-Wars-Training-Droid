#docs: https://simple-pid.readthedocs.io/en/latest/
from simple_pid import PID
import math

class Navigate:
    #orbit radius in centimeters
    _radius = 200


    #still need to calculate
    _thrustP = 0
    _thrustI = 0
    _thrustD = 0

    hover = 100


    #still need to calculate
    _pitchP = 0
    _pitchI = 0
    _pitchD = 0

    #still need to calculate
    _yawP = 0
    _yawI = 0
    _yawD = 0

    #seconds
    _time = 0.01

    _pitch = PID(_pitchP, _pitchI, _pitchD, sample_time= 0.01, setpoint = _radius)
    _yaw = PID(_yawP, _yawI, _yawD, sample_time = 0.01, setpoint = 0)
    _thrust = PID(_thrustP, _thrustI, _thrustD, sample_time = 0.01, setpoint = hover)

    #units centimeters
    _allowedError = 10
    _allowedAngle = 5

    #orbit power either positive or negative from 1000 - 2000
    _orbitSpeed = 1050
    _atOrbit = False

    def __init__(self, pp, pi, pd, yp, yi, yd, tp, ti, td, radius = 200, time = 0.01, allowedError = 10, allowedAngle = 5, orbitSpeed = 1100, _hover = 100):
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

        self._time = time

        self._pitch.sample_time = time
        self._pitch.setpoint = radius

        self._yaw.sample_time = time
        self._yaw.setpoint = 0
        
        self._hover = _hover
        self._thrust.sample_time = time
        self._thrust.setpoint = _hover

        self._allowedError = allowedError
        self._allowedAngle = allowedAngle

        self._orbitSpeed = orbitSpeed

        self.neutral = 992
        self.hover_neutral = 992 # need to actually find this

    def changeRadius(self, radius = 0):
        if radius == 0:
            pass
    def setLoopTime(self, time):
        self._time = time
        self._pitch.sample_time = time
        self._yaw.sample_time = time
        self._thrust.sample_time = time

    def _getAngle(self, x, y):
        return (math.atan(x/y) * 180/math.pi)

    def tick(self, currX, currY, orbit = False):
        angle = self._getAngle(currX,currY)
        atAngle = False
        atRadius = False

        if (abs(angle) <= self._allowedAngle):
            atAngle = True

        if (abs(currY-self._radius) <= self._allowedError):
            atRadius = True

        yawCommand = self._yaw(angle) + 992
        pitchCommand = self._pitch(currY) + 992

        if (orbit and atRadius and atAngle):
            self._atOrbit = True

        if not orbit:
            self._atOrbit = False

        if orbit and not self._atOrbit:
            if atAngle:
                return self.neutral , pitchCommand, self.neutral 
            elif atAngle and atRadius:
                return self.neutral , self.neutral , self.neutral 
            else:
                return yawCommand, self.neutral , self.neutral 
        elif orbit and self._atOrbit:
            return yawCommand, pitchCommand, self._orbitSpeed

        if atAngle:
            return self.neutral , pitchCommand, self.neutral 
        elif atAngle and atRadius:
            return self.neutral , self.neutral , self.neutral 
        else:
            return yawCommand, self.neutral , self.neutral 

            #return order is established as yawcommand, pitchcommand, orbitSpeed
    
    def heightTick(self, currH):

        atHeight = False
        if currH == self._hover:
            atHeight = True
        
        thrustCommand = self._thrust(currH) + 992

        if atHeight:
            return self.hover_neutral
        else:
            return thrustCommand
