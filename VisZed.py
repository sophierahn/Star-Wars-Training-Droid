#######################################################################
#
# Copyright (c) 2020, STEREOLABS.
#
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################

import pyzed.sl as sl
import cv2
import numpy as np
from multiprocessing import Pipe
import time
import math

def get_color_id_gr(idx):
    id_colors = [(59, 232, 176),
             (25,175,208),
             (105,102,205),
             (255,185,0),
             (252,99,107)]




    color_idx = idx % 5
    arr = id_colors[color_idx]
    return arr





#add zed_conn
def Viszedmain(zed_conn):
    visualize = True

    # Create a Camera object
    zed = sl.Camera()
    

    # Create a InitParameters object and set configuration parameters
    init_params = sl.InitParameters()
    #consider turning down resolution
    init_params.camera_resolution = sl.RESOLUTION.HD720  # Use HD720 video mode
    init_params.coordinate_units = sl.UNIT.METER
    init_params.sdk_verbose = True
    init_params.camera_fps = 15  # Set fps at 15

    # Open the camera
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        exit(1)


    mat = sl.Mat()
    runtime_parameters = sl.RuntimeParameters()

    obj_param = sl.ObjectDetectionParameters()
    obj_param.enable_tracking=True
    obj_param.image_sync=True

    if obj_param.enable_tracking :
        positional_tracking_param = sl.PositionalTrackingParameters()
        positional_tracking_param.set_floor_as_origin = True
        zed.enable_positional_tracking(positional_tracking_param)

    err = zed.enable_object_detection(obj_param)
    if err != sl.ERROR_CODE.SUCCESS :
        print (repr(err))
        zed.close()
        exit(1)

    objects = sl.Objects()
    obj_runtime_param = sl.ObjectDetectionRuntimeParameters()
    obj_runtime_param.detection_confidence_threshold = 40

    shut_off = False
    target_found = False
    p_list = [0,0,1]
    # position = [right to left, up and down, forward backward]


    while zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS and not shut_off:
        if zed_conn.poll():
            shut_off = zed_conn.recv()
        zed.retrieve_image(mat, sl.VIEW.LEFT)
        image_data = mat.get_data()
        if zed.retrieve_objects(objects, obj_runtime_param) == sl.ERROR_CODE.SUCCESS:
            if objects.is_new:
                obj_array = objects.object_list
                length = len(obj_array)
                if length > 0: # if there are people, start sifting through them
                    if target_found:# if we have a target locked in, start searching for them
                        x = 0
                        while x < length:  
                            person = obj_array[x]
                            x += 1
                            personID = person.id
                            if personID == targetID:
                                position = person.position
                                p_list = position.tolist() # send a sanitized list
                                target_found = True
                                break
                            else:
                                target_found = False # if we go through all the objects, and there are no targets, indicate this
                    #if we make it through the above loop, we want to be able to choose a new person that same loop            
                    if not target_found: # if there are objects but none of them match your target (or we simply never had a target), find a new one
                        person = obj_array[0] # pick the closest thing as your target
                        targetID = person.id
                        position = person.position
                        p_list = position.tolist()# send a sanitized list
                        target_found = True

                else:# if there are no objects, pan and restart target search
                    p_list = [-0.25, 0, 1]
                    target_found = False
    #------------------------------------------------------------------------------------------------------
    #visualization stuff

                if target_found:
                    bounding_box = person.bounding_box_2d
                    cv2.rectangle(image_data, (int(bounding_box[0,0]),int(bounding_box[0,1])),
                        (int(bounding_box[2,0]),int(bounding_box[2,1])),
                        get_color_id_gr(int(person.id)), 3)
    #-------------------------------------------------------------------------------------------
                if not math.isnan(p_list[0]):
                    list_in_cm = [p_list[0]*100, p_list[1]*100, p_list[2]*100]
                    zed_conn.send(list_in_cm)

#-------------------------------------------------------------------------------------------------------
#Visualization stuff
                x = round(p_list[0], 4)
                y = round(p_list[2], 4)
                if -0.5 <= x <= 0.5 and 2<= y <= 3:
                    cv2.putText(image_data,'FIRE!!!!', (30,100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        
                cv2.putText(image_data,str(x) + ' , ' + str(y), (30,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
                cv2.imshow("ZED", image_data)
                key = cv2.waitKey(1)

    cv2.destroyAllWindows()
#-------------------------------------------------------------------------------------------------------


    # Close the camera
    zed.close()
