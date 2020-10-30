from martypy.RICROSSerial import RICROSSerial
from typing import Dict, List, Optional, Union
import logging
import time
from .RICProtocols import DecodedMsg, RICProtocols
from .RICInterfaceSerial import RICInterfaceSerial
from .RICHWElems import RICHWElems
from .exceptions import (MartyConnectException,
                         MartyCommandException)

logger = logging.getLogger(__name__)

class SerialClient():
    '''
    Lower level interface class between the `Marty` abstracted
    control class and the RIC serial interface
    '''
    SIDE_CODES = {
        'left'    : 1,
        'right'   : 0,
        'forward' : 3,
        'back'    : 2,
        'auto'    : 0,
    }

    EYE_POSES = {
        'angry'   : 'eyesAngry',
        'excited' : 'eyesExcited',
        'normal'  : 'eyesNormal',
        'wide'    : 'eyesWide',
        'wiggle'  : 'wiggleEyes'
    }

    NOT_IMPLEMENTED_STR = "Unfortunately this Marty doesn't do that"
    
    def __init__(self, client_type: str, loc: str, 
                debug: bool = False, serialBaud: int = None, 
                *args, **kwargs):
        '''
        Initialise connection to remote Marty over a serial port by name 'loc'

        Args:
            client_type: usb (for usb serial port) or alt (for alternate serial port)
            loc: str, must be a serial port
            debug: show Marty logging messages to the log output
            serialBaud: serial baud rate

        Raises:
            MartyConnectException if the serial connection to the host failed
        '''
        if client_type is None or client_type == "usb":
            self.protocol = "overascii"
            self.serialBaud = 115200 if serialBaud is None else serialBaud
        else:
            self.protocol = "plain"
            self.serialBaud = 921600 if serialBaud is None else serialBaud

        self.debug = debug
        self.serialPort = loc
        self.ricIF = RICInterfaceSerial()
        self.lastSubscribedMsgTime = None
        self.maxTimeBetweenPubs = 10
        self.ricHardware = RICHWElems()
        self.isClosing = False

        # Open comms
        try:
            # Connection params
            rifConfig = {
                "serialPort": self.serialPort,
                "serialBaud": self.serialBaud,
                "ifType": self.protocol,
            }
            openOk = self.ricIF.open(rifConfig)
            if not openOk:
                raise MartyConnectException("Failed to open serial port")

        except Exception as excp:
            raise MartyConnectException(str(excp))

        self.ricIF.setDecodedMsgCB(self._rxDecodedMsg)
        self.ricIF.setTimerCB(self._msgTimerCallback)

        if self.debug:
            self.ricIF.setLogLineCB(self._logDebugMsg)

    def start(self):
        '''
        Start
        '''
        self.ricIF.getRICSystemInfo()
        self.ricIF.getRICName()
        self.ricIF.getRICCalibInfo()
        self.ricIF.getHWElemList()

    def close(self):
        '''
        Close interface to RIC
        '''
        self.isClosing = True
        # Stop any publishing messages
        self.ricIF.sendRICRESTCmdFrame('{"cmdName":"subscription","action":"update",' + \
                '"pubRecs":[' + \
                    '{"name":"MultiStatus","rateHz":0},' + \
                    '{"name":"PowerStatus","rateHz":0},' + \
                    '{"name":"AddOnStatus","rateHz":0}' + \
                ']}\0')
        # Allow message to be sent
        time.sleep(0.5)
        # Close the RIC interface (which includes the serial port)
        self.ricIF.close()

    def hello(self) -> bool:
        '''
        Zero joints and wiggle eyebrows
        '''
        return self.ricIF.sendRICRESTURL("traj/getReady")

    def get_ready(self) -> bool:
        '''
        Prepare for motion!
        '''
        return self.ricIF.sendRICRESTURL("traj/getReady")

    def discover(self) -> List[str]:
        '''
        Try and find some Martys!
        '''
        return []

    def stop(self, stopInfo: int) -> bool:
        '''
        Stop motions
        Args:
            stopInfo, int, a member of Marty.STOP_TYPE's values
        Raises:
            MartyCommandException if the stop_type is unknown
        '''
        robotRestCmd = "stop"
        trajCmd = ""
        if stopInfo == 0: robotRestCmd = "stopAfterMove"
        elif stopInfo == 2: robotRestCmd = "panic"
        elif stopInfo == 3: trajCmd = "getReady"
        elif stopInfo == 4 or stopInfo == 5: robotRestCmd = "pause"
        isOk = self.ricIF.sendRICRESTURL("robot/" + robotRestCmd)
        if len(trajCmd) > 0:
            self.ricIF.sendRICRESTURL("traj/" + trajCmd)
        return isOk

    def hold_position(self, hold_time: int) -> bool:
        '''
        Hold at current position
        Args:
            hold_time, time to hold position in milli-seconds
        '''
        isOk = self.ricIF.sendRICRESTURL(f"traj/hold?move_time={hold_time}")

    def move_joint(self, joint_id: int, position: float, move_time: int) -> bool:
        '''
        Move a specific joint to a position
        Args:
            joint_id: a member of Marty.JOINT_IDS values
            position: floating point number in degrees
            move_time: how long this movement should last, in milliseconds
        '''
        return self.ricIF.sendRICRESTURL(f"traj/joint?jointID={joint_id}&angle={position}&moveTime={move_time}")

    def get_joint_position(self, joint_id: Union[int, str]) -> float:
        '''
        Get the position (angle in degrees) of a joint
        Args:
            joint_name_or_num: see the Marty.JOINT_IDS dictionary (can be name or number)
        Returns:
            position of the joint in degrees
            will be 0 if the joint position is unknown
        '''
        return self.ricHardware.getServoPos(joint_id)

    def get_joint_current(self, joint_id: Union[int, str]) -> float:
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
        return self.ricHardware.getServoCurrent(joint_id)

    def get_joint_status(self, joint_id: Union[int, str]) -> int:
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
        return self.ricHardware.getServoFlags(joint_id)

    def lean(self, direction: str, amount: float, move_time: int) -> bool:
        '''
        Lean over in a direction
        Args:
            direction: 'left', 'right', 'forward', 'back', 'auto'
            amount: percentage of normal lean
            move_time: how long this movement should last, in milliseconds
        '''
        try:
            directionNum = self.SIDE_CODES[direction]
        except KeyError:
            self.preException(True)
            raise MartyCommandException("Direction must be one of {}, not '{}'"
                                        "".format(set(self.SIDE_CODES.keys()), direction))
        return self.ricIF.sendRICRESTURL(f"traj/lean?side={directionNum}&leanAngle={amount}&moveTime={move_time}")

    def walk(self, num_steps: int = 2, start_foot:str = 'auto', turn: int = 0, 
                step_length:int = 40, move_time: int = 1500) -> bool:
        '''
        Walking
        Args:
            num_steps: int, how many steps to take
            start_foot: 'left', 'right' or 'auto', start walking with this foot
            turn: How much to turn (-128 to 127). 0 is straight.
            step_length: How far to step (approximately in mm)
            move_time: how long this movement should last, in milliseconds
        '''
        try:
            sideNum = self.SIDE_CODES[start_foot]
        except KeyError:
            raise MartyCommandException("Direction must be one of {}, not '{}'"
                                        "".format(set(self.SIDE_CODES.keys()), start_foot))
        return self.ricIF.sendRICRESTURL(f"traj/step/{num_steps}?side={sideNum}&stepLength={step_length}&turn={turn}&moveTime={move_time}")

    def eyes(self, joint_id: int, pose_or_angle: Union[str, float], move_time: int = 100) -> bool:
        '''
        Move the eyes to a pose or an angle
        Args:
            pose_or_angle: 'angry', 'excited', 'normal', 'wide', 'wiggle' or 
                           angle (in degrees - can be negative),
            move_time, milliseconds
        '''
        if type(pose_or_angle) is str:
            try:
                eyesTrajectory = self.EYE_POSES[pose_or_angle]
            except KeyError:
                raise MartyCommandException("pose must be one of {}, not '{}'"
                                            "".format(set(self.EYE_POSES.keys()), pose_or_angle))
            return self.ricIF.sendRICRESTURL(f"traj/{eyesTrajectory}")
        return self.move_joint(joint_id, pose_or_angle, move_time)

    def kick(self, side: str = 'right', twist: float = 0, move_time: int = 2000) -> bool:
        '''
        Kick with Marty's feet
        Args:
            side: 'left' or 'right', which foot to use
            twist: this parameter is not used (just leave blank or pass 0 value)
            move_time: how long this movement should last, in milliseconds
        '''
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.sendRICRESTURL(f"traj/kick?side={self.SIDE_CODES[side]}&moveTime={move_time}")

    def arms(self, left_angle: float, right_angle: float, move_time: int) -> bool:
        '''
        Move the arms to a position
        Args:
            left_angle: Position of the left arm (-128 to 127)
            right_angle: Position of the right arm (-128 to 127)
            move_time: how long this movement should last, in milliseconds
        '''
        self.move_joint(6, left_angle, move_time)
        return self.move_joint(7, right_angle, move_time)

    def celebrate(self, move_time: int = 4000) -> bool:
        '''
        Do a small celebration
        Args:
            move_time: how long this movement should last, in milliseconds
        '''

        # TODO - add celebrate trajectory to Marty V2
        
        return self.ricIF.sendRICRESTURL("traj/celebrate")

    def circle_dance(self, side: str = 'right', move_time: int = 1500) -> bool:
        '''
        Boogy, Marty!
        '''
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.sendRICRESTURL(f"traj/circle?side={self.SIDE_CODES[side]}&moveTime={move_time}")

    def dance(self, side: str = 'right', move_time: int = 1500) -> bool:
        '''
        Another Boogy, Marty!
        '''
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.sendRICRESTURL(f"traj/dance?side={self.SIDE_CODES[side]}&moveTime={move_time}")

    def wiggle(self, move_time: int = 1500) -> bool:
        '''
        Wiggle Marty!
        '''
        return self.ricIF.sendRICRESTURL(f"traj/wiggle?moveTime={move_time}")

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
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.sendRICRESTURL("traj/sidestep?side={self.SIDE_CODES[side]}&stepLength={step_length}&moveTime={move_time}")

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
        return self.ricIF.sendRICRESTURL(f"filerun/{name_or_freq_start}.raw")

    def pinmode_gpio(self, gpio: int, mode: str) -> bool:
        '''
        Configure a GPIO pin

        gpio: pin number between 0 and 7
        mode: choose from: 'digital in','analog in' or 'digital out'
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def write_gpio(self, gpio: int, value: int) -> bool:
        '''
        Write a value to a GPIO port
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def digitalread_gpio(self, gpio: int) -> bool:
        '''
        Returns:
            Returns High/Low state of a GPIO pin
        Args:
            GPIO pin number, >= 0 (non-negative)
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def i2c_write(self, *byte_array: int) -> bool:
        '''
        Write a bytestream to the i2c port.
        The first byte should be the address, following from that
        the datagram folows standard i2c spec
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def i2c_write_to_ric(self, address: int, byte_array: bytes) -> bool:
        '''
        Write a formatted bytestream to the i2c port.
        The bytestream is formatted in the ROS serial format.

        address: the other device's address
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def get_battery_voltage(self) -> float:
        '''
        Returns:
            The battery voltage reading as a float in Volts
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def get_battery_remaining(self) -> float:
        '''
        Returns:
            The battery remaining capacity in percent
        '''
        powerStatus = self.ricHardware.getPowerStatus()
        return powerStatus.get("remCapPC", 0)

    def get_distance_sensor(self) -> float:
        '''
        Returns:
            The distance sensor reading as a float (raw, no units)
        '''
        # TODO NotImplemented
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def get_accelerometer(self, axis: Optional[str] = None, axisCode: int = 0) -> float:
        '''
        Args:
            axis: (optional) str 'x', 'y' or 'z' - if omitted then return x, y and z values
            axisCode: 0, 1 or 2 depending on axis (0 if axis is omitted)
        Returns:
            If axis is provided then returns the most recently read x, y or z 
                acceleration value - or 0 if no information is available
            If axis is not provided returns a tuple with x, y and z values (which may
                be 0 if no information is available)
        '''
        if axis is None:
            return self.ricHardware.getIMUAll()
        return self.ricHardware.getIMUAxisValue(axisCode)

    def enable_motors(self, enable: bool = True, clear_queue: bool = True) -> bool:
        '''
        Toggle power to motors
        Args:
            enable: True/False toggle
            clear_queue: Default True, prevents unfinished but 'muted' motions
                         from jumping as soon as motors are enabled
        '''
        return True
                  
    def enable_safeties(self, enable: bool = True) -> bool:
        '''
        Tell the board to turn on 'normal' safeties
        '''
        return True

    def fall_protection(self, enable: bool = True) -> bool:
        '''
        Toggle fall protections
        Args:
            enable: True/False toggle
        '''
        return True

    def motor_protection(self, enable: bool = True) -> bool:
        '''
        Toggle motor current protections
        Args:
            enable: True/False toggle
        '''
        return True

    def battery_protection(self, enable: bool = True) -> bool:
        '''
        Toggle low battery protections
        Args:
            enable: True/False toggle
        '''
        return True

    def buzz_prevention(self, enable: bool = True) -> bool:
        '''
        Toggle motor buzz prevention
        Args:
            enable: True/False toggle
        '''
        return True

    def lifelike_behaviour(self, enable: bool = True) -> bool:
        '''
        Tell the robot whether it can or can't move now and then in a lifelike way when idle.
        Args:
            enable: True/False toggle
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def set_parameter(self, *byte_array: int) -> bool:
        '''
        Set board parameters.

        Args:
            byte_array: a list in the following format [paramID, params]
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def save_calibration(self) -> bool:
        '''
        Set the current motor positions as the zero positions
        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def clear_calibration(self) -> bool:
        '''
        Tell the Robot to forget it's calibration
        BE CAREFUL, this can cause unexpected movement or self-interference
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def ros_command(self, *byte_array: int) -> bool:
        '''
        Low level proxied access to the ROS Serial API between
        the modem and main controller
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def keyframe (self, time: float, num_of_msgs: int, msgs) -> List[bytes]:
        '''
        Takes in information about movements and generates keyframes
        returns a list of bytes

        time: time (in seconds) taken to complete movement
        num_of_msgs: number of commands sent
        msgs: commands sent in the following format [(ID CMD), (ID CMD), etc...]
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def get_chatter(self) -> bytes:
        '''
        Return chatter topic data (variable length)
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def get_firmware_version(self) -> bool:
        '''
        Ask the board to print the firmware version over chatter
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def _mute_serial(self) -> bool:
        '''
        Mutes the internal serial line on RIC. Depends on platform and API
        NOTE: Once you've done this, the Robot will ignore you until you cycle power.
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def ros_serial_formatter(self, topicID: int, send: bool = False, *message: int) -> List[int]:
        '''
        Formats message into ROS serial format and
        returns formatted message as a list

        Calls ros_command with the processed message if send is True.

        More information about the ROS serial format can be
        found here: http://wiki.ros.org/rosserial/Overview/Protocol
        '''
        raise MartyCommandException(self.NOT_IMPLEMENTED_STR)

    def is_moving(self) -> bool:
        '''
        Check if Marty is moving

        Args:
            none
        Returns:
            True if Marty is moving
        '''
        return self.ricHardware.getIsMoving()

    def is_paused(self) -> bool:
        '''
        Check if Marty is paused

        Args:
            none
        Returns:
            True if Marty is paused
        '''
        return self.ricHardware.getIsPaused()

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
        return self.ricHardware.getRobotStatus()

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
                "status": joint status flags (see Marty.JOINT_STATUS)
        '''
        return self.ricHardware.getServos()

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
        return self.ricHardware.getPowerStatus()

    def get_addon_info(self) -> Dict:
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
        return self.ricHardware.getPowerStatus()

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
        return self.ricHardware.getAddOns()

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
        return self.ricHardware.getAddOn(add_on_name_or_id)

    def preException(self, isFatal: bool) -> None:
        if isFatal:
            self.ricIF.close()
        logger.debug(f"Pre-exception isFatal {isFatal}")

    def _rxDecodedMsg(self, decodedMsg: DecodedMsg, interface: RICInterfaceSerial):
        if decodedMsg.protocolID == RICProtocols.PROTOCOL_ROSSERIAL:
            # logger.debug(f"ROSSERIAL message received {len(decodedMsg.payload)}")
            self.lastSubscribedMsgTime = time.time()
            if decodedMsg.payload:
                RICROSSerial.decode(decodedMsg.payload, 0, self.ricHardware.updateWithROSSerialMsg)
        elif decodedMsg.protocolID == RICProtocols.PROTOCOL_RICREST:
            logger.debug(f"RIC REST message received {decodedMsg.payload}")

    def _logDebugMsg(self, logMsg: str) -> None:
        logger.debug(logMsg)

    def _msgTimerCallback(self) -> None:
        if self.isClosing:
            return
        if self.lastSubscribedMsgTime is None or \
                    time.time() > self.lastSubscribedMsgTime + self.maxTimeBetweenPubs:
            # Subscribe for publication messages
            self.ricIF.sendRICRESTCmdFrame('{"cmdName":"subscription","action":"update",' + \
                            '"pubRecs":[' + \
                                '{"name":"MultiStatus","rateHz":10.0},' + \
                                '{"name":"PowerStatus","rateHz":1.0},' + \
                                '{"name":"AddOnStatus","rateHz":10.0}' + \
                            ']}\0')
            self.lastSubscribedMsgTime = time.time()
