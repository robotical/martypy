'''
Python library to communicate with Marty the Robot V1 and V2 by Robotical

Getting started:  
1) Import Marty from the martypy library  
2) Create a Marty object that connects the way you want  
3) Tell your Marty to dance  

```python
from martypy import Marty  
my_marty = Marty("wifi","192.168.0.53")  
my_marty.dance()
```

The tags :one: and :two: indicate when the method is available for Marty V1 :one: and Marty V2 :two:
'''
import time
from typing import Callable, Dict, List, Optional, Union, Tuple
from enum import Enum
from .ClientGeneric import ClientGeneric
from .ClientMV2 import ClientMV2
from .ClientMV1 import ClientMV1
from .Exceptions import (MartyCommandException,
                         MartyConfigException)
from .RICROSSerial import RICROSSerial

class Marty(object):

    CLIENT_TYPES = {
        'socket' : ClientMV1,
        'exp'    : ClientMV2,
        'usb'    : ClientMV2,
        'wifi'   : ClientMV2,
        'test'   : ClientMV2,
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
        'eyes'           : 8        
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

    HW_ELEM_IDS = {
        'LeftHip'        : 0,
        'LeftTwist'      : 1,
        'LeftKnee'       : 2,
        'RightHip'       : 3,
        'RightTwist'     : 4,
        'RightKnee'      : 5,
        'LeftArm'        : 6,
        'RightArm'       : 7,
        'Eyes'           : 8,
        'IMU0'           : 19,
    }

    ADD_ON_TYPE_NAMES = [
        "IRFoot"
    ]

    PUBLISH_TOPIC_SERVOS = RICROSSerial.ROSTOPIC_V2_SMART_SERVOS
    PUBLISH_TOPIC_ACCELEROMETER = RICROSSerial.ROSTOPIC_V2_ACCEL
    PUBLISH_TOPIC_POWER = RICROSSerial.ROSTOPIC_V2_POWER_STATUS
    PUBLISH_TOPIC_ADDONS = RICROSSerial.ROSTOPIC_V2_ADDONS
    PUBLISH_TOPIC_ROBOT_STATUS = RICROSSerial.ROSTOPIC_V2_ROBOT_STATUS

    class Disco(Enum):
        ARMS = {"00000088"}
        FEET = {"00000087"}
        EYES = {"00000089"}
        ALL = {"00000087", "00000088", "00000089"}

    def __init__(self,
                method: str,
                locator: str = "",
                extra_client_types: dict = dict(),
                blocking: Union[bool, None] = None,
                *args, **kwargs) -> None:
        '''
        Start a connection to Marty :one: :two:

        For example:

            * `Marty("wifi", "192.168.86.53")` to connect to Marty via WiFi on IP Address 192.168.0.53
            * `Marty("usb", "COM2")` on a Windows computer with Marty connected by USB cable to COM2
            * `Marty("usb", "/dev/tty.SLAB_USBtoUART")` on a Mac computer with Marty connected by USB cable to /dev/tty.SLAB_USBtoUART
            * `Marty("exp", "/dev/ttyAMA0")` on a Raspberry Pi computer with Marty connected by expansion cable to /dev/ttyAMA0

        **Blocking Mode**

        Each command that makes Marty move (e.g. `walk()`, `dance()`, `move_joint()`,
        but also `hold_position()`) comes with two modes - blocking and non-blocking.

        Issuing a command in blocking mode will make your program pause until Marty
        physically stops moving. Only then the next line of your code will be executed.

        In non-blocking mode, each movement command simply tells Marty what to do and
        returns immediately, meaning that your code will continue to execute while
        Marty is moving.

        Every movement command takes an optional `blocking` argument that can be used
        to choose the mode for that call. If you plan to use the same mode all or most
        of the time, it is better to to use the `Marty.set_blocking()` method or use
        the `blocking` constructor argument. The latter defaults to `True` (blocking)
        if not provided.

        Args:
            method: method of connecting to Marty - it may be: "usb",
                "wifi", "socket" (Marty V1) or "exp" (expansion port used to connect
                to a Raspberry Pi, etc)
            locator: location to connect to, depending on the method of connection this
                is the serial port name, network (IP) Address or network name (hostname) of Marty
                that the computer should use to communicate with Marty.
                If `method` is `"usb"` and there is only a single Marty connected,
                `locator` can be left out and the Marty will be found automatically.
                If multiple Martys are detected, one of them will be chosen
                arbitrarily and connected to.
            blocking: Default movement command mode for this `Marty` instance.
                * `True` (default): blocking mode
                * `False`: non-blocking mode

        Raises:
            * MartyConfigException if the parameters are invalid
            * MartyConnectException if Marty couldn't be contacted
        '''
        # Merge in any extra clients that have been added and check valid
        self.client: ClientGeneric = None
        self.CLIENT_TYPES = ClientGeneric.dict_merge(self.CLIENT_TYPES, extra_client_types)

        # Get and check connection parameters
        if type(method) is not str:
            raise MartyConfigException(f'Method must be one of {self.CLIENT_TYPES.keys()}')
        if '://' in method:
            method, _, locator = method.partition('://')
        if method.lower() not in self.CLIENT_TYPES.keys():
            raise MartyConfigException(f'Unrecognised method "{method}"')

        # Initialise the client class used to communicate with Marty
        client_cls = self.CLIENT_TYPES[method.lower()]
        self.client = client_cls(method.lower(), locator, *args, blocking=blocking, **kwargs)

        # Get Marty details
        self.client.start()

    def dance(self, side: str = 'right', move_time: int = 3000, blocking: Optional[bool] = None) -> bool:
        '''
        Boogie, Marty! :one: :two:
        Args:
            side: 'left' or 'right', which side to start on
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.dance(side, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def celebrate(self, move_time: int = 4000, blocking: Optional[bool] = None) -> bool:
        '''
        Coming soon! Same as `wiggle()` for now. :one: :two:
        Args:
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.celebrate(move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def wiggle(self, move_time: int = 4000, blocking: Optional[bool] = None) -> bool:
        '''
        Wiggle :two:
        Args:
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.wiggle(move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def circle_dance(self, side: str = 'right', move_time: int = 2500, blocking: Optional[bool] = None) -> bool:
        '''
        Circle Dance :two:
        Args:
            side: 'left' or 'right', which side to start on
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.circle_dance(side, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def walk(self, num_steps: int = 2, start_foot:str = 'auto', turn: int = 0,
                step_length:int = 25, move_time: int = 1500, blocking: Optional[bool] = None) -> bool:
        '''
        Make Marty walk :one: :two:
        Args:
            num_steps: how many steps to take
            start_foot: 'left', 'right' or 'auto', start walking with this foot Note: :two: Unless
                    you specify 'auto', all steps are taken with the same foot so
                    it only makes sense to use the start_foot argument with `num_steps=1`.
            turn: How much to turn (-100 to 100 in degrees), 0 is straight.
            step_length: How far to step (approximately in mm)
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.walk(num_steps, start_foot, turn, step_length, move_time)
        if result:
            num_steps = max(1, min(num_steps, 10))  # Clip num_steps
            self.client.wait_if_required(num_steps*move_time, blocking)
        return result
    
    def lift_foot(self, side: str) -> bool:
        '''
        Lift one of Marty's feet :two:
        Args:
            side: 'left' or 'right', which foot to lift
        Returns:
            True if Marty accepted the request
        '''
        return self.client.lift_foot(side)

    def lower_foot(self, side: str) -> bool:
        '''
        Lower one of Marty's feet :two:
        Args:
            side: 'left' or 'right', which foot to lower
        Returns:
            True if Marty accepted the request
        '''
        return self.client.lower_foot(side)
    
    def wave(self, side: str) -> bool:
        '''
        Wave :two:
        Args:
            None
        Returns:
            True if Marty accepted the request
        '''
        return self.client.wave(side)

    def get_ready(self, blocking: Optional[bool] = None) -> bool:
        '''
        Move Marty to the normal standing position and wiggle eyebrows :one: :two:
        Will also enable motors for Marty v1 :one:
        Args:
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.get_ready()
        if result:
            self.client.wait_if_required(4000, blocking)
        return result

    def stand_straight(self, move_time: int = 2000, blocking: Optional[bool] = None) -> bool:
        '''
        Move Marty to the normal standing position :one: :two:
        Args:
            move_time: How long (in milliseconds) Marty will take to reach the
                normal standing position. (Higher number means slower movement.)
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.stand_straight(move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def eyes(self, pose_or_angle: Union[str, int], move_time: int = 1000, blocking: Optional[bool] = None) -> bool:
        '''
        Move the eyes to a pose or an angle :one: :two:
        Args:
            pose_or_angle: 'angry', 'excited', 'normal', 'wide', or 'wiggle' :two: - alternatively
                           this can be an angle in degrees (which can be a negative number)
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.eyes(Marty.JOINT_IDS['eyes'], pose_or_angle, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def kick(self, side: str = 'right', twist: int = 0, move_time: int = 2500, blocking: Optional[bool] = None) -> bool:
        '''
        Kick one of Marty's feet :one: :two:
        Args:
            side: 'left' or 'right', which foot to use
            twist: the amount of twisting do do while kicking (in degrees)
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.kick(side, twist, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def arms(self, left_angle: int, right_angle: int, move_time: int, blocking: Optional[bool] = None) -> bool:
        '''
        Move both of Marty's arms to angles you specify :one: :two:
        Args:
            left_angle: Angle of the left arm (degrees -100 to 100)
            right_angle: Position of the right arm (degrees -100 to 100)
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.arms(left_angle, right_angle, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def lean(self, direction: str, amount: Optional[int] = None, move_time: int = 1000,
             blocking: Optional[bool] = None) -> bool:
        '''
        Lean over in a direction :one: :two:
        Args:
            direction: `'left'`, `'right'`, `'forward'`, or `'back'`
            amount: How much to lean. The defaults and the exact meaning is
                different between Marty V1 and V2:
                - :one: If not specified or `None`, `amount` defaults to `50` (no
                        specific unit). Limit is -60/60 in either direction.
                - :two: If not specified or `None`, `amount` defaults to `29` degrees.
                        Limit for foward and back is 45 and limit for left and right is 60.
            move_time: How long this movement should last, in milliseconds.
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.lean(direction, amount, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def sidestep(self, side: str, steps: int = 1, step_length: int = 35,
            move_time: int = 1000, blocking: Optional[bool] = None) -> bool:
        '''
        Take sidesteps :one: :two:
        Args:
            side: 'left' or 'right', direction to step in
            steps: number of steps to take
            step_length: how broad the steps are (up to 127)
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.sidestep(side, steps, step_length, move_time)
        if result:
            steps = max(1, min(steps, 10))  # Clip steps
            self.client.wait_if_required(steps*move_time, blocking)
        return result

    def set_volume(self, volume: int) -> bool:
        '''
        Set the volume of Marty's sound :two:
        Args:
            volume: Volume to set (0-100)
        Returns:
            True if Marty accepted the request
        '''
        return self.client.set_volume(volume)

    def get_volume(self) -> int:
        '''
        Get the volume of Marty's sound :two:
        Args:
            None
        Returns:
            Volume of Marty's sound (0-100)
        '''
        return self.client.get_volume()

    def play_sound(self, name_or_freq_start: Union[str,int], 
            freq_end: Optional[int] = None, 
            duration: Optional[int] = None) -> bool:
        '''
        Play a named sound (Marty V2 :two:) or make a tone (Marty V1 :one:)
        Args:
            name_or_freq_start: name of the sound, e.g. 'excited' or 'no_way' :two:
            name_or_freq_start: starting frequency, min 20, max 20000, Hz :one:
            freq_end:  ending frequency, min 20, max 20000, Hz :one:
            duration: milliseconds, maximum 5000 :one:
        Returns:
            True if Marty accepted the request
        '''
        return self.client.play_sound(name_or_freq_start, freq_end, duration)

    def get_accelerometer(self, axis: Optional[str] = None) -> float:
        '''
        Get the latest value from the Marty's accelerometer :one: :two:
        Args:
            axis: (optional) 'x', 'y' or 'z' OR no parameter at all (see returns below)
        Returns:  
            * The acceleration value from the axis (if axis specified)  
            * A tuple containing x, y and z values (if no axis) :two:
            Note that the returned value will be 0 if no value is available
        Raises:
            MartyCommandException if the axis is unknown
        '''
        axisCode = 0
        if (axis is not None) and (type(axis) is str):
            if axis not in self.ACCEL_AXES:
                self.client.preException(True)
                raise MartyCommandException("Axis must be one of {}, not '{}'"
                                            "".format(set(self.ACCEL_AXES.keys()), axis))
            axisCode = self.ACCEL_AXES.get(axis, 0)
        return self.client.get_accelerometer(axis, axisCode)

    def is_moving(self) -> bool:
        '''
        Check if Marty is moving :two:
        Args:
            none
        Returns:
            True if Marty is moving
        '''
        return self.client.is_moving()

    def stop(self, stop_type: Optional[str] = None) -> bool:
        '''
        Stop Marty's movement  :one: :two:  

        You can also control what way to "stop" you want with the parameter stop_type. For instance:  
        
        * 'clear queue' to finish the current movement before stopping (clear any queued movements)
        * 'clear and stop' stop immediately (and clear queues)
        * 'clear and disable' :one: stop and disable the robot
        * 'clear and zero' stop and move back to get_ready pose
        * 'pause' pause motion
        * 'pause and disable' :one: pause motion and disable the robot

        Args:
            stop_type: the way to stop - see the options above

        Raises:
            MartyCommandException if the stop_type is unknown
        '''
        # Default to plain "stop"
        stopCode = 1 
        if stop_type is not None:
            if stop_type not in self.STOP_TYPE:
                self.client.preException(True)
                raise MartyCommandException("Unknown stop_type '{}', not in Marty.STOP_TYPE"
                                            "".format(stop_type))
            stopCode = self.STOP_TYPE.get(stop_type, stopCode)
        return self.client.stop(stop_type, stopCode)

    def resume(self) -> bool:
        '''
        Resume Marty's movement after a pause :two:
        Returns:
            True if Marty accepted the request
        '''
        return self.client.resume()

    def hold_position(self, hold_time: int, blocking: Optional[bool] = None) -> bool:
        '''
        Hold Marty at its current position :two:
        Args:
            hold_time, time to hold position in milli-seconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
                Holding position counts as movement because Marty is using its motors to
                actively resist any attempts to move its joints.
        Returns:
            True if Marty accepted the request
        '''
        # Default to plain "stop"
        result = self.client.hold_position(hold_time)
        if result:
            self.client.wait_if_required(hold_time, blocking)
        return result

    def is_paused(self) -> bool:
        '''
        Check if Marty is paused :two:
        Returns:
            True if Marty is paused
        '''
        return self.client.is_paused()

    def is_blocking(self) -> bool:
        '''
        Check the default movement command behaviour of this Marty.  :one: :two:
        Returns:
            `True` if movement commands block by default
        '''
        return self.client.is_blocking()

    def set_blocking(self, blocking: bool):
        '''
        Change whether movement commands default to blocking or non-blocking behaviour
        for this Marty.  :one: :two:

        The blocking behaviour can also be specified on a per-command basis using the
        `blocking=` argument which takes precedence over Marty's overall setting.

        Args:
            blocking: whether or not to block by default
        '''
        self.client.set_blocking(blocking)

    def move_joint(self, joint_name_or_num: Union[int, str], position: int, move_time: int,
                   blocking: Optional[bool] = None) -> bool:
        '''
        Move a specific joint to a position :one: :two:
        Args:
            joint_name_or_num: joint to move, see the Marty.JOINT_IDS dictionary (can be name or number)
            position: angle in degrees
            move_time: how long this movement should last, in milliseconds
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        Returns:
            True if Marty accepted the request
        Raises:
            MartyCommandException if the joint_name_or_num is unknown
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client.preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
        result = self.client.move_joint(jointIDNo, position, move_time)
        if result:
            self.client.wait_if_required(move_time, blocking)
        return result

    def get_joint_position(self, joint_name_or_num: Union[int, str]) -> float:
        '''
        Get the position (angle in degrees) of a joint :two:
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        Returns:
            Angle of the joint in degrees
        Raises:
            MartyCommandException if the joint_name_or_num is unknown            
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client.preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
        return self.client.get_joint_position(jointIDNo)

    def get_joint_current(self, joint_name_or_num: Union[int, str]) -> float:
        '''
        Get the current (in milli-Amps) of a joint :one: :two:
        This can be useful in detecting when the joint is working hard and is related
        to the force which the joint's motor is exerting to stay where it is
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        Returns:
            the current of the joint in milli-Amps (this will be 0 if the joint current is unknown)
        Raises:
            MartyCommandException if the joint_name_or_num is unknown
        '''
        jointIDNo = joint_name_or_num
        if type(joint_name_or_num) is str:
            if joint_name_or_num not in self.JOINT_IDS:
                self.client.preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
        return self.client.get_joint_current(jointIDNo)

    def get_joint_status(self, joint_name_or_num: Union[int, str]) -> int:
        '''
        Get information about a joint :two:
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
                self.client.preException(True)
                raise MartyCommandException("Joint must be one of {}, not '{}'"
                                            "".format(set(self.JOINT_IDS.keys()), joint_name_or_num))
            jointIDNo = self.JOINT_IDS.get(joint_name_or_num, 0)
        return self.client.get_joint_status(jointIDNo)

    def get_distance_sensor(self) -> Union[int, float]:
        '''
        Get the latest value from the distance sensor :one: :two:
        Returns:
            The distance sensor reading. The meaning of the returned value is different 
            between Marty V1 and V2:
                - :one: Returns a raw distance sensor reading as a `float`.
                - :two: Returns the distance in millimeters as `int`.
            Both will return 0 if no distance sensor is found.
        '''
        return self.client.get_distance_sensor()

    def speak(self, words: str = "hello", voice: str = "alto", blocking: Optional[bool] = False) -> bool:
        '''
        Make Marty speak :two:
        Args:
            words: what to say
            voice: 'alto', 'tenor' or 'chipmunk' :two:
            blocking: whether to wait for speech to finish before returning
        Returns:
            True if Marty accepted the request
        '''
        result = self.client.speak(words, voice)
        if result:
            if blocking:
                self.client.wait_if_required(5000, blocking)
        return result

    def foot_on_ground(self, add_on_or_side: str) -> bool:
        '''
        Checks whether the foot is on a surface :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor, name of an IR sensor, `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
        Returns:
            A boolean for whether the addon detects the ground. `True` for ground detected, `False` otherwise.
        '''
        return self.client.foot_on_ground(add_on_or_side)

    def foot_obstacle_sensed(self, add_on_or_side: str) -> bool:
        '''
        Checks whether there is an obstacle in front of the foot :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor, name of an IR sensor, `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
        Returns:
            A boolean for whether the addon detects and obstacle. `True` for obstacle detected, `False` otherwise.
        '''
        return self.client.foot_obstacle_sensed(add_on_or_side)

    def get_obstacle_sensor_reading(self, add_on_or_side: str) -> int:
        '''
        Gets a raw obstacle sensor reading from an IR or color sensor :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor, name of an IR sensor, `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
        Returns:
            Raw reading of obstacle sensor data from the add on.
        '''
        return self.client.get_obstacle_sensor_reading(add_on_or_side)
    
    def get_color_sensor_color(self, add_on_or_side: str) -> int:
        '''
        Gets the colour detected by a colour sensor :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
        Returns:
            one of  "yellow", "green", "blue", "purple", "red", "air", "unclear"
        '''
        return self.client.get_color_sensor_color(add_on_or_side)
    
    def get_color_sensor_hex(self, add_on_or_side: str) -> str:
        '''
        Gets the colour detected by a colour sensor :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
        Returns:
            The hex code of the colour detected by the sensor
        '''
        return self.client.get_color_sensor_hex(add_on_or_side)
    
    def get_color_sensor_value_by_channel(self, add_on_or_side: str, channel: str) -> int:
        '''
        Gets the value of a colour sensor channel :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
            channel: Takes in the name of a channel `'clear'` `'red'`, `'green'`, or `'blue'`
        Returns:
            The value of the channel
        '''
        return self.client.get_color_sensor_value_by_channel(add_on_or_side, channel)

    def get_ground_sensor_reading(self, add_on_or_side: str) -> int:
        '''Gets a raw ground sensor reading from an IR or color sensor :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor, name of an IR sensor, `'left'` for the add on connected to the left foot,
             or `'right'` for the add on connected to the right foot. 
        Returns:
            Raw reading of ground sensor data from the add on.
        '''
        return self.client.get_ground_sensor_reading(add_on_or_side)

    def get_battery_remaining(self) -> float:
        '''
        Get the battery remaining percentage :two:
        Returns:
            The battery remaining capacity in percent
        '''
        return self.client.get_battery_remaining()

    def save_calibration(self) -> bool:
        '''
        Set the current motor positions as the zero positions :one: :two:

        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        return self.client.save_calibration()

    def clear_calibration(self) -> bool:
        '''
        Mark the current calibration as invalid :one: :two:

        This has no immediate physical effect. Marty will still remember the last
        calibration but will report that it needs to be calibrated again. (You may
        notice that a "Calibrate" button appears in the app for example.)
        '''
        return self.client.clear_calibration()

    def is_calibrated(self) -> bool:
        '''
        Check if Marty is calibrated :two:
        '''
        return self.client.is_calibrated()

    def get_robot_status(self) -> Dict:
        '''
        Get status of Marty the Robot :two:
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
        Get information on all of Marty's joints :two:
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
        Get information on Marty's battery and power supply :two:
        Args:
            none
        Returns:
            Dictionary containing:
                "battRemainCapacityPercent": remaining battery capacity in percent
                "battTempDegC": battery temperature in degrees C
                "battRemainCapacityMAH": remaining battery capacity in milli-Amp-Hours
                "battFullCapacityMAH": capacity of the battery when full in milli-Amp-Hours
                "battCurrentMA": current the battery is supplying (or being charged with) milli-Amps
                "power5VOnTimeSecs": number of seconds the power to joints and add-ons has been on
                "powerUSBIsConnected": True if USB is connected
                "power5VIsOn": True if power to the joints and add-ons is turned on

                 Other values for internal use

            **Note:** Some keys may not be included if Marty reports that the
                      corresponding information is not available.
        '''
        return self.client.get_power_status()
    
    def get_add_ons_status(self) -> Dict:
        '''
        Get latest information for all add-ons :two:
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
        Get latest information for a single add-on :two:
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

    def add_on_query(self, add_on_name: str, data_to_write: bytes, num_bytes_to_read: int) -> Dict:
        '''
        Write and read an add-on directly (raw-mode) :two:
        Args:
            add_on_name: name of the add-on (see get_add_ons_status() at the top level or response to
                `addon/list` REST API command)
            data_to_write: can be zero length if nothing is to be written, the first byte will generally
                be the register or opcode of the add-on
            num_bytes_to_read: number of bytes to read from the device - can be zero
        Returns:
            Dict with keys including:
                "rslt" - the result which will be "ok" if the query succeeded
                "dataRead" - the data read from the add-on
        '''
        return self.client.add_on_query(add_on_name, data_to_write, num_bytes_to_read)

    def get_system_info(self) -> Dict:
        '''
        Get information about Marty :two:
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
                "RicHwRevNo": the revision number of the RIC hardware
        '''
        return self.client.get_system_info()

    def set_marty_name(self, name: str) -> bool:
        '''
        Set Marty's name :two:
        Args:
            name to call Marty
        Returns:
            True if successful in setting the name
        '''
        return self.client.set_marty_name(name)

    def get_marty_name(self) -> str:
        '''
        Get Marty's name :two:
        Args:
            none
        Returns:
            the name given to Marty
        '''
        return self.client.get_marty_name()

    def is_marty_name_set(self) -> bool:
        '''
        Check if Marty's name is set :two:
        Args:
            none
        Returns:
            True if Marty's name is set
        '''
        return self.client.is_marty_name_set()

    def get_hw_elems_list(self) -> List:
        '''
        Get a list of all of the hardware elements on Marty :two:
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
        return self.client.get_hw_elems_list()

    def send_ric_rest_cmd(self, ricRestCmd: str) -> None:
        '''
        Send a command in RIC REST format to Marty :two:  

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
        Send a command in RIC REST format to Marty and wait for reply :two:  

        This is a special purpose command which you can use to do advanced
        control of Marty
        Args:
            ricRestCmd: string containing the command to send to Marty
        Returns:
            Dictionary containing the response received from Marty
        '''
        return self.client.send_ric_rest_cmd_sync(ricRestCmd)

    def get_motor_current(self, motor_id: int) -> float:
        '''
        Get current flowing through a joint motor :one: :two:
        Args:
            motor_id, integer >= 0 (non-negative) selects which motor to query
        Returns:
            Instantaneous current sense reading from motor `motor_id`
        '''
        return self.get_joint_current(motor_id)

    def is_conn_ready(self) -> bool:
        '''
        Check if the robot is connected and the connection is ready to accept
        commands :two:
        Args:
            None
        Returns:
            True if the robot is connected and ready
        '''
        return self.client.is_conn_ready()
        
    def disco_off(self, add_on: Union[Disco, str] = Disco.ALL, api = 'led') -> bool:
        '''
        Turn disco add on LEDs off :two:
        Args:
            add_on: add on name of which the function applies to
            api: which API to use, 'raw_query' or 'led'
        Returns:
            True if Marty accepted the request
        '''
        if type(add_on) is str:
            return self.client.disco_off(add_on, api)
        else:
            return self.client.disco_group_operation(self.client.disco_off, add_on.value, {'api':api}, api=api)

    def disco_pattern(self, pattern: int, add_on: Union[Disco, str] = Disco.ALL) -> bool:
        '''
        DEPRECATED: use disco_named_pattern instead
        Turn on a pattern of lights on the disco LED add on :two:
        Args:
            pattern: 1 or 2, pattern of lights that user wants to use
            add_on: add on name of which the function applies to
        Returns:
            True if Marty accepted the request
        '''
        if type(add_on) is str:
            return self.client.disco_pattern(pattern, add_on)
        else:
            return self.client.disco_group_operation(self.client.disco_pattern, add_on.value, {'pattern':pattern}, api='raw_query')

    def disco_named_pattern(self, add_on: str, pattern: str) -> bool:
        '''
        Turn on a named pattern of lights on the disco LED add on :two:
        Args:
            add_on: add on name of which the function applies to
            pattern: name of the pattern to use
        Returns:
            True if Marty accepted the request
        '''
        if type(add_on) is str:
            return self.client.disco_named_pattern(add_on, pattern)
        else:
            return self.client.disco_group_operation(self.client.disco_named_pattern, add_on.value, {'pattern':pattern}, api='led')

    def disco_color(self, color: Union[str, Tuple[int, int, int]] = 'white', 
                    add_on: Union[Disco, str] = Disco.ALL, 
                    region: Union[int, str] = 'all',
                    api = 'led'
                    ) -> bool:
        '''
        Turn on disco add on LED lights to a specific color :two:
        Args:
            color: color to switch the LEDs to; takes in a hex code, RGB tuple of integers between 0-255, 
                   or one of the built in colors: white, red, blue, yellow, green, teal, pink, purple, orange
            add_on: add on name of which the function applies to
            region: 0,1,2; region on the add on
        Returns:
            True if Marty accepted the request
        '''
        if type(add_on) is str:
            if api == 'raw_query':
                return self.client.disco_color(color, add_on, region)
            elif api == 'led':
                return self.client.disco_color_led_api(color, add_on, region)
        else:
            if api == 'raw_query':
                return self.client.disco_group_operation(self.client.disco_color, add_on.value, {'color':color, 'region':region}, api='raw_query')
            elif api == 'led':
                return self.client.disco_group_operation(self.client.disco_color_led_api, add_on.value, {'color':color, 'region':region}, api='led')
                # raise MartyCommandException("Disco LED API not supported for disco group operation. Please use addon name")
    
    def disco_color_specific_led(self, color: Union[str, Tuple[int, int, int]], add_on: str, add_on_who_am_i: str, led_id: int) -> bool:
        '''
        Turn on disco add on specific LED light to a color :two:
        Args:
            color: color to switch the LEDs to; takes in a hex code, RGB tuple of integers between 0-255, 
                   or one of the built in colors: white, red, blue, yellow, green, teal, pink, purple, orange
            add_on: add on name of which the function applies to
            add_on_who_am_i: who am i string of the add on
            led_id: ID of the LED to change
        Returns:
            True if Marty accepted the request
        '''
        return self.client.disco_color_specific_led(color, add_on, add_on_who_am_i, led_id)

    def disco_color_eyepicker(self, colours: Union[str, List[str]], add_on: str) -> bool:
        '''
        Turn on disco add on specific LED lights to specific colors :two:
        Args:
            colours: list of colors to switch the LEDs to; takes in a hex code, the position in the list corresponds to the LED ID
            add_on: add on name of which the function applies to
        Returns:
            True if Marty accepted the request
        '''
        return self.client.disco_color_eyepicker(colours, add_on)

    def rgb_operator(self, r: int, g: int, b: int) -> list[int]:
        '''
        Takes in RGB values and returns them as tuples :one: :two:
        Args:
            r: red value
            g: green value
            b: blue value
        Returns:
            List of RGB values after the operation
        '''
        return (r, g, b)

    def hsv_operator(self, h: int, s: int, v: int) -> list[int]:
        '''
        Takes in HSL values and returns them in RGB tuples :one: :two:
        Args:
            h: hue value
            s: saturation value
            l: lightness value
        Returns:
            List of RGB values after the operation
        '''
        # first make sure s and v are 0-1
        if s > 1:
            s = s / 100
        if v > 1:
            v = v / 100
        h = h % 360
        if h < 0:
            h += 360
        s = max(0, min(s, 1))
        v = max(0, min(v, 1))

        i = int(h // 60)
        f = (h / 60) - i
        p = v * (1 - s)
        q = v * (1 - (s * f))
        t = v * (1 - (s * (1 - f)))

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        elif i == 5:
            r, g, b = v, p, q
        else:
            r, g, b = 0, 0, 0  # Fallback, though this shouldn't happen

        return [int(r * 255), int(g * 255), int(b * 255)]

    def function_led(self, colour: Tuple[int, int, int], breathe: str = "on", breath_ms: int = 1000) -> bool:
        '''
        Turn on function LED light to a color :two:
        Args:
            colour: color to switch the LEDs to; takes in an RGB tuple of integers between 0-255
            breathe: "on"/"breath"
            breath_ms: time in milliseconds for the LED to breath
        Returns:
            True if Marty accepted the request
        '''
        return self.client.function_led(colour, breathe, breath_ms)
    
    def function_led_off(self) -> bool:
        '''
        Turn off function LED light :two:
        Args:
            none
        Returns:
            True if Marty accepted the request
        '''
        return self.client.function_led_off()

    ''' 
    ============================================================
    The following commands are for Marty V1 Only
    ============================================================
    '''

    def enable_motors(self, enable: bool = True, clear_queue: bool = True) -> bool:
        '''
        Toggle power to motors :one:
        Args:
            enable: True/False toggle
            clear_queue: Default True, prevents unfinished but 'muted' motions
                         from jumping as soon as motors are enabled
        '''
        return self.client.enable_motors(enable, clear_queue)

    def enable_safeties(self, enable: bool = True) -> bool:
        '''
        Tell the board to turn on 'normal' safeties :one:
        '''
        return self.client.enable_safeties(enable)

    def fall_protection(self, enable: bool = True) -> bool:
        '''
        Toggle fall protections :one:
        Args:
            enable: True/False toggle
        '''
        return self.client.fall_protection(enable)

    def motor_protection(self, enable: bool = True) -> bool:
        '''
        Toggle motor current protections :one:
        Args:
            enable: True/False toggle
        '''
        return self.client.motor_protection(enable)

    def battery_protection(self, enable: bool = True) -> bool:
        '''
        Toggle low battery protections :one:
        Args:
            enable: True/False toggle
        '''
        return self.client.battery_protection(enable)

    def buzz_prevention(self, enable: bool = True) -> bool:
        '''
        Toggle motor buzz prevention :one:
        Args:
            enable: True/False toggle
        '''
        return self.client.buzz_prevention(enable)

    def lifelike_behaviour(self, enable: bool = True) -> bool:
        '''
        Tell the robot whether it can or can't move now and then in a lifelike way when idle. :one:
        Args:
            enable: True/False toggle
        '''
        return self.client.lifelike_behaviour(enable)

    def ros_command(self, *byte_array: int) -> bool:
        '''
        Low level proxied access to the ROS Serial API between 
        the modem and main controller :one:
        '''
        return self.client.ros_command(*byte_array)

    def keyframe (self, time: float, num_of_msgs: int, msgs) -> List[bytes]:
        '''
        Takes in information about movements and generates keyframes
        returns a list of bytes :one:
        Args:
            time: time (in seconds) taken to complete movement
            num_of_msgs: number of commands sent
            msgs: commands sent in the following format [(ID CMD), (ID CMD), etc...]
        '''
        return self.client.keyframe(time, num_of_msgs, msgs)

    def get_chatter(self) -> bytes:
        '''
        Return chatter topic data (variable length) :one:
        '''
        return self.client.get_chatter()

    def get_firmware_version(self) -> bool:
        '''
        Ask the board to print the firmware version over chatter :one:
        '''
        return self.client.get_firmware_version()

    def _mute_serial(self) -> bool:
        '''
        Mutes the internal serial line on RIC. Depends on platform and API :one:
        NOTE: Once you've done this, the Robot will ignore you until you cycle power.
        '''
        return self.client.mute_serial()

    def ros_serial_formatter(self, topicID: int, send: bool = False, *message: int) -> List[int]:
        '''
        Formats message into ROS serial format and
        returns formatted message as a list :one:  

        Calls ros_command with the processed message if send is True.
        More information about the ROS serial format can be
        found here: http://wiki.ros.org/rosserial/Overview/Protocol
        '''
        return self.client.ros_serial_formatter(topicID, send, message)

    def pinmode_gpio(self, gpio: int, mode: str) -> bool:
        '''
        Configure a GPIO pin :one:
        Args:
            gpio: pin number between 0 and 7
            mode: choose from: 'digital in','analog in' or 'digital out'
        '''
        return self.client.pinmode_gpio(gpio, mode)

    def write_gpio(self, gpio:int, value: int) -> bool:
        '''
        Write a value to a GPIO port :one:
        '''
        return self.client.write_gpio(gpio, value)

    def digitalread_gpio(self, gpio: int) -> bool:
        '''
        Read from GPIO :one:
        Args:
            GPIO pin number, >= 0 (non-negative)
        Returns:
            Returns High/Low state of a GPIO pin
        '''
        return self.client.digitalread_gpio(gpio)

    def set_parameter(self, *byte_array: int) -> bool:
        '''
        Set board parameters :one:
        Args:
            byte_array: a list in the following format [paramID, params]
        '''
        return self.client.set_parameter(byte_array)

    def i2c_write(self, *byte_array: int) -> bool:
        '''
        Write a bytestream to the i2c port. :one:  

        The first byte should be the address, following from that
        the datagram folows standard i2c spec
        '''
        return self.client.i2c_write(*byte_array)

    def i2c_write_to_ric(self, address: int, byte_array: bytes) -> bool:
        '''
        Write a formatted bytestream to the i2c port. :one:  

        The bytestream is formatted in the ROS serial format.

        address: the other device's address
        '''
        return self.client.i2c_write_to_ric(address, byte_array)

    def i2c_write_to_rick(self, address: int, byte_array: bytes) -> bool:
        '''
        Write a formatted bytestream to the i2c port. :one:  

        The bytestream is formatted in the ROS serial format.
        address: the other device's address
        '''
        return self.client.i2c_write_to_ric(address, byte_array)

    def get_battery_voltage(self) -> float:
        '''
        Get the voltage of the battery :one:
        Returns:
            The battery voltage reading as a float in Volts
        '''
        return self.client.get_battery_voltage()

    def hello(self, blocking: Optional[bool] = None) -> bool:
        '''
        Zero joints and wiggle eyebrows :one:
        Args:
            blocking: Blocking mode override; whether to wait for physical movement to
                finish before returning. Defaults to the value returned by `self.is_blocking()`.
        '''
        result = self.client.hello()
        if result:
            self.client.wait_if_required(4000, blocking)
        return result

    def discover(self) -> List[str]:
        '''
        Try and find us some Martys! :one:
        '''
        return self.client.discover()

    ''' 
    ============================================================
    Helper commands that you probably won't need to use directly
    ============================================================
    '''

    def __del__(self) -> None:
        '''
        Marty is stopping
        '''
        self.close()

    def close(self) -> None:
        '''
        Close connection to Marty
        '''
        if self.client:
            self.client.close()

    def register_logging_callback(self, loggingCallback: Callable[[str], None]) -> None:
        '''
        Register a callback function to be called on every log message from RIC. :two:

        Log messages are used mainly for debugging and error reporting.
        Args:
            messageCallback: a callback function (with one string argument - the log message)
        Returns:
            None
        '''
        if self.client:
            self.client.register_logging_callback(loggingCallback)

    def register_publish_callback(self, messageCallback: Callable[[int],None]) -> None:
        '''
        Register a callback function to be called on every message published by RIC. :two:

        RIC publishes information like the accelerometer and joint positions constantly.
        If registered, the callback is called after the message is fully decoded, so a common
        use-case is to check the topic (the int passed to the callback) to see if the information
        is of interest (for example topic == Marty.PUBLISH_TOPIC_ACCELEROMETER if new accelerometer 
        data is available). Then get the changed information using the regular get_accelerometer method
        (or get_joints, etc for other data).
        Args:
            messageCallback: a callback function (with one argument - the topic code of the published 
                    message) that will be called on every message published by RIC.
        Returns:
            None
        '''
        if self.client:
            self.client.register_publish_callback(messageCallback)

    def register_report_callback(self, messageCallback: Callable[[str],None]) -> None:
        '''
        Register a callback function to be called on every report message recieved from RIC. :two:

        Report messages are used for alert conditions such as Falling, Over Current, etc.
        The report message (passed in the callback function str) is a JSON string.
        The elements of the JSON string include:
            msgType: the type of report message (this will be "warn" for all alerts)
            msgBody: the message text (this is "freeFallDet" or "overCurrentDet")
            IDNo: the IDNo of the element that generated the report (the codes for these
                are in the Marty.HW_ELEM_IDS dictionary but additional ones may appear if
                add-ons create warnings - the IDNos of add-ons are not fixed numbers but you
                can see the IDNo of add-ons by using the get_add_ons_status() method)
        Args:
            messageCallback: a callback function (with one string argument) 
                    that will be called on every message published by RIC.
        Returns:
            None
        '''
        if self.client:
            self.client.register_report_callback(messageCallback)

    def get_interface_stats(self) -> Dict:
        '''
        Get interface statistics from Marty. :two:

        This is mainly useful for debugging and troubleshooting of martypy itself.
        Returns:
            A dictionary of interface statistics including:
                roundTripAvgMS: average round trip time for command/response messages in milliseconds
                msgRxRatePS: max number of messages received per second
                msgTxRatePS: max number of messages sent per second
                unmatched: number of unmatched messages
                matched: number of matched messages
                unnumbered: number of unnumbered messages
                timedOut: number of messages that timed out
                uploadBPS: upload speed in bytes per second (for file uploads, etc)
                rxCount: number of messages received
                txCount: number of messages sent
            The dictionary may also include several records of the form:
                <topic>PS: number of messages published on each topic where <topic> is the topic name
                       and can be servos, imu, robot, power or addons
        '''
        return self.client.get_interface_stats()

    def get_test_output(self) -> str:
        '''
        This is only used for self-testing of martypy when the test interface is chosen instead of
        wifi, serial, etc :two:
        '''
        return self.client.get_test_output()

    def send_file(self, filename: str, 
                progress_callback: Callable[[int, int], bool] = None,
                file_dest:str = "fs") -> bool:
        '''
        Send a file to Marty. :two:

        Args:
            filename: the name of the file to send
            progress_callback: callback used to indicate how file send is progressing, callable takes three params
                    which are bytesSent and totalBytes and
                    returns a bool which should be True to continue the file upload or False to abort
            file_dest: "fs" to upload to file system, "ricfw" for new RIC firmware
        Returns:
            True if the file was sent successfully
        Throws:
            OSError: operating system exceptions
            May throw other exceptions so include a general exception handler
        '''
        return self.client.send_file(filename, progress_callback, file_dest)

    def play_mp3(self, filename: str,
                progress_callback: Callable[[int, int], bool] = None) -> bool:
        '''
        Play an mp3 file on the robot. :two:
        Args:
            filename: the name of the mp3 file to play
        Returns:
            True if the file was played successfully
        '''
        return self.client.play_mp3(filename, progress_callback)

    def get_file_list(self) -> List[str]:
        '''
        Get a list of files on the robot. :two:
        Args:
            None
        Returns:
            A list of files on the robot
        '''
        return self.client.get_file_list()

    def delete_file(self, filename: str) -> bool:
        '''
        Delete a file on the robot. :two:
        Args:
            filename: the name of the file to delete
        Returns:
            True if the file was deleted successfully
        '''
        return self.client.delete_file(filename)
