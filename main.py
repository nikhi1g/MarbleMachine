# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port=0, speed=INIT_RAMP_SPEED)


# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    gate = ObjectProperty(None)
    auto = ObjectProperty(None)
    ramp = ObjectProperty(None)
    staircase = ObjectProperty(None)
    rampSpeed = ObjectProperty(None)
    staircaseSpeed = ObjectProperty(None)
    title = ObjectProperty(None)
    rampSpeedLabel = ObjectProperty(None)
    staircaseSpeedLabel = ObjectProperty(None)
    anticrash = ObjectProperty(None)

    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    speedramp = 0
    staircaseSpeed = 40

    cyprus.initialize()

    cyprus.setup_servo(2)

    s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
                 steps_per_unit=200, speed=8)

    cyprus.set_servo_position(2, 0)

    cyprus.set_pwm_values(1, period_value=100000, compare_value=50000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
    sleep(6)
    cyprus.set_pwm_values(1, period_value=80000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)

    s0.go_until_press(0, 20000)
    while s0.isBusy():
        sleep(0.5)

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def busymotor(self):
        while self.s0.isBusy():
            sleep(0.4)

    def toggleGate(self):
        if self.gate.text == 'Open Gate':  # & self.ramp.text == "Press for Ramp":
            cyprus.set_servo_position(2, 0.5)
            print("gate closed")
            self.gate.text = 'Close Gate'
        elif self.gate.text == 'Close Gate':
            cyprus.set_servo_position(2, 0)
            print("gate open")
            self.gate.text = 'Open Gate'

    def toggleStaircase(self):
        if self.staircase.text == 'Staircase On':
            cyprus.set_pwm_values(1, period_value=25000, compare_value=50000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.staircase.text = 'Staircase Off'
        elif self.staircase.text == 'Staircase Off':
            cyprus.set_pwm_values(1, period_value=80000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.staircase.text = 'Staircase On'



    def toggleRamp(self):

        if self.ramp.text == "Press for Ramp":
            self.s0.setMaxSpeed(500)
            self.ramp.text = "Ramping"
            self.s0.relative_move(28.5)
            self.busymotor()
            self.s0.go_until_press(0, 100000)
            self.ramp.text = "Ramping"
            self.ramp.text = "Press for Ramp"


    def command(self):
        self.s0.softStop()
        refresher = threading.Thread(target=self.toggleRamp)  # thread call to toggleRamp()
        refresher.start()

    def automatic(self):
        print('auto 1 run has started')
        self.toggleGate()
        sleep(0.15)
        self.toggleGate()
        sleep(1)
        self.toggleRamp()
        self.busymotor()
        self.toggleStaircase()
        sleep(6)
        self.toggleStaircase()

    def threadautomatic(self):
        self.s0.softStop()
        refresher1 = threading.Thread(target=self.automatic)  # thread call to toggleRamp()
        refresher1.start()



    def setRampSpeed(self):
        print(self.rampSpeed.value)
        self.speedramp = self.rampSpeed.value

    def setStaircaseSpeed(self, speed):
        print("Set the staircase speed and update slider text")

    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def anticrash(self):
        cyprus.initialize()
        self.s0.go_until_press(0, 40000)

    def quit(self):
        print("Exit")
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
