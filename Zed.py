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
def zedmain(zed_conn):

    # Create a Camera object
    zed = sl.Camera()
    

    # Create a InitParameters object and set configuration parameters
    init_params = sl.InitParameters()
    #consider turning down resolution
    init_params.camera_resolution = sl.RESOLUTION.HD720  # Use HD720 video mode
    init_params.depth_mode = sl.DEPTH_MODE.PERFORMANCE
    init_params.coordinate_units = sl.UNIT.METER
    init_params.sdk_verbose = True

    # Open the camera
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        exit(1)

    obj_param = sl.ObjectDetectionParameters()
    obj_param.enable_tracking=True
    obj_param.image_sync=True
    obj_param.enable_mask_output=True


    mat = sl.Mat()
    #camera_infos = zed.get_camera_information()
    if obj_param.enable_tracking :
        positional_tracking_param = sl.PositionalTrackingParameters()
        #positional_tracking_param.set_as_static = True
        positional_tracking_param.set_floor_as_origin = True
        zed.enable_positional_tracking(positional_tracking_param)

    #print("Object Detection: Loading Module...")

    err = zed.enable_object_detection(obj_param)
    if err != sl.ERROR_CODE.SUCCESS :
        print (repr(err))
        zed.close()
        exit(1)

    objects = sl.Objects()
    obj_runtime_param = sl.ObjectDetectionRuntimeParameters()
    obj_runtime_param.detection_confidence_threshold = 40

    shut_off = False
    #closed = False

    while zed.grab() == sl.ERROR_CODE.SUCCESS and not shut_off:
        #time.sleep(0.0001)
        if zed_conn.poll():
            shut_off = zed_conn.recv()
        err = zed.retrieve_objects(objects, obj_runtime_param)
        zed.retrieve_image(mat, sl.VIEW.LEFT)
        if objects.is_new :
            obj_array = objects.object_list
            #image_data = mat.get_data()
           # print(str(len(obj_array))+" Object(s) detected\n")
            if len(obj_array) > 0 :
                first_object = obj_array[0]


                #bounding_box = first_object.bounding_box_2d
                #cv2.rectangle(image_data, (int(bounding_box[0,0]),int(bounding_box[0,1])),
                            #(int(bounding_box[2,0]),int(bounding_box[2,1])),
                              #get_color_id_gr(int(first_object.id)), 3)



                #print("First object attributes:")
               # print(" Label '"+repr(first_object.label)+"' (conf. "+str(int(first_object.confidence))+"/100)")
                #if obj_param.enable_tracking :
                    #print(" Tracking ID: "+str(int(first_object.id))+" tracking state: "+repr(first_object.tracking_state)+" / "+repr(first_object.action_state))
                position = first_object.position
                #print(position)
                p_list = position.tolist()
                
                list_in_cm = [p_list[0]*100, p_list[1]*100, p_list[2]*100]
                old_list = list_in_cm
                
                #to catch the NAN which is apparently a float? idk its a real bother
                #if isinstance(list_in_cm[0], float):
                   # list_in_cm = old_list

                zed_conn.send(list_in_cm)
        #cv2.imshow("ZED", image_data)


                
    #cv2.destroyAllWindows()

    # Close the camera
    zed.close()




#zedmain()
