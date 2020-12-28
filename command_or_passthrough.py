from SBUS import SBUS
import sys
import serial
import time
from multiprocessing import Pipe


def SBUSmain(sbus_conn):
    taranis = SBUS()
    failed_install = 0
    commands = [172,992,992,992,992,992,992,992,992,992,992, 992, 992, 992, 992,992] # a bunch of neutral commands
    frameslost = 0
    failsafes = 0
    shut_down = False
    #auto_mode = 992
    debug = True
    in_comm = commands

    #part of an error check 
    while not shut_down:
        uart = taranis.install()

        if not taranis.INSTALL_ERROR:

            #While all is going well
            while taranis.SBUS_OK and not shut_down:

                taranis.read(uart)

                if taranis.desync:
                    uart.reset_input_buffer()

                while sbus_conn.poll():
                   in_comm = sbus_conn.recv()
                


                output = taranis.buildPacket(in_comm, False, False, False, False)
                taranis.write(output,uart)
                #--------------------------------------------------------------------
                

                #set flags-----------
                if taranis.failSafe:
                    #setting the land indicator to high
                    taranis.channels_in[9] = 1800 
                    failsafes += 1
                        
                if taranis.frameLost:
                    #indicator to the main script that a frame was lost
                    taranis.channels_in[11] = 1800
                    frameslost += 1
                
                if in_comm[0] == 0:
                    shut_down = True
                    break      
                    
                #Send out
                sbus_conn.send(taranis.channels_in) #Consider moving

                output = taranis.buildPacket(in_comm, False, False, False, False)
                taranis.write(output,uart)
        else:
            failed_install += 1
            print("SBUS install error")
            sbus_conn.send(taranis.INSTALL_ERROR)
            shut_down = True
    sbus_conn.close()
    uart.close()
    if debug:
        print("Strange packet: ", taranis.strange_packet)
        print("frames lost: ", frameslost)
        print("Failsafes : ", failsafes)
        print("Fail saf packet was: ", taranis.failed_packet)
        print("Frame lost packet was: ", taranis.lost_packet )


    sys.exit("End of program, shutting down")       

                
'''
                #this allows for commands to be recieved and sent IF we are in auto_mode and even if there is a desync
                if not taranis.desync or auto_mode > 1500: # I cant let it just reloop if theres a desync error, its too slow
                    #only update and send things out if theres no desync or it's auto_mode
                    auto_mode = taranis.channels_in[8] 
                    
                    if auto_mode > 1500: # I have to ask twice to differentiate between modes
                        commands = in_comm # use commands, old or new, to carry on

                    else: # if manual mode, commands is equal to channels in
                        commands = taranis.channels_in

                            
                    #Main loop shut off signal
                    if in_comm[0] == 0:
                            shut_down = True
                            break      
                    
                   # if debug:
                        #if taranis.channels_in[5] < 1500:
                            #shut_down = True
                            #break

                    #Create output packet - either commands or deconstructed incoming packet
                    #output = taranis.buildPacket(commands, False, False, False, False)

                elif taranis.desync:# if desync and not auto mode, resend the last good packet, because packet_in wont have reset
                    output = taranis.packet_in
                    uart.reset_input_buffer()


                #write out whatever was given in any mode or condition
                taranis.write(output,uart)
'''          
        

