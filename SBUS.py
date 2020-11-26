#tons of credit to carbon225 on github, the code is heavily based on theirs and they helped me understand it better
#www.os.mbed.com/users/Digixx/notebook/futaba-s-bus-controlled-by-mbed/
import fcntl, array, struct, termios, time, os
import math 
import numpy
import serial 
import bitstring
import sys


class SBUS:
    #Here I define all those lovely lil untouchable variables
    _SBUS_PACKET_SIZE = 25
    _SBUS_DESYNC_END = 2
    _SBUS_DESYNC_HDR = 1
    _READ_BUF_SIZE = _SBUS_PACKET_SIZE * 2
    _SBUS_HEADER = 0b00001111
    _SBUS_END = 0b00000000
    _nextRead = _READ_BUF_SIZE
    SBUS_OPT_C17 = 0b0001
    SBUS_OPT_C18 = 0b0010
    SBUS_OPT_FL = 0b0100
    SBUS_OPT_FS = 0b1000
    _packet = bytearray(_SBUS_PACKET_SIZE)
    readBuf = bytearray(_READ_BUF_SIZE)
    _NUM_CHANNELS = 16
    INSTALL_ERROR = False
    SBUS_OK = True
    desync = False
    time_to_land = False



    def __init__(self, _SBUS_PACKET_SIZE = 25,_SBUS_DESYNC_END = 2,_SBUS_DESYNC_HDR = 1,_SBUS_HEADER = 0b00001111,_SBUS_END = 0b00000000,_nextRead = 50,SBUS_OPT_C17 = 0b0001,SBUS_OPT_C18 = 0b0010,SBUS_OPT_FL = 0b0100,SBUS_OPT_FS = 0b1000, _NUM_CHANNELS = 16, INSTALL_ERROR = False):
        self._SBUS_PACKET_SIZE = 25
        self._SBUS_DESYNC_END = 2
        self._SBUS_DESYNC_HDR = 1
        self._READ_BUF_SIZE = _SBUS_PACKET_SIZE * 2
        self._SBUS_HEADER = _SBUS_HEADER
        self._SBUS_END = _SBUS_END
        self._nextRead = _nextRead
        self.SBUS_OPT_C17 = SBUS_OPT_C17
        self.SBUS_OPT_C18 = SBUS_OPT_C18
        self.SBUS_OPT_FL = SBUS_OPT_FL
        self.SBUS_OPT_FS = SBUS_OPT_FS
        self._NUM_CHANNELS = 16
        self.INSTALL_ERROR = INSTALL_ERROR
        self.SBUS_OK = True
        self.desync = False
        self._packet = bytearray(_SBUS_PACKET_SIZE)
        self.packet_in = [[0]*16,0,0,0,0]
        self.ch17 = False
        self.ch18 = False
        self.failSafe = False
        self.frameLost = False
        self.time_to_land = False
        self.strange_packet = bytearray(_SBUS_PACKET_SIZE)
        self.num_strange_packets = 0


    def install(self): # set up the serial port, the object holds the access to the buffer i think
        #setting timeout controls blocking vs nonblocking, timeout = 0 sets to nonblocking mode
        #timeout of none waits forever/ until requested number of bytes are recieved which I THINK is what we want
        
        try:
            uart = serial.Serial("/dev/ttyUSB0", baudrate=100000, bytesize=serial.EIGHTBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO)
            self.INSTALL_ERROR = False
            return uart
        #errors include Value error when param out of range and Serial Exception when device cannot be found
        except serial.SerialException:
            self.INSTALL_ERROR = True

        
    def close(self, uart):   
        uart.close()

    def read(self, uart):
        
        start_found = False
        x = 0


        while x < 50:
            self.desync = False
            
            in_byte = uart.read(1)# this is taking the majority of the processing time

            self.SBUS_OK = True

            if in_byte[0] == self._SBUS_HEADER and not start_found:
                start_found = True
                self._packet[0] = in_byte[0]
                _packetPos = 1

            #specifically elif so it doesn't copy in the start bit twice    
            elif start_found:

                #start reading bytes into the _packet starting after the start byte
                self._packet[_packetPos] = in_byte[0]
                _packetPos += 1 

                #if we've filled a full sbus _packet
                if _packetPos >= self._SBUS_PACKET_SIZE:


                    #check if its a valid packet
                    if self.verifyPacket():
                        #give decodePacket a bytearray and return a list of channels and the bools
                        channels_in, opt_in = self.decodePacket()
                        #Mostly for beugging to catch the instances where the packets are still garbled at this point
                        if channels_in[10] != 992:
                            self.strange_packet = self._packet
                            self.num_strange_packets += 1

                        if self.failSafe:
                            self.time_to_land = True

                        return channels_in, opt_in
                    else:
            
                        self.desync = True

                        #mostly garbage data to indicate desync
                        channels_in = [1,1,1,1,1800,1,1,1,1,1,1,1800,1,1,1,1]
                        opt_in = 0b00100100 #ensure frame lost bit is set, could be position 2 or 6 depending on endian
                        return channels_in, opt_in
        #for loop incrementing            
            x += 1
                        
            



    #takes in properly formatted packet list as well as serial port object
    #writes said packet to the serial port
    def write(self, packet, uart):

        
        opt_out = 0
        #take the packet tuple apart
        channels_out = packet[0]

        opt_out |= packet[1] * self.SBUS_OPT_C17 
        opt_out |= packet[2] * self.SBUS_OPT_C18
        opt_out |= packet[3] * self.SBUS_OPT_FS
        opt_out |= packet[4] * self.SBUS_OPT_FL

        output = self.encode(channels_out, opt_out)

        uart.write(output)

        


    

    #used to verify that an incoming packet from Taranis has proper start and end bits, otherwise the data must be corrupted
    #returns if the packet can be trusted or not
    def verifyPacket(self):
        if self._packet[0] == self._SBUS_HEADER and self._packet[self._SBUS_PACKET_SIZE - 1] == self._SBUS_END:
            return True
        else:
            return False
    

    #will take in a list of commands and put the in the byte array
    #this function will vary as I adjust the PID library
    #will output bytearray of channels
    def fillChannels(self, commands):
        channels = bytearray(commands)
        return channels

    
    #A function to build a packet list and undergo some error checking
    #maybe try ditching this function?
    def buildPacket(self, channels_out, ch17, ch18, failsafe, frameLost):

        #load up packet list
        packet = channels_out, ch17, ch18, failsafe, frameLost
        msg0 = ""
        msg1 = ""
        msg2 = ""
        msg3 = ""
        msg4 = ""
        error = False

        #verify data types
        if not isinstance(packet[0], list):
            print(F"channels out is not a list")
            error = True

        if not isinstance(packet[1], bool):
            print(F"ch17 is not a bool")
            error = True

        if not isinstance(packet[2], bool):
            print(F"ch18 is not a bool")
            error = True
        
        if not isinstance(packet[3], bool):
            print(F"failsafe is not a bool")
            error = True

        if not isinstance(packet[4], bool):
            print(F"frameLost is not a bool")
            error = True
        else:
            return packet
        


    
    #Takes in channels list  and outputs a _packet bytearray
    def encode(self, channels_out, opt_out):

        #init stuff like packet array
        packet = bytearray(self._SBUS_PACKET_SIZE)

        #---------------------------

        if not packet or not channels_out:
            print(F"something went wrong but frankly im not sure what")

        #---------------------------

        #set start and end bits
        packet[0] = self._SBUS_HEADER
        packet[24] = self._SBUS_END

        #kick off packet loading alogrithm
        packet[1] = channels_out[0] & 0xFF
        packet[2] = channels_out[0] >> 8 & 0b111
        current_byte = 2
        usedBits = 3 # from LSB

        #to fill 16 channels
        for ch in range(1,16):
            #while channel not fully encoded
            bitsWritten = 0
            while bitsWritten < 11:

                #strip written bits, shift over used bits
                packet[current_byte] |= channels_out[ch] >> bitsWritten << usedBits & 0xff
                
                hadToWrite = 11 - bitsWritten
                couldWrite = 8 - usedBits

                wrote = couldWrite
                if hadToWrite < couldWrite:
                    wrote = hadToWrite
                else:
                    current_byte += 1

                bitsWritten += wrote
                usedBits += wrote
                usedBits %= 8
            #increment ch to get through channel encoding
            ch += 1
        
        #set error flags
        packet[23] = opt_out

        return packet







    

    #take in _packet and output channels list and opt
    #handles bit shifting and endian switch outlined for futuba SBUS
    def decodePacket(self):
        channels_in = [0]*self._NUM_CHANNELS


        channels_in[0] = (self._packet[1] | (self._packet[2] << 8)  & 0x07FF)
        channels_in[1] = ((self._packet[2] >> 3) | (self._packet[3] << 5) & 0x07FF)
        channels_in[2] = ((self._packet[3] >> 6) | (self._packet[4] << 2) | (self._packet[5] << 10) & 0x07FF)
        channels_in[3] = ((self._packet[5] >> 1) | (self._packet[6] << 7) & 0x07FF)
        channels_in[4] = ((self._packet[6] >> 4) | (self._packet[7] << 4) & 0x07FF)
        channels_in[5] = ((self._packet[7] >> 7) | (self._packet[8] << 1) | (self._packet[9] << 9) & 0x07FF)
        channels_in[6] = ((self._packet[9] >> 2) | (self._packet[10] << 6) & 0x07FF)
        channels_in[7] = ((self._packet[10] >> 5) | (self._packet[11] << 3) & 0x07FF)
        channels_in[8] = (self._packet[12]  | (self._packet[13] << 8) & 0x07FF)
        channels_in[9] = ((self._packet[13] >> 3) | (self._packet[14] << 5) & 0x07FF)
        channels_in[10] = ((self._packet[14] >> 6) | (self._packet[15] << 2) | (self._packet[16] << 10) & 0x07FF)
        channels_in[11] = ((self._packet[16] >> 1) | (self._packet[17] << 7) & 0x07FF)
        channels_in[12] = ((self._packet[17] >> 4) | (self._packet[18] << 4) & 0x07FF)
        channels_in[13] = ((self._packet[18] >> 7) | (self._packet[19] << 1) | (self._packet[20] << 9) & 0x07FF)
        channels_in[14] = ((self._packet[20] >> 2) | (self._packet[21] << 6) & 0x07FF)
        channels_in[15] = ((self._packet[21] >> 5) | (self._packet[22] << 3) & 0x07FF)

        opt = self._packet[23] & 0xF


        #create input packet list for passthrough situations
        #there will ALWAYS be a packet in and there will ALWAYS only be one (bc when new info comes in it gets updated)
        #so this will make it easily accessible for passthrough scenarios
        self.ch17 = bool(opt & self.SBUS_OPT_C17)
        self.ch18 = bool(opt & self.SBUS_OPT_C18)
        self.failSafe = bool(opt & self.SBUS_OPT_FS)
        self.frameLost = bool(opt & self.SBUS_OPT_FL)

        self.packet_in = channels_in, self.ch17, self.ch18, self.failSafe, self.frameLost
        #dont need to worry about _packet[24] cause thats the end bit (0X00)

        return channels_in, opt



