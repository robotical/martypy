from .serialclient import SerialClient
from .socketclient import SocketClient
from .testclient import TestClient
from .exceptions import MartyConnectException, MartyConfigException

class Marty(object):

    CLIENT_TYPES = {
        'socket' : SocketClient,
        'serial' : SerialClient,
        'test'   : TestClient,
    }

    def __init__(self, url='socket://marty.local'):
        '''
        Initialise a Marty client class from a url

        Args:
            url: Describes where the Marty can be found and what protocol it's speaking

        Raises:
            MartyConnectException if the client couldn't be initialised
        '''

        proto, _, loc = url.partition('://')

        if not (proto and loc):
            raise MartyConfigException('Invalid URL format "{}" given'.format(url))

        if proto not in self.CLIENT_TYPES.keys():
            raise MartyConfigtException('Unrecognised URL protocol "{}"'.format(proto))

        # Initialise the client class used to communicate with Marty
        self.client = self.CLIENT_TYPES[proto](loc)



    def hello(self):
        '''
        Zero joints and wiggle eyebrows
        '''
        self.client.execute('hello')


    def stop(self, stop_type):
        '''
        Stop motions
        '''


    def move_joint(self):
        '''
        Move a specific joint to a position
        '''


    def lean(self, direction, amount, move_time):
        '''
        Lean over in a direction
        '''


    def walk(self, num_steps, turn, move_time, step_length):
        '''
        Walking macro
        '''


    def eyes(self, angle):
        '''
        Move the eyes to an angle
        '''


    def kick(self, side, move_time, twist):
        '''
        Kick with Marty's feet
        '''


    def arms(self, right_angle, left_angle, move_time):
        '''
        Move the arms to a position
        '''


    def lift_leg(self, leg, move_time):
        '''
        Lift a leg up
        '''


    def lower_leg(self, leg, move_time):
        '''
        Lower a leg down
        '''


    def celebrate(self, move_time):
        '''
        Do a small celebration
        '''


    def sidestep(self, side, steps, move_time, step_length):
        '''
        Take sidesteps
        '''


    def stand_straight(self, move_time):
        '''
        Return to the zero position for motors
        '''


    def play_sound(self, fre_start, freq_end, duration):
        '''
        Play a tone
        '''


    def get_battery_volatage(self):
        '''
        Returns:
            The battery voltage reading as a float

        Code:
            battery
        '''


    def get_accelerometer(self):
        '''
        Returns:
            The most recently read x, y and z accelerations
        '''


    def get_motor_current(self, motor_id):
        '''
        Returns:
            Instantaneous current sense reading from motor `motor_id`
        '''


    def digitalread_gpio(self, gpio):
        '''
        Returns:
            Returns High/Low state of a GPIO pin
        '''


    def enable_motors(self, enable):
        '''
        Toggle power to motors
        
        Command:
           enable_motors and disable_motors
        '''


    def _fall_protection(self, enable):
        '''
        Toggle fall protections
        '''


    def _motor_protection(self, enable):
        '''
        Toggle motor current protections
        '''


    def _battery_protection(self, enable):
        '''
        Toggle low battery protections
        '''


    def _save_calibration(self):
        '''
        Set the current motor positions as the zero positions
        '''
