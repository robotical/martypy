'''
Marty
Python 3 library to communicate with Marty V1 and V2 by Robotical

Getting started:
1) Import Marty from the martypy library
2) Create a Marty object that connects the way you want
3) Tell your marty to walk

.. code-block:: python
from martypy import Marty
my_marty = Marty("wifi","192.168.0.53")
my_marty.walk()
...
'''
from typing import Dict, List, Optional, Union
from .serialclient import SerialClient
from .socketclient import SocketClient
from .exceptions import (MartyCommandException,
                         MartyConfigException)

class Marty(object):

    CLIENT_TYPES = {
        'socket' : SocketClient,
        'exp'    : SerialClient,
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
        'left hip'       : 0,
        'left twist'     : 1,
        'left knee'      : 2,
        'right hip'      : 3,
        'right twist'    : 4,
        'right knee'     : 5,
        'left arm'       : 6,
        'right arm'      : 7,
        'eyes'          : 8        
    }

    JOINT_STATUS = {
        'enabled'           : 0x01,
        'current limit now' : 0x02,
        'current limit long': 0x04,
        'busy'              : 0x08,
        'pos restricted'    : 0x10,
        'paused'            : 0x20,
        'comms ok'          : 0x80
    }

    ACCEL_AXES = {
        'x' : 0,
        'y' : 1,
        'z' : 2,
    }

    HW_ELEM_TYPES = [
        "SmartServo",
        "IMU",
        "I2SOut",
        "BusPixels",
        "GPIO",
        "FuelGauge",
        "PowerCtrl"
        ]

    ADD_ON_TYPE_NAMES = [
        "IRFoot"
    ]

    def __init__(self, 
                method: str,
                locator: str,
                client_types: dict = dict(),
                *args, **kwargs) -> None:
        '''
        Start a connection with Marty
        For example:
            (1) to connect to Marty via WiFi on IP Address 192.168.0.53
                use Marty("wifi", "192.168.86.53")
            (2) on a Windows computer with Marty connected by USB cable to COM2
                use Marty("usb", "COM2")
            (3) on a Mac computer with Marty connected by USB cable to /dev/tty.SLAB_USBtoUART
                use Marty("usb", "/dev/tty.SLAB_USBtoUART")
            (4) on a Raspberry Pi computer with Marty connected by expansion cable to /dev/ttyAMA0
                use Marty("exp", "/dev/ttyAMA0")

        Args:
            method: string, method of connecting to Marty - it may be: "usb",
                "wifi", "socket" (Marty V1) or "exp" (expansion port used to connect
                to a Raspberry Pi, etc)
            locator: string, depending on the method of connection (above) this is the
                serial port, IP Address or network name of Marty - that the computer uses
                to communicate with Marty.

        Raises:
            MartyConfigException if the parameters are invalid
            MartyConnectException if Marty couldn't be contacted
        '''
        # Merge in any clients that have been added and check valid
        self.CLIENT_TYPES = SocketClient.dict_merge(self.CLIENT_TYPES, client_types)
        if method not in self.CLIENT_TYPES.keys():
            raise MartyConfigException('Unrecognised URL clientType "{}"'.format(method))

        # Initialise the client class used to communicate with Marty
        self.client = self.CLIENT_TYPES[method](method, locator, *args, **kwargs)

        # Get Marty details
        self.client.start()

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
            turn: How much to turn (-128 to 127), 0 is straight.
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
        return self.client.eyes(Marty.JOINT_IDS['eyes'], pose_or_angle, move_time)

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

    def stop(self, stop_type: Optional[str] = None) -> bool:
        '''
        Stop Marty's movement

        Args:
            stop_type, can be:
                'clear queue'       clear movement queue only (so finish the current movement)
                'clear and stop'    clear movement queue and servo queues (freeze in-place)
                'clear and disable' clear everything and disable motors
                'clear and zero'    clear everything, and make robot return to zero
                'pause'             pause, but keep servo and movequeue intact and motors enabled
                'pause and disable' as pause, but disable motors too

        Raises:
            MartyCommandException if the stop_type is unknown
        '''
        # Default to plain "stop"
        stopInfo = 1 
        if stop_type is not None:
            if stop_type not in self.STOP_TYPE:
                self.client._preException(True)
                raise MartyCommandException("Unknown Stop Type '{}', not in Marty.STOP_TYPE"
                                            "".format(stop_type))
            stopInfo = self.STOP_TYPE.get(stop_type, stopInfo)
        return self.client.stop(stopInfo)

    def hold_position(self, hold_time: int) -> bool:
        '''Hold Marty at its current position

        Args:
            hold_time, time to hold position in milli-seconds
        '''
        # Default to plain "stop"
        return self.client.hold_position(hold_time)

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

    def move_joint(self, joint_name_or_num: Union[int, str], position: float, move_time: int) -> bool:
        '''
        Move a specific joint to a position
        Args:
            joint_name_or_num: joint to move, see the Marty.JOINT_IDS dictionary (can be name or number)
            position: angle in degrees
            move_time: how long this movement should last, in milliseconds
        Raises:
            MartyCommandException if the joint_name_or_num is unknown
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client._preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
        return self.client.move_joint(jointIDNo, position, move_time)

    def get_joint_position(self, joint_name_or_num: Union[int, str]) -> float:
        '''
        Get the position (angle in degrees) of a joint
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        Raises:
            MartyCommandException if the joint_name_or_num is unknown            
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client._preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
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
        Raises:
            MartyCommandException if the joint_name_or_num is unknown
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client._preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
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
        Raises:
            MartyCommandException if the joint_name_or_num is unknown
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client._preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
        return self.client.get_joint_status(jointIDNo)

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
        Raises:
            MartyCommandException if the axis is unknown
        '''
        axisCode = 0
        if (axis is not None) and (type(axis) is str):
            if axis not in self.ACCEL_AXES:
                self.client._preException(True)
                raise MartyCommandException("Axis must be one of {}, not '{}'"
                                            "".format(set(self.ACCEL_AXES.keys()), axis))
            axisCode = self.ACCEL_AXES.get(axis, 0)
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
        Tell Marty to forget it's calibration
        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        return self.client.clear_calibration()

    def is_calibrated(self) -> bool:
        '''
        Check if Marty is calibrated
        '''
        return self.client.is_calibrated()

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
                "IDNo": the joint identification number (see Marty.JOINT_IDS)
                "name": the name of the joint
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
        return self.client.get_power_status()
    
    def get_add_ons_status(self) -> Dict:
        '''
        Get latest information for all add-ons
        Args:
            none
        Returns:
            Dictionary containing dictionaries (one for each add-on) each of which contain:
                "IDNo": the add-on identification number
                "name": the name of the add-on
                "type": the type of the add-on (see Marty.ADD_ON_TYPE_NAMES but it may not be in this list)
                "whoAmITypeCode": a code which can be used for further add-on identification
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
                "IDNo": the add-on identification number
                "valid": True if the data is valid
                "data": 10 bytes of data from the add-on - the format of this data depends
                        on the type of add-on
        '''
        return self.client.get_add_on_status(add_on_name_or_id)

    def get_system_info(self) -> Dict:
        '''
        Get information about Marty
        Args:
            none
        Returns:
            Dictionary containing:
                "HardwareVersion": string containing the version of Marty hardware
                                "1.0" for Marty V1
                                "2.0" for Marty V2
                                other values for later versions of Marty
                "SystemName": the name of the physical hardware in Marty - this will be 
                              RicFirmwareESP32 for Marty V2 and
                              MartyV1 for Marty V1
                "SystemVersion": a string in semantic versioning format with the version
                                 of Marty firmware (e.g. "1.2.3")
                "SerialNo": serial number of this Marty
                "MAC": the base MAC address of the Marty
        '''
        return self.client.get_system_info()

    def get_system_info(self) -> Dict:
        '''
        Get information about Marty
        Args:
            none
        Returns:
            Dictionary containing:
                "HardwareVersion": string containing the version of Marty hardware
                                "1.0" for Marty V1
                                "2.0" for Marty V2
                                other values for later versions of Marty
                "SystemName": the name of the physical hardware in Marty - this will be 
                              RicFirmwareESP32 for Marty V2 and
                              MartyV1 for Marty V1
                "SystemVersion": a string in semantic versioning format with the version
                                 of Marty firmware (e.g. "1.2.3")
                "SerialNo": serial number of this Marty
                "MAC": the base MAC address of the Marty
        '''
        return self.client.get_system_info()

    def set_marty_name(self, name: str) -> bool:
        '''
        Set Marty's name
        Args:
            name to call Marty
        Returns:
            True if successful in setting the name
        '''
        return self.client.set_marty_name(name)

    def get_marty_name(self) -> str:
        '''
        Get Marty's name
        Args:
            none
        Returns:
            the name given to Marty
        '''
        return self.client.get_marty_name()

    def is_marty_name_set(self) -> bool:
        '''
        Check if Marty's name is set
        Args:
            none
        Returns:
            True if Marty's name is set
        '''
        return self.client.is_marty_name_set()

    def get_hw_elems_list(self) -> List:
        '''
        Get a list of all of the hardware elements on Marty
        Args:
            none
        Returns:
            List containing a dictionary for each hardware element, each element is in the form:
                "name": name of the hardware element
                "type": type of element, see Marty.HW_ELEM_TYPES, other types may appear as add-ons
                "busName": name of the bus the element is connected to
                "addr": address of the element if it is connected to a bus
                "addrValid": 1 if the address is valid, else 0
                "IDNo": identification number of the element
                "whoAmI": string from the hardware which may contain additional identification
                "whoAmITypeCode": string indicating the type of hardware
                "SN": serial number of the hardware element
                "versionStr": version string of hardware element in semantic versioning (semver) format
                "commsOK": 1 if the element is communicating ok, 0 if not
        '''
        return self.client.get_hw_elem_status()

    def send_ric_rest_cmd(self, ricRestCmd: str) -> None:
        '''
        Send a command in RIC REST format to Marty
        This is a special purpose command which you can use to do advanced
        control of Marty
        Args:
            ricRestCmd: string containing the command to send to Marty
        Returns:
            None
        '''
        self.client.send_ric_rest_cmd(ricRestCmd)

    def send_ric_rest_cmd_sync(self, ricRestCmd: str) -> Dict:
        '''
        Send a command in RIC REST format to Marty and wait for reply
        This is a special purpose command which you can use to do advanced
        control of Marty
        Args:
            ricRestCmd: string containing the command to send to Marty
        Returns:
            Dictionary containing the response received from Marty
        '''
        return self.client.send_ric_rest_cmd_sync(ricRestCmd)

    def get_ready(self) -> bool:
        '''
        Prepare for motion!
        '''
        return self.client.get_ready()

    def __del__(self) -> None:
        '''
        Marty is stopping
        '''
        self.client.close()

    def close(self) -> None:
        '''
        Close connection to Marty
        '''
        if self.client:
            self.client.close()

    def hello(self) -> bool:
        '''
        Zero joints and wiggle eyebrows
        '''
        return self.client.hello()

    def discover(self) -> List[str]:
        '''
        Try and find us some Martys!
        '''
        return self.client.discover()

