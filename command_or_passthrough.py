from SBUS import SBUS
import sys
import serial
import time
from multiprocessing import Pipe


#add sbus_conn
def SBUSmain(sbus_conn):
    taranis = SBUS()
    failed_install = 0
    commands = [1]*16
    frameslost = 0
    shut_down = False
    channels = [1]*16
    last_channels = [0]*16
    auto_mode = 992
    debug = False

    #part of an error check 
    while not shut_down:

        uart = taranis.install()

        if not taranis.INSTALL_ERROR:

            #While all is going well
            while taranis.SBUS_OK and not shut_down:

                channels, opt = taranis.read(uart)


                if opt != 0x00:
                    if taranis.time_to_land:
                        #setting the land indicator to high so that the main script will begin to land
                        channels[7] = 1800
                        
                    if taranis.frameLost:
                        #indicator to the main script that a frame was lost
                        channels[11] = 1800
                        frameslost += 1
                

                #this allows for commands to be recieved and sent IF we are in auto_mode and even if there is a desync
                if not taranis.desync or auto_mode > 1500: 
                    #only update and send things out if theres no desync or it's auto_mode
                    auto_mode = channels[6]
                        
                    #not sure if i should implement these
                    #If a frame is lost, should the flight controller know?
                    failSafe = taranis.failSafe
                    frameLost = taranis.frameLost

                    sbus_conn.send(channels)
                        
                    #only accept new commands if theyre present
                    if sbus_conn.poll():

                        commands = sbus_conn.recv()

                    else:
                        commands = channels
                        
                    #i can't think of a scenario where throttle would be zero so this will be the shut off signal
                    if commands[0] == 0:
                        shut_down = True
                        break
                    if debug:
                        if channels[4] < 1500:
                            shut_down = True
                    if commands[10] == 992:        
                        #write the commands to the FC, whatever they may be
                        output = taranis.buildPacket(commands, False, False, False, False)
                        taranis.write(output,uart)
                    else:
                        output = taranis.buildPacket(last_channels, False, False, False, False)
                        taranis.write(output, uart)
                    last_channels = channels

                elif taranis.desync:
                    #if there was desync, read will return 1s and that will be passed through, indicating desync
                    sbus_conn.send(channels)
                    print("Desync Error")
                    uart.reset_input_buffer()

                    #send last packet if there was as desync issue
                    taranis.write(taranis.packet_in,uart)       
            uart.close()
        else:
            failed_install += 1
            print("SBUS install error")
            sbus_conn.send(taranis.INSTALL_ERROR)
            shut_down = True
    sbus_conn.close()
    if debug:
        print("Strange packet: ", taranis.strange_packet)
        print("frames lost: ", frameslost)


    sys.exit("End of program, shutting down")



#SBUSmain()
