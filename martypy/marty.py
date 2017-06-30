import struct
from .utils import dict_merge
from .serialclient import SerialClient
from .socketclient import SocketClient
from .testclient import TestClient
from .exceptions import MartyCommandException, MartyConnectException, MartyConfigException


class Marty(object):
    '''
    High-level client library for Marty the Robot by Robotical Ltd
    '''

    CLIENT_TYPES = {
        'socket' : SocketClient,
        'serial' : SerialClient,
        'test'   : TestClient,
    }

    def __init__(self, url='socket://marty.local', client_types=dict(), *args, **kwargs):
        '''
        Initialise a Marty client class from a url

        Args:
            url: Describes where the Marty can be found and what protocol it's speaking

        Raises:
            MartyConnectException if the client couldn't be initialised
        '''

        proto, _, loc = url.partition('://')

        self.CLIENT_TYPES = dict_merge(self.CLIENT_TYPES, client_types)
        
        if not (proto and loc):
            raise MartyConfigException('Invalid URL format "{}" given'.format(url))

        if proto not in self.CLIENT_TYPES.keys():
            raise MartyConfigtException('Unrecognised URL protocol "{}"'.format(proto))

        # Initialise the client class used to communicate with Marty
        self.client = self.CLIENT_TYPES[proto](proto, loc, *args, **kwargs)

        # To be able to do anything:
        self.enable_motors(True)


    def _pack_uint16(self, num):
        '''
        Pack an unsigned 16 bit int into two 8 bit bytes, little-endian
        Returns:
           tuple(least-sig-byte, most-sig-byte)
        '''
        data = struct.pack('<h', num)
        return data[0], data[1]


    def hello(self):
        '''
        Zero joints and wiggle eyebrows
        '''
        return self.client.execute('hello')


    def discover(self):
        '''
        Try and find us some Marties!
        '''
        return self.client.execute('discover')


    SIDE_CODES = {
        'left'    : 0x00,
        'right'   : 0x01,
        'forward' : 0x02,
        'back'    : 0x03
    }


    STOP_TYPE = {
        'clear queue'       : 0, # clear movement queue only (so finish the current movement)
        'clear and stop'    : 1, # clear movement queue and servo queues (freeze in-place)
        'clear and disable' : 2, # clear everything and disable motors
        'clear and zero'    : 3  # clear everything, and make robot return to zero
    }


    def stop(self, stop_type=None):
        '''
        Stop motions
        Args:
            stop_type, str, a member of Marty.STOP_TYPE's keys
        Raises:
            MartyCommandException if the stop_type is unknown
        '''
        if stop_type is None:
            stop_type = 'clear and zero'

        try:
            stop = self.STOP_TYPE[stop_type]
        except KeyError:
            raise MartyCommandException("Unknown Stop Type '{}', not in Marty.STOP_TYPE"
                                        "".format(stop_type))

        return self.client.execute('stop', stop)


    def move_joint(self, joint_id, postition, move_time):
        '''
        Move a specific joint to a position
        Args:
            move_time: how long this movement should last, in milliseconds
        '''
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('move_joint', joint_id, postition, dur_lsb, dur_msb)


    def lean(self, direction, amount, move_time):
        '''
        Lean over in a direction
        TODO: Calibration for amount
        Args:
            direction: 'left' or 'right'
            amount: distance
            move_time: how long this movement should last, in milliseconds
        '''
        side_c = self.SIDE_CODES[side]
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('lean', side_c, amount, dur_lsb, dur_msb)


    def walk(self, num_steps=2, start_foot='left', turn=0, step_length=25, move_time=1500):
        '''
        Walking macro
        TODO: Calibration step_length, turn
        Args:
            num_steps: int, how many steps to take
            start_foot: 'left' or 'right', start walking with this foot
            turn: Turnyness TODO No idea
            step_length: How far to step (approximately in mm)
            move_time: how long this movement should last, in milliseconds
        '''
        side_c = self.SIDE_CODES[start_foot]
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('walk', num_steps, turn, dur_lsb, dur_msb, step_length, side_c)


    def eyes(self, angle):
        '''
        Move the eyes to an angle
        Args:
            angle, int, degrees
        TODO: Calibration, zero if angle is None?
        '''
        return self.client.execute('eyes', angle)


    def kick(self, side, twist, move_time):
        '''
        Kick with Marty's feet
        TODO: Calibration for twist
        Args:
            side: 'left' or 'right', which foot to use
            twist: TODO
            move_time: how long this movement should last, in milliseconds
        '''
        side_c = self.SIDE_CODES[side]
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('kick', side_c, twist, dur_lsb, dur_msb)


    def arms(self, right_angle, left_angle, move_time):
        '''
        Move the arms to a position
        TODO: Calibration on angles
        Args:
            right_angle: Position of the right arm
            left_angle: Position of the left arm
            move_time: how long this movement should last, in milliseconds
        '''
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('arms', right_angle, left_angle, dur_lsb, dur_msb)


    def lift_leg(self, leg, distance, move_time):
        '''
        Lift a leg up
        TODO: Calibration for distance
        Args:
            leg: 'left' or 'right' leg
            distance: How high to raise the leg
            move_time: how long this movement should last, in milliseconds
        '''
        raise NotImplementedError()
        side_c = self.SIDE_CODES[side]
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('lift_leg', side_c, distance, dur_lsb, dur_msb)


    def lower_leg(self, leg, distance, move_time):
        '''
        Lower a leg down
        Args:
            leg: 'left' or 'right' leg
            distance: How much to lower the leg
            move_time: how long this movement should last, in milliseconds
        '''
        raise NotImplementedError()
        side_c = self.SIDE_CODES[side]
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('lower_leg', side_c, distance, dur_lsb, dur_msb)


    def celebrate(self, move_time=1000):
        '''
        Do a small celebration
        Args:
            move_time: how long this movement should last, in milliseconds
        '''
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('celebrate', dur_lsb, dur_msb)


    def sidestep(self, side, steps, step_length, move_time):
        '''
        Take sidesteps
        TODO: Calibration for step length
        Args:
            side: 'left' or 'right', direction to step in
            steps: number of steps to take
            step length: how broad the steps are
            move_time: how long this movement should last, in milliseconds
        '''
        side_c = self.SIDE_CODES[side]
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('sidestep', side_c, steps, dur_lsb, dur_msb, step_length)


    def stand_straight(self, move_time=1000):
        '''
        Return to the zero position for motors
        Args:
            move_time: how long this movement should last, in milliseconds
        '''
        dur_lsb, dur_msb = self._pack_uint16(move_time)
        return self.client.execute('stand_straight', dur_lsb, dur_msb)


    def play_sound(self, freq_start, freq_end, duration):
        '''
        Play a tone
        Args:
            freq_start: starting frequency, Hz
            freq_end:   ending frequency, Hz
            duration:   milliseconds, maximum 5000
        '''
        f_start_lsb, f_start_msb = self._pack_uint16(freq_start)
        f_end_lsb, f_end_msb = self._pack_uint16(freq_end)
        dur_lsb, dur_msb = self._pack_uint16(duration)
        return self.client.execute('play_sound',
                                   f_start_lsb, f_start_msb,
                                   f_end_lsb, f_end_msb,
                                   dur_lsb, dur_msb)


    def get_battery_voltage(self):
        '''
        Returns:
            The battery voltage reading as a float in Volts
        '''
        return self.client.execute('battery')


    ACCEL_AXES = {
        'x' : 0x00,
        'y' : 0x01,
        'z' : 0x02,
    }

    def get_accelerometer(self, axis):
        '''
        Args:
            axis: str 'x', 'y' or 'z'
        Returns:
            The most recently read x, y and z accelerations
        '''
        try:
            ax = self.ACCEL_AXES[axis]
        except KeyError:
            raise MartyCommandException("Axis must be one of {}, not '{}'"
                                        "".format(set(self.ACCEL_AXES.keys()), axis))
        return self.client.execute('accel', ax)


    def get_motor_current(self, motor_id):
        '''
        Args:
            motor_id, integer >= 0 (non-negative) selects which motor to query
        Returns:
            Instantaneous current sense reading from motor `motor_id`
        TODO: Calibrate units
        '''
        return self.client.execute('motorcurrent', int(motor_id))


    def digitalread_gpio(self, gpio):
        '''
        Returns:
            Returns High/Low state of a GPIO pin
        Args:
            GPIO pin number, >= 0 (non-negative)
        '''
        return bool(self.client.execute('gpio', int(gpio)))


    def enable_motors(self, enable=True):
        '''
        Toggle power to motors
        Args:
            enable: True/False toggle
        '''
        if enable:
            return self.client.execute('enable_motors') and True
        else:
            return self.client.execute('disable_motors') and False


    def fall_protection(self, enable):
        '''
        Toggle fall protections
        Args:
            enable: True/False toggle
        '''
        return self.client.execute('fall_protection', enable)


    def motor_protection(self, enable):
        '''
        Toggle motor current protections
        Args:
            enable: True/False toggle
        '''
        return self.client.execute('motor_protection', enable)


    def battery_protection(self, enable):
        '''
        Toggle low battery protections
        Args:
            enable: True/False toggle
        '''
        return self.client.execute('battery_protection', enable)


    def buzz_prevention(self, enable):
        '''
        Toggle motor buzz prevention
        Args:
            enable: True/False toggle
        '''
        return self.client.execute('buzz_prevention', enable)


    def save_calibration(self):
        '''
        Set the current motor positions as the zero positions
        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        return self.client.execute('save_calibration')


    def ros_command(self, byte_array):
        '''
        Low level proxied access to the ROS Serial API between
        the modem and main controller
        '''
        return self.client.execute('ros_command', byte_array)


    def get_chatter(self):
        '''
        Return chatter topic data (variable length)
        '''
        return self.client.execute('chatter')
