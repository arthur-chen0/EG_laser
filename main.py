#!/usr/bin/env python
# -*- coding: utf-8 -*-

import picamera
import time
import threading
import RPi.GPIO as GPIO
from laser_2 import Laser, result_callback
from argparse import ArgumentParser
import datetime as dt

parser = ArgumentParser()
parser.add_argument("-p","--port", help="serial port path", required=True)

distance_d = 0
mutex = threading.Lock()
running = False
laser = None
camera = None

class result(result_callback):
    def on_distance(self, distance):
        global distance_d
        print('distance: ' + str(distance))
        mutex.acquire()
        distance_d = distance
        mutex.release()

    def on_error(self, error):
        print('error: ' + error)

def button_pressed_callback(channel):
    global laser, camera, running, distance_d
    if running:
        print("stop!")
        running = False
        distance_d = 0
        camera.stop_preview()
        laser.stop_auto_mode()
        laser.is_running = False
    else:
        print("start!")
        running = True
        if laser.open():
            laser.is_running = True
            laser.auto_measurement()
        camera.start_preview()


if __name__ == '__main__':

    try:
        args = parser.parse_args()

        #init laser module
        laser = Laser(args.port)
        laser.callback = result()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(16, GPIO.FALLING, callback=button_pressed_callback, bouncetime=300)

        #init picamera
        camera = picamera.PiCamera()
        camera.resolution = (1024, 768)
        camera.rotation   = 180
        camera.crop       = (0.0, 0.0, 1.0, 1.0)
        camera.annotate_text_size = 120
        while True:
            if running:
                mutex.acquire()
                camera.annotate_text = str(float(distance_d/10))
                mutex.release()
            time.sleep(0.5)
        

    except KeyboardInterrupt:
        print("stop auto mode")
        laser.stop_auto_mode()
        laser.is_running = False
        GPIO.cleanup()
        exit()
        # laser.t._stop()
