'''
Marty
Python library to communicate with Marty V1 and V2
'''
from typing import Dict, List, Optional, Tuple, Union
import six
import struct
from .serialclient import SerialClient
from .socketclient import SocketClient
from .exceptions import (MartyCommandException,
                         MartyConfigException)

class Marty(object):
    '''
    High-level client library for Marty the Robot by Robotical Ltd
    '''
    CLIENT_TYPES = {
        'socket' : SocketClient,
        'alt'    : SerialClient,
        'usb'    : SerialClient,
    }

    STOP_TYPE = {
        'clear queue'       : 0, # clear movement queue only (so finish the current movement)
        'clear and stop'    : 1, # clear movement queue and servo queues (freeze in-place)
        'clear and disable' : 2, # clear everything and disable motors
        'clear and zero'    : 3, # clear everything, and make robot return to zero
        'pause'             : 4, # pause, but keep servo and movequeue intact and motors enabled
        'pause and disable' : 5, # as 4, but disable motors too
    }

    JOINT_IDS = {
        'LeftHip'       : 0,
        'LeftTwist'     : 1,
        'LeftKnee'      : 2,
        'RightHip'      : 3,
        'RightTwist'    : 4,
        'RightKnee'     : 5,
        'LeftArm'       : 6,
        'RightArm'      : 7,
        'Eyes'          : 8        
    }

    JOINT_STATUS = {
        'Enabled'       : 0x01,
        'CurrentLimInst': 0x02,
        'CurrentLimSust': 0x04,
        'Busy'          : 0x08,
        'PosRestricted' : 0x10,
        'Paused'        : 0x20,
        'CommsOk'       : 0x80
    }

    ACCEL_AXES = {
        'x' : 0,
        'y' : 1,
        'z' : 2,
    }

    def __init__(self, url: str ='socket://marty.local',
                 client_types: dict = dict(),
                 *args, **kwargs) -> None:
        '''
        Initialise a Marty client class from a url

        Args:
            url: How to connect to Marty - e.g. 
                 usb://COM2 for Windows serial connection to Marty USB port
                 alt://dev/ttyAMA0 for Raspberry Pi serial connection

        Raises:
            MartyConfigException if the parameters are invalid
            MartyConnectException if Marty couldn't be connected
        '''
        # Get and check connection parameters
        client_type, _, loc = url.partition('://')
        if not (client_type and loc):
            raise MartyConfigException('Invalid URL format "{}" given'.format(url))

        # Merge in any clients that have been added and check valid
        self.CLIENT_TYPES = SocketClient.dict_merge(self.CLIENT_TYPES, client_types)
        if client_type not in self.CLIENT_TYPES.keys():
            raise MartyConfigException('Unrecognised URL clientType "{}"'.format(client_type))

        # Initialise the client class used to communicate with Marty
        self.client = self.CLIENT_TYPES[client_type](client_type, loc, *args, **kwargs)

        # Get Marty details
        self.client.start()

    def close(self) -> None:
        '''
        Close connection to Marty
        '''
        self.client.close()

    def hello(self) -> bool:
        '''
        Zero joints and wiggle eyebrows
        '''
        return self.client.hello()

    def get_ready(self) -> bool:
        '''
        Prepare for motion!
        '''
        return self.client.get_ready()

    def discover(self) -> List[str]:
        '''
        Try and find us some Martys!
        '''
        return self.client.discover()

    def stop(self, stop_type: Optional[str] = None) -> bool:
        '''
        Stop motions
        Args:
            stop_type, str, a member of Marty.STOP_TYPE's keys
        Raises:
            MartyCommandException if the stop_type is unknown
        '''
        # Default to plain "stop"
        stopInfo = 1 
        if stop_type is not None:
            try:
                stopInfo = self.STOP_TYPE[stop_type]
            except KeyError:
                raise MartyCommandException("Unknown Stop Type '{}', not in Marty.STOP_TYPE"
                                            "".format(stop_type))
        return self.client.stop(stopInfo)

    def move_joint(self, joint_name_or_num: Union[int, str], position: float, move_time: int) -> bool:
        '''
        Move a specific joint to a position
        Args:
            joint_name_or_num: joint to move, see the Marty.JOINT_IDS dictionary (can be name or number)
            position: angle in degrees
            move_time: how long this movement should last, in milliseconds
        '''
        try:
            if type(joint_name_or_num) is str:
                jointIDNo = self.JOINT_IDS[joint_name_or_num]
            else:
                jointIDNo = joint_name_or_num
        except KeyError:
            raise MartyCommandException("Joint must be one of {}, not '{}'"
                                        "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
        self.client.move_joint(jointIDNo, position, move_time)

    def get_joint_position(self, joint_name_or_num: Union[int, str]) -> float:
        '''
        Get the position (angle in degrees) of a joint
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        '''
        try:
            if type(joint_name_or_num) is str:
                jointIDNo = self.JOINT_IDS[joint_name_or_num]
            else:
                jointIDNo = joint_name_or_num
        except KeyError:
            raise MartyCommandException("Joint must be one of {}, not '{}'"
                                        "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
        return self.client.get_joint_position(jointIDNo)

    def get_joint_current(self, joint_name_or_num: Union[int, str]) -> float:
        '''
        Get the current (in milli-Amps) of a joint
        This can be useful in detecting when the joint is working hard and is related
        to the force which the joint's motor is exerting to stay where it is
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        Returns:
            current of the joint in milli-Amps
            will be 0 if the joint current is unknown
        '''
        try:
            if type(joint_name_or_num) is str:
                jointIDNo = self.JOINT_IDS[joint_name_or_num]
            else:
                jointIDNo = joint_name_or_num
        except KeyError:
            raise MartyCommandException("Joint must be one of {}, not '{}'"
                                        "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
        return self.client.get_joint_current(jointIDNo)

    def get_joint_status(self, joint_name_or_num: Union[int, str]) -> int:
        '''
        Get information about a joint
        This can be helpful to find out if the joint is working correctly and if it is
        moving at the moment, etc
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        Returns:
            a code number which is the sum of codes in the Marty.JOINT_STATUS dictionary
            will be 0 if the joint status is unknown
        '''
        try:
            if type(joint_name_or_num) is str:
                jointIDNo = self.JOINT_IDS[joint_name_or_num]
            else:
                jointIDNo = joint_name_or_num
        except KeyError:
            raise MartyCommandException("Joint must be one of {}, not '{}'"
                                        "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
        return self.client.get_joint_status(jointIDNo)

    def lean(self, direction: str, amount: float, move_time: int) -> bool:
        '''
        Lean over in a direction
        Args:
            direction: 'left', 'right', 'forward', 'back', 'auto'
            amount: percentage of normal lean
            move_time: how long this movement should last, in milliseconds
        '''
        return self.client.lean(direction, amount, move_time)

    def walk(self, num_steps: int = 2, start_foot:str = 'auto', turn: int = 0, 
                step_length:int = 40, move_time: int = 1500) -> bool:
        '''
        Walking macro
        Args:
            num_steps: int, how many steps to take
            start_foot: 'left', 'right' or 'auto', start walking with this foot
            turn: How much to turn (-128 to 127). 0 is straight.
            step_length: How far to step (approximately in mm)
            move_time: how long this movement should last, in milliseconds
        '''
        return self.client.walk(num_steps, start_foot, turn, step_length, move_time)

    def eyes(self, pose_or_angle: Union[str, float], move_time: int = 100) -> bool:
        '''
        Move the eyes to a pose or an angle
        Args:
            pose_or_angle: 'angry', 'excited', 'normal', 'wide', 'wiggle' or 
                           angle (in degrees - can be negative),
            move_time, milliseconds
        '''
        return self.client.eyes(Marty.JOINT_IDS['Eyes'], pose_or_angle, move_time)

    def kick(self, side: str = 'right', twist: float = 0, move_time: int = 2000) -> bool:
        '''
        Kick with Marty's feet
        Args:
            side: 'left' or 'right', which foot to use
            twist: this parameter is not used (just leave blank or pass 0 value)
            move_time: how long this movement should last, in milliseconds
        '''
        return self.client.kick(side, twist, move_time)

    def arms(self, left_angle: float, right_angle: float, move_time: int) -> bool:
        '''
        Move the arms to a position
        Args:
            left_angle: Position of the left arm (-128 to 127)
            right_angle: Position of the right arm (-128 to 127)
            move_time: how long this movement should last, in milliseconds
        '''
        return self.client.arms(left_angle, right_angle, move_time)

    def celebrate(self, move_time: int = 4000) -> bool:
        '''
        Do a small celebration
        Args:
            move_time: how long this movement should last, in milliseconds
        '''

        # TODO - add celebrate trajectory to Marty V2

        return self.client.celebrate(move_time)

    def circle_dance(self, side: str = 'right', move_time: int = 1500) -> bool:
        '''
        Boogy, Marty!
        '''
        return self.client.circle_dance(side, move_time)

    def dance(self, side: str = 'right', move_time: int = 1500) -> bool:
        '''
        Another Boogy, Marty!
        '''
        return self.client.dance(side, move_time)

    def wiggle(self, move_time: int = 1500) -> bool:
        '''
        Wiggle Marty!
        '''
        return self.client.wiggle(move_time)

    def sidestep(self, side: str, steps: int = 1, step_length: int = 100, 
            move_time: int = 2000) -> bool:
        '''
        Take sidesteps
        Args:
            side: 'left' or 'right', direction to step in
            steps: number of steps to take
            step length: how broad the steps are (up to 127)
            move_time: how long this movement should last, in milliseconds
        '''
        return self.client.sidestep(side, steps, step_length, move_time)

    def play_sound(self, name_or_freq_start: Union[str,float], 
            freq_end: Optional[float] = None, 
            duration: Optional[int] = None) -> bool:
        '''
        Play a named sound (Marty V2) or make a tone (Marty V1)
        Args (Marty V2):
            name_or_freq_start: name of sound
        Args (Marty V1):
            name_or_freq_start: starting frequency, Hz
            freq_end:  ending frequency, Hz
            duration: milliseconds, maximum 5000
        '''
        return self.client.play_sound(name_or_freq_start, freq_end, duration)

    def pinmode_gpio(self, gpio: int, mode: str) -> bool:
        '''
        Configure a GPIO pin

        gpio: pin number between 0 and 7
        mode: choose from: 'digital in','analog in' or 'digital out'
        '''
        return self.client.pinmode_gpio(gpio, mode)

    def write_gpio(self, gpio:int, value: int) -> bool:
        '''
        Write a value to a GPIO port
        '''
        return self.client.write_gpio(gpio, value)

    def digitalread_gpio(self, gpio: int) -> bool:
        '''
        Returns:
            Returns High/Low state of a GPIO pin
        Args:
            GPIO pin number, >= 0 (non-negative)
        '''
        return self.client.digitalread_gpio(gpio)

    def i2c_write(self, *byte_array: int) -> bool:
        '''
        Write a bytestream to the i2c port.
        The first byte should be the address, following from that
        the datagram folows standard i2c spec
        '''
        return self.client.i2c_write(*byte_array)

    def i2c_write_to_ric(self, address: int, byte_array: bytes) -> bool:
        '''
        Write a formatted bytestream to the i2c port.
        The bytestream is formatted in the ROS serial format.

        address: the other device's address
        '''
        return self.client.i2c_write_to_ric(address, byte_array)

    def i2c_write_to_rick(self, address: int, byte_array: bytes) -> bool:
        '''
        Write a formatted bytestream to the i2c port.
        The bytestream is formatted in the ROS serial format.

        address: the other device's address
        '''
        return self.client.i2c_write_to_ric(address, byte_array)

    def get_battery_voltage(self) -> float:
        '''
        Returns:
            The battery voltage reading as a float in Volts
        '''
        return self.client.get_battery_voltage()

    def get_battery_remaining(self) -> float:
        '''
        Returns:
            The battery remaining capacity in percent
        '''
        return self.client.get_battery_remaining()

    def get_distance_sensor(self) -> float:
        '''
        Returns:
            The distance sensor reading as a float (raw, no units)
        '''
        return self.client.distance()

    def get_accelerometer(self, axis: Optional[str] = None) -> float:
        '''
        Args:
            axis: (optional) str 'x', 'y' or 'z' - if omitted then return x, y and z values
        Returns:
            If axis is provided then returns the most recently read x, y or z 
                acceleration value - or 0 if no information is available
            If axis is not provided returns a tuple with x, y and z values (which may
                be 0 if no information is available)
        '''
        axisCode = 0
        if axis is not None:
            try:
                axisCode = self.ACCEL_AXES[axis]
            except KeyError:
                raise MartyCommandException("Axis must be one of {}, not '{}'"
                                            "".format(set(self.ACCEL_AXES.keys()), axis))
        return self.client.get_accelerometer(axis, axisCode)

    def get_motor_current(self, motor_id: int) -> float:
        '''
        Args:
            motor_id, integer >= 0 (non-negative) selects which motor to query
        Returns:
            Instantaneous current sense reading from motor `motor_id`
        '''
        return self.get_joint_current(motor_id)

    def enable_motors(self, enable: bool = True, clear_queue: bool = True) -> bool:
        '''
        Toggle power to motors
        Args:
            enable: True/False toggle
            clear_queue: Default True, prevents unfinished but 'muted' motions
                         from jumping as soon as motors are enabled
        '''
        return self.client.enable_motors(enable, clear_queue)

    def enable_safeties(self, enable: bool = True) -> bool:
        '''
        Tell the board to turn on 'normal' safeties
        '''
        return self.client.enable_safeties(enable)

    def fall_protection(self, enable: bool = True) -> bool:
        '''
        Toggle fall protections
        Args:
            enable: True/False toggle
        '''
        return self.client.fall_protection(enable)

    def motor_protection(self, enable: bool = True) -> bool:
        '''
        Toggle motor current protections
        Args:
            enable: True/False toggle
        '''
        return self.client.motor_protection(enable)

    def battery_protection(self, enable: bool = True) -> bool:
        '''
        Toggle low battery protections
        Args:
            enable: True/False toggle
        '''
        return self.client.battery_protection(enable)

    def buzz_prevention(self, enable: bool = True) -> bool:
        '''
        Toggle motor buzz prevention
        Args:
            enable: True/False toggle
        '''
        return self.client.buzz_prevention(enable)

    def lifelike_behaviour(self, enable: bool = True) -> bool:
        '''
        Tell the robot whether it can or can't move now and then in a lifelike way when idle.
        Args:
            enable: True/False toggle
        '''
        return self.client.lifelike_behaviour(enable)

    def set_parameter(self, *byte_array: int) -> bool:
        '''
        Set board parameters.

        Args:
            byte_array: a list in the following format [paramID, params]
        '''
        return self.client.set_parameter(byte_array)

    def save_calibration(self) -> bool:
        '''
        Set the current motor positions as the zero positions
        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        return self.client.save_calibration()

    def clear_calibration(self) -> bool:
        '''
        Tell the Robot to forget it's calibration
        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        return self.client.clear_calibration()

    def ros_command(self, *byte_array: int) -> bool:
        '''
        Low level proxied access to the ROS Serial API between
        the modem and main controller
        '''
        return self.client.ros_command(*byte_array)

    def keyframe (self, time: float, num_of_msgs: int, msgs) -> List[bytes]:
        '''
        Takes in information about movements and generates keyframes
        returns a list of bytes

        time: time (in seconds) taken to complete movement
        num_of_msgs: number of commands sent
        msgs: commands sent in the following format [(ID CMD), (ID CMD), etc...]
        '''
        return self.client.keyframe(time, num_of_msgs, msgs)

    def get_chatter(self) -> bytes:
        '''
        Return chatter topic data (variable length)
        '''
        return self.client.get_chatter()

    def get_firmware_version(self) -> bool:
        '''
        Ask the board to print the firmware version over chatter
        '''
        return self.client.get_firmware_version()

    def _mute_serial(self) -> bool:
        '''
        Mutes the internal serial line on RIC. Depends on platform and API
        NOTE: Once you've done this, the Robot will ignore you until you cycle power.
        '''
        return self.client.mute_serial()

    def ros_serial_formatter(self, topicID: int, send: bool = False, *message: int) -> List[int]:
        '''
        Formats message into ROS serial format and
        returns formatted message as a list

        Calls ros_command with the processed message if send is True.

        More information about the ROS serial format can be
        found here: http://wiki.ros.org/rosserial/Overview/Protocol
        '''
        return self.client.ros_serial_formatter(topicID, send, message)

    def is_moving(self) -> bool:
        '''
        Check if Marty is moving

        Args:
            none
        Returns:
            True if Marty is moving
        '''
        return self.client.is_moving()

    def is_paused(self) -> bool:
        '''
        Check if Marty is paused

        Args:
            none
        Returns:
            True if Marty is paused
        '''
        return self.client.is_paused()

    def get_robot_status(self) -> Dict:
        '''
        Get status of Marty the Robot

        Args:
            none
        Returns:
            Dictionary containing:
                "workQCount" number of work items (movements) that are queued up
                "isMoving": True if Marty is moving
                "isPaused": True if Marty is paused
                "isFwUpdating": True if Marty is doing an update
        '''
        return self.client.get_robot_status()

    def get_joints(self) -> Dict:
        '''
        Get information on all of Marty's joints

        Args:
            none
        Returns:
            Dictionary containing dictionaries (one for each joint) each of which contain:
                "id": the joint identification number (see Marty.JOINT_IDS)
                "pos": the angle of the joint
                "current": the joint current (in milli-Amps)
                "enabled": True if the servo is enabled
                "commsOK": True if the servo is communicating ok
                "flags": joint status flags (see Marty.JOINT_STATUS)
        '''
        return self.client.get_joints()

    def get_power_status(self) -> Dict:
        '''
        Get information on all of Marty's joints

        Args:
            none
        Returns:
            Dictionary containing:
                "remCapPC" remaining battery capacity in percent
                "tempDegC": battery temperature in degrees C
                "remCapMAH": remaining battery capacity in milli-Amp-Hours
                "fullCapMAH": capacity of the battery when full in milli-Amp-Hours
                "currentMA": current the battery is supplying (or being charged with) milli-Amps
                "power5VOnTimeSecs": number of seconds the power to joints and add-ons has been on
                "isOnUSBPower": True if Marty is running on power from the USB connector
                "is5VOn": True if power to the joints and add-ons is turned on
        '''
        raise self.client.get_power_status()
    
    def get_add_ons_status(self) -> Dict:
        '''
        Get latest information for all add-ons

        Args:
            none
        Returns:
            Dictionary containing dictionaries (one for each add-on) each of which contain:
                "id": the add-on identification number
                "valid": True if the data is valid
                "data": 10 bytes of data from the add-on - the format of this data depends
                        on the type of add-on
        '''
        return self.client.get_add_ons_status()

    def get_add_on_status(self, add_on_name_or_id: Union[int, str]) -> Dict:
        '''
        Get latest information for a single add-on

        Args:
            add_on_name_or_id: either the name or the id (number) of an add-on
        Returns:
            Dictionary containing:
                "id": the add-on identification number
                "valid": True if the data is valid
                "data": 10 bytes of data from the add-on - the format of this data depends
                        on the type of add-on
        '''
        return self.client.get_add_on_status(add_on_name_or_id)
