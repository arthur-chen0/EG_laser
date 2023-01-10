#!/usr/bin/env python
# -*- coding: utf-8 -*-

import picamera
import time
import threading
from laser_2 import Laser, result_callback
from argparse import ArgumentParser
import datetime as dt

parser = ArgumentParser()
parser.add_argument("-p","--port", help="serial port path", required=True)

distance_d = 0
mutex = threading.Lock()

class result(result_callback):
    def on_distance(self, distance):
        global distance_d
        print('distance: ' + str(distance))
        mutex.acquire()
        distance_d = distance
        mutex.release()

    def on_error(self, error):
        print('error: ' + error)


if __name__ == '__main__':

    try:
        args = parser.parse_args()

        #init laser module
        laser = Laser(args.port)
        laser.callback = result()
        if laser.open():
            laser.auto_measurement()

        #init picamera
        camera = picamera.PiCamera()
        camera.resolution = (1024, 768)
        camera.rotation   = 180
        camera.crop       = (0.0, 0.0, 1.0, 1.0)

        # display preview
        camera.start_preview()
        camera.annotate_text_size = 120
        while True:
            mutex.acquire()
            camera.annotate_text = str(float(distance_d/10))
            mutex.release()
            time.sleep(0.5)
        
        

    except KeyboardInterrupt:
        print("stop auto mode")
        laser.stop_auto_mode()
        laser.is_running = False
        # laser.t._stop()
