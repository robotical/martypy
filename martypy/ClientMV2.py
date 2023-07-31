import logging
import os
import time
import re
from typing import Callable, Dict, List, Optional, Union, Tuple
from packaging import version
from .ClientGeneric import ClientGeneric
from .RICCommsSerial import RICCommsSerial
from .RICCommsWiFi import RICCommsWiFi
from .RICCommsTest import RICCommsTest
from .RICProtocols import DecodedMsg, RICProtocols
from .RICROSSerial import RICROSSerial
from .RICInterface import RICInterface
from .RICHWElems import RICHWElems
from .Exceptions import (MartyConnectException,
                         MartyCommandException)

logger = logging.getLogger(__name__)

class ClientMV2(ClientGeneric):
    '''
    Lower level connector to Marty V2
    '''
    def __init__(self,
                method: str,
                locator: str,
                serialBaud: Union[int, None] = None,
                port = 80,
                wsPath = "/ws",
                subscribeRateHz = 10.0,
                ricInterface: Optional[RICInterface] = None,
                *args, **kwargs):
        '''
        Initialise connection to remote Marty
        Args:
            client_type: 'wifi' (for WiFi), 'usb' (for usb serial), 'exp' (for expansion serial),
                'test' (output is available via get_test_output())
            locator: str, ipAddress, hostname, serial-port, name of test file etc
                    depending on method
            serialBaud: serial baud rate
            port: IP port for websockets
            wsPath: path to use for websocket connection
            subscribeRateHz: rate of fastest subscription to events
        Raises:
            MartyConnectException if the connection to the host failed
        '''
        # Call base constructor
        super().__init__(*args, **kwargs)

        # Initialise vars
        self.subscribeRateHz = subscribeRateHz
        self.lastRICSerialMsgTime = None
        self.lastSubscrReqMsgTime = None
        self.maxTimeBetweenPubs = 10
        self.minTimeBetweenSubReqs = 10
        self.max_blocking_wait_time = 120  # seconds
        self.ricHardware = RICHWElems()
        self.isClosing = False
        self.ricSystemInfo = {}
        self.ricHwElemsInfoByIDNo = {}
        self.ricHwElemsList = []
        self.loggingCallback = None
        self.publishedMsgCallback = None
        self.reportMsgCallback = None
        self._initComplete = False
        self.maxWaitForConnReadySecs = 10
        self._minSysVersForSubscribeAPI = "1.0.0"
        self._interfaceMethod = method
        self._numHwStatusRetries = 10
        self._sendFileProgressCB = None
        self._recvFileProgressCB = None
        self._playMP3ProgressCB = None
        # Debug
        self.DEBUG_RECEIVE_PUBLISHED_MSG = False
        self.DEBUG_RECEIVE_RICREST_MSGS = False
        self.DEBUG_RECEIVE_BRIDGE_RICREST_MSGS = False
        self.DEBUG_GET_RIC_VERSION = False
        self.DEBUG_GET_HW_ELEMS_INFO = False
        self.DEBUG_SUBSCRIBE_TO_PUB_MSGS = False
        self.DEBUG_CONNECTION_PROCESS = False

        # Check if we are given a RICInterface
        if ricInterface is None:
            # Handle the method of connection
            if method == "usb" or method == "exp":
                ifType = "overascii" if method == "usb" else "plain"
                if serialBaud is None:
                    serialBaud = 115200 if method == "usb" else 921600
                rifConfig = {
                    "serialPort": locator,
                    "serialBaud": serialBaud,
                    "ifType": ifType,
                }
                self.ricIF = RICInterface(RICCommsSerial())
            elif method == "test":
                rifConfig = {
                    "testFileName": locator
                }
                self.ricIF = RICInterface(RICCommsTest())
            else:
                rifConfig = {
                    "ipAddrOrHostname": locator,
                    "ipPort": port,
                    "wsPath": wsPath,
                    "ifType": "plain"
                }
                self.ricIF = RICInterface(RICCommsWiFi(self._onReconnect))
        else:
            rifConfig = {
                "ipAddrOrHostname": locator,
                "ifType": "plain"
            }
            self.ricIF = ricInterface

        # Debug
        ricConnStartTime = time.time()
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug("Starting to connect to RIC")

        # Open comms
        openOk = self.ricIF.open(rifConfig)
        if not openOk:
            raise MartyConnectException("Failed to open connection")

        # Debug
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug(f"RIC interface connection took {time.time() - ricConnStartTime} seconds")

        # Callbacks
        self.ricIF.setDecodedMsgCB(self._rxDecodedMsg)
        self.ricIF.setTimerCB(self._msgTimerCallback)
        self.ricIF.setLogLineCB(self._logDebugMsg)

    def start(self):
        # Debug
        debugRICOverallStart = time.time()
        debugStartTime = time.time()
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug("Starting to communicate with RIC")

        # Get the version of RIC
        self._getRICVersion()

        # Debug
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug(f"Got RIC version in {time.time() - debugStartTime} seconds")
        debugStartTime = time.time()

        # Get HWElems
        self._updateHwElemsInfo()

        # Debug
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug(f"Got HWElems in {time.time() - debugStartTime} seconds")

        # Now completed init
        self._initComplete = True

        # Debug
        # self._updateHwElemsInfo()

        # Wait for connection to be ready
        waitStartTime = time.time()
        while not self.is_conn_ready():
            if time.time() - waitStartTime > self.maxWaitForConnReadySecs:
                raise MartyConnectException("Connection to Marty not ready")
            time.sleep(0.1)

        # Debug
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug(f"Marty wait for ready time {time.time() - debugStartTime} seconds")

        # A flag is set on the first subscribed message - wait a little longer
        # to ensure that one of each subscribed message type has been received
        time.sleep(0.5)

        # Debug
        if self.DEBUG_CONNECTION_PROCESS:
            logger.debug(f"Marty overall start time {time.time() - debugRICOverallStart} seconds")

    def close(self):
        if self.isClosing:
            return
        self.isClosing = True
        # Send unsubscribe request
        self._unsubscribeFromPubMessages()
        # Close the RIC interface
        self.ricIF.close()

    def wait_if_required(self, expected_wait_ms: int, blocking_override: Union[bool, None]):
        if not self.is_blocking(blocking_override):
            return
        if self.subscribeRateHz <= 0:
            return

        deadline = time.time() + expected_wait_ms/1000 + self.max_blocking_wait_time
        time.sleep(2.5 * 1/self.subscribeRateHz)  # Give Marty time to report it is moving

        # The is_moving flag may be cleared briefly between 2 queued trajectories
        # Robot status may not be available for a while after Marty is turned on / connected to
        while self.is_moving() or self.get_robot_status().get('workQCount', 1) > 0:
            time.sleep(0.2 * 1/self.subscribeRateHz)
            if time.time() > deadline:
                raise TimeoutError("Marty wouldn't stop moving. Are you also controlling it via another method?"
                                   f"{os.linesep}If you issued some very long-running non-blocking commands, "
                                   "try increasing `marty.client.max_blocking_wait_time` (the current value "
                                   f"is {self.max_blocking_wait_time} s)")

    def hello(self) -> bool:
        return self.ricIF.cmdRICRESTRslt("traj/getReady")

    def get_ready(self) -> bool:
        return self.ricIF.cmdRICRESTRslt("traj/getReady")

    def stand_straight(self, move_time: int = 2000) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"traj/standStraight?moveTime={move_time}")

    def discover(self) -> List[str]:
        return []

    def stop(self, stop_type: str, stopCode: int) -> bool:
        robotRestCmd = "stop"
        trajCmd = ""
        if stopCode == 0: robotRestCmd = "stopAfterMove"
        elif stopCode == 2: robotRestCmd = "panic"
        elif stopCode == 3: trajCmd = "getReady"
        elif stopCode == 4 or stopCode == 5: robotRestCmd = "pause"
        isOk = self.ricIF.cmdRICRESTRslt("robot/" + robotRestCmd)
        if len(trajCmd) > 0:
            self.ricIF.cmdRICRESTRslt("traj/" + trajCmd)
        return isOk

    def resume(self) -> bool:
        return self.ricIF.cmdRICRESTRslt("robot/resume")

    def hold_position(self, hold_time: int) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"traj/hold?moveTime={hold_time}")

    def move_joint(self, joint_id: int, position: int, move_time: int) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"traj/joint?jointID={joint_id}&angle={position}&moveTime={move_time}")

    def get_joint_position(self, joint_id: int) -> float:
        return self.ricHardware.getServoPos(joint_id, self.ricHwElemsInfoByIDNo)

    def get_joint_current(self, joint_id: int) -> float:
        return self.ricHardware.getServoCurrent(joint_id, self.ricHwElemsInfoByIDNo)

    def get_joint_status(self, joint_id: int) -> int:
        return self.ricHardware.getServoFlags(joint_id, self.ricHwElemsInfoByIDNo)

    def lean(self, direction: str, amount: Optional[int], move_time: int) -> bool:
        if amount is None:
            amount = 29
        try:
            directionNum = ClientGeneric.SIDE_CODES[direction]
        except KeyError:
            self.preException(True)
            raise MartyCommandException("Direction must be one of {}, not '{}'"
                                        "".format(set(ClientGeneric.SIDE_CODES.keys()), direction))
        return self.ricIF.cmdRICRESTRslt(f"traj/lean?side={directionNum}&leanAngle={amount}&moveTime={move_time}")

    def walk(self, num_steps: int = 2, start_foot:str = 'auto', turn: int = 0,
                step_length:int = 25, move_time: int = 1500) -> bool:
        side_url_param = ''
        if start_foot != 'auto':
            try:
                sideNum = ClientGeneric.SIDE_CODES[start_foot]
            except KeyError:
                raise MartyCommandException("Direction must be one of {}, not '{}'"
                                            "".format(set(ClientGeneric.SIDE_CODES.keys()), start_foot))
            side_url_param = f'&side={sideNum}'
        return self.ricIF.cmdRICRESTRslt(f"traj/step/{num_steps}?stepLength={step_length}&turn={turn}"
                                         f"&moveTime={move_time}" + side_url_param)

    def eyes(self, joint_id: int, pose_or_angle: Union[str, int], move_time: int = 100) -> bool:
        if type(pose_or_angle) is str:
            try:
                eyesTrajectory = ClientGeneric.EYE_POSES[pose_or_angle]
            except KeyError:
                raise MartyCommandException("pose must be one of {}, not '{}'"
                                            "".format(set(ClientGeneric.EYE_POSES.keys()), pose_or_angle))
            return self.ricIF.cmdRICRESTRslt(f"traj/{eyesTrajectory}")
        return self.move_joint(joint_id, int(pose_or_angle), move_time)

    def kick(self, side: str = 'right', twist: int = 0, move_time: int = 2500) -> bool:
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.cmdRICRESTRslt(f"traj/kick?side={ClientGeneric.SIDE_CODES[side]}&moveTime={move_time}&turn={twist}")

    def arms(self, left_angle: int, right_angle: int, move_time: int) -> bool:
        self.move_joint(6, left_angle, move_time)
        return self.move_joint(7, right_angle, move_time)

    def celebrate(self, move_time: int = 4000) -> bool:

        # TODO - add celebrate trajectory to Marty V2
        return self.ricIF.cmdRICRESTRslt(f"traj/wiggle?moveTime={move_time}")

    def circle_dance(self, side: str = 'right', move_time: int = 2500) -> bool:
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.cmdRICRESTRslt(f"traj/circle?side={ClientGeneric.SIDE_CODES[side]}&moveTime={move_time}")

    def dance(self, side: str = 'right', move_time: int = 3000) -> bool:
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.cmdRICRESTRslt(f"traj/dance?side={ClientGeneric.SIDE_CODES[side]}&moveTime={move_time}")

    def wiggle(self, move_time: int = 4000) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"traj/wiggle?moveTime={move_time}")

    def sidestep(self, side: str, steps: int = 1, step_length: int = 35,
            move_time: int = 1000) -> bool:
        if side != 'right' and side != 'left':
            raise MartyCommandException("side must be one of 'right' or 'left', not '{}'"
                                        "".format(side))
        return self.ricIF.cmdRICRESTRslt(f"traj/sidestep/{steps}?side={ClientGeneric.SIDE_CODES[side]}"
                                         f"&stepLength={step_length}&moveTime={move_time}")

    def set_volume(self, volume: int) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"audio/vol/{volume}")

    def get_volume(self) -> int:
        result = self.ricIF.cmdRICRESTURLSync("audio/vol")
        if result.get("rslt", "") == "ok":
            return result.get("volPC", 0)
        return 0

    def play_sound(self, name_or_freq_start: Union[str,float],
            freq_end: Optional[float] = None,
            duration: Optional[int] = None) -> bool:
        if type(name_or_freq_start) is not str:
            raise MartyCommandException("name_or_freq_start must be a string")
        if name_or_freq_start.lower().endswith(".mp3"):
            return self.play_mp3(str(name_or_freq_start), self.ricIF)
        if not name_or_freq_start.lower().endswith(".raw"):
            name_or_freq_start += ".raw"
        return self.ricIF.cmdRICRESTRslt(f"filerun/{name_or_freq_start}")

    def pinmode_gpio(self, gpio: int, mode: str) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def write_gpio(self, gpio: int, value: int) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def digitalread_gpio(self, gpio: int) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def i2c_write(self, *byte_array: int) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def i2c_write_to_ric(self, address: int, byte_array: bytes) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def get_battery_voltage(self) -> float:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def get_battery_remaining(self) -> float:
        powerStatus = self.ricHardware.getPowerStatus()
        return powerStatus.get("battRemainCapacityPercent", 0)

    def get_distance_sensor(self) -> int:
        for attached_add_on in self.get_add_ons_status().values():
            if type(attached_add_on) == dict and attached_add_on['whoAmI'] == 'VCNL4200':
                distance_bytes = attached_add_on['data'][1:3]
                distance = int.from_bytes(distance_bytes, 'big')
                return distance
        return 0

    def _index_data_color_ir(self, attached_add_on: Dict[str, str]) -> list:
        '''
        Parses data of passed-in color or IR sensor :two:
        Args:
            attached_add_on: Name of IR or color sensor add on
        Returns:
            A tuple with three integers of data (detection byte, obstacle value, ground value)
            and a string of whether the sensor is a default 'left' or 'right' add on
        '''
        if attached_add_on['whoAmI'] == 'IRFoot':
            detection_flags = attached_add_on['data'][1]
            obstacle_data_raw = int.from_bytes(attached_add_on['data'][2:4], 'big')
            ground_data_raw = int.from_bytes(attached_add_on['data'][4:6], 'big')
            return (detection_flags, obstacle_data_raw, ground_data_raw), 'right'
        if attached_add_on['whoAmI'] == 'coloursensor':
            detection_flags = attached_add_on['data'][6]
            obstacle_data_raw = int.from_bytes(attached_add_on['data'][8:10], 'big')
            ground_data_raw = attached_add_on['data'][2]
            return (detection_flags, obstacle_data_raw, ground_data_raw), 'left'
        return []

    def _get_obstacle_and_ground_raw_data(self, add_on_or_side: str) -> list:
        '''
        Finds the wanted color or IR sensor and gets the parsed obstacle and ground data :two:
        Args:
            add_on_or_side: Takes in the name of a color sensor, name of an IR
            sensor, `'left'` for the add on connected to the left foot,
            or `'right'` for the add on connected to the right foot
        Returns:
            A tuple of the detection byte, obstacle reading, and ground reading of the add on
        '''
        sensor_whoamis = {'IRFoot', 'coloursensor'}
        sensor_data = {'left': [], 'right': []}
        sensor_possible_names = {
            'left': ['LeftColorSensor', 'LeftIRFoot'],
            'right': ['RightIRFoot', 'RightColorSensor']
        }
        addon_names = sensor_possible_names.get(add_on_or_side, [])

        # There may be a situation just after connecting to RIC where publication messages from the addon
        # have not yet been received so we need to wait for them to be received before we can parse them
        addon_statuses = {}.values()
        for retryLoop in range(10):
            addon_statuses = self.get_add_ons_status().values()
            if len(addon_statuses) != 0:
                break
            time.sleep(0.1)
        if len(addon_statuses) == 0:
            raise MartyCommandException("No add-ons found")

        # Get the add-on values
        for attached_add_on in addon_statuses:
            if type(attached_add_on) == dict and attached_add_on.get('whoAmI','') in sensor_whoamis:
                obstacle_and_ground_data, side = self._index_data_color_ir(attached_add_on)
                if attached_add_on['name'] in addon_names:
                    return obstacle_and_ground_data
                else:
                    sensor_data[side].append(obstacle_and_ground_data)
        if len(sensor_data[add_on_or_side.lower()]) == 1:
            return sensor_data[add_on_or_side.lower()][0]
        elif add_on_or_side.lower() == 'left' or add_on_or_side.lower() == 'right':
            raise MartyCommandException(
                f"Marty could not find a {add_on_or_side} sensor. "
                "Please make sure your add ons are plugged in and named correctly"
            )
        else:
            raise MartyCommandException(
                f"The add on '{add_on_or_side}' is not a valid add on for obstacle and ground sensing."
                "Please make sure to pass in the name of an IR sensor or Color sensor."
            )

    def foot_on_ground(self, add_on_or_side: str) -> bool:
        raw_data = self._get_obstacle_and_ground_raw_data(add_on_or_side)
        if len(raw_data) > 0:
            return (raw_data[0] & 0b10) == 0b00
        return False

    def foot_obstacle_sensed(self, add_on_or_side: str) -> bool:
        raw_data = self._get_obstacle_and_ground_raw_data(add_on_or_side)
        if len(raw_data) > 0:
            return (raw_data[0] & 0b1) == 0b1
        return False

    def get_obstacle_sensor_reading(self, add_on_or_side: str) -> int:
        raw_data = self._get_obstacle_and_ground_raw_data(add_on_or_side)
        if len(raw_data) > 1:
            return raw_data[1]
        return 0

    def get_ground_sensor_reading(self, add_on_or_side: str) -> int:
        raw_data = self._get_obstacle_and_ground_raw_data(add_on_or_side)
        if len(raw_data) > 2:
            return raw_data[2]
        return 0

    def get_accelerometer(self, axis: Optional[str] = None, axisCode: int = 0) -> float | Tuple[float,float,float]:
        if axis is None:
            return self.ricHardware.getIMUAll()
        return self.ricHardware.getIMUAxisValue(axisCode)

    def enable_motors(self, enable: bool = True, clear_queue: bool = True) -> bool:
        return True

    def enable_safeties(self, enable: bool = True) -> bool:
        return True

    def fall_protection(self, enable: bool = True) -> bool:
        return True

    def motor_protection(self, enable: bool = True) -> bool:
        return True

    def battery_protection(self, enable: bool = True) -> bool:
        return True

    def buzz_prevention(self, enable: bool = True) -> bool:
        return True

    def lifelike_behaviour(self, enable: bool = True) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def set_parameter(self, *byte_array: int) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def save_calibration(self) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"calibrate/set")

    def clear_calibration(self) -> bool:
        return self.ricIF.cmdRICRESTRslt(f"calibrate/setFlag/0")

    def is_calibrated(self) -> bool:
        result = self.ricIF.cmdRICRESTURLSync("calibrate")
        if result.get("rslt", "") == "ok":
            return result.get("calDone", 0) != 0
        return False

    def ros_command(self, *byte_array: int) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def keyframe (self, time: float, num_of_msgs: int, msgs) -> List[bytes]:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def get_chatter(self) -> bytes:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def get_firmware_version(self) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def _mute_serial(self) -> bool:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def ros_serial_formatter(self, topicID: int, send: bool = False, *message: int) -> List[int]:
        raise MartyCommandException(ClientGeneric.NOT_IMPLEMENTED)

    def is_moving(self) -> bool:
        return self.ricHardware.getIsMoving()

    def is_paused(self) -> bool:
        return self.ricHardware.getIsPaused()

    def get_robot_status(self) -> Dict:
        return self.ricHardware.getRobotStatus()

    def get_joints(self) -> Dict:
        return self.ricHardware.getServos(self.ricHwElemsInfoByIDNo)

    def get_power_status(self) -> Dict:
        return self.ricHardware.getPowerStatus()

    def get_add_ons_status(self) -> Dict:
        return self.ricHardware.getAddOns(self.ricHwElemsInfoByIDNo)

    def get_add_on_status(self, add_on_name_or_id: Union[int, str]) -> Dict:
        return self.ricHardware.getAddOn(add_on_name_or_id, self.ricHwElemsInfoByIDNo)

    def add_on_query(self, add_on_name: str, data_to_write: bytes, num_bytes_to_read: int) -> Dict:
        return self.ricIF.addOnQueryRaw(add_on_name, data_to_write, num_bytes_to_read)

    def get_system_info(self) -> Dict:
        return self.ricSystemInfo

    def set_marty_name(self, name: str) -> bool:
        escapedName = name.replace('"', '').replace('\n','')
        return self.ricIF.cmdRICRESTRslt(f"friendlyname/{escapedName}")

    def get_marty_name(self) -> str:
        result = self.ricIF.cmdRICRESTURLSync("friendlyname")
        if result.get("rslt", "") == "ok":
            return result.get("friendlyName", "Marty")
        return "Marty"

    def is_marty_name_set(self) -> bool:
        result = self.ricIF.cmdRICRESTURLSync("friendlyname")
        if result.get("rslt", "") == "ok":
            return result.get("friendlyNameIsSet", 0) != 0
        return False

    def get_hw_elems_list(self) -> List:
        self._updateHwElemsInfo()
        return self.ricHwElemsList

    def send_ric_rest_cmd(self, ricRestCmd: str) -> None:
        self.ricIF.sendRICRESTURL(ricRestCmd)

    def send_ric_rest_cmd_sync(self, ricRestCmd: str) -> Dict:
        return self.ricIF.cmdRICRESTURLSync(ricRestCmd)

    def is_conn_ready(self) -> bool:
        if not self.ricIF.isOpen():
            return False
        return self._initComplete and ((self.lastRICSerialMsgTime is not None) or (self.subscribeRateHz == 0) or (len(self.ricHwElemsList) < 10))

    def _is_valid_disco_addon(self, add_on: str) -> bool:
        disco_whoamis = {"LEDfoot", "LEDarm", "LEDeye"}
        for attached_add_on in self.get_add_ons_status().values():
            if type(attached_add_on) == dict and attached_add_on['name'] == add_on:
                if attached_add_on['whoAmI'] in disco_whoamis:
                    return True
                else:
                    raise MartyCommandException(f"The add on name: '{add_on}' is not a valid disco add on. "
                                                "Please check the add on name in the scratch app -> configure -> add ons")
        raise MartyCommandException(f"The add on name '{add_on}' is not a valid add on. Please check the add on "
                                    "name in the scratch app -> configure -> add ons")

    def disco_off(self, add_on: str) -> bool:
        if self._is_valid_disco_addon(add_on):
            response = self.add_on_query(add_on, bytes.fromhex('01'), 0)
            return response.get("rslt", "") == "ok"
        return False

    def disco_pattern(self, pattern: int, add_on: str) -> bool:
        patternStr = ""
        if pattern == 1:
            patternStr = '10'
        elif pattern == 2:
            patternStr = '11'
        else:
            raise Exception("Pattern must be 1 or 2")
        if self._is_valid_disco_addon(add_on):
            response = self.add_on_query(add_on, bytes.fromhex(patternStr), 0)
            return response.get("rslt", "") == "ok"
        return False

    def _region_to_bytes(self, region: Union[str, int]) -> bytes:
        regionTuple = ()
        if region == 'all':
            regionTuple = (2,)
        else:
            regionTuple = (4, int(region))
        return bytes(regionTuple)

    def _downscale_color(self, color: Union[tuple, bytes]):
        return bytes(c//25 for c in color)

    def _is_valid_color_hex(self, color_hex: str) -> bool:
        hex_pattern = re.compile("^([A-Fa-f0-9]{6})$")
        return bool(hex_pattern.match(color_hex))

    def _parse_color_hex(self, color_hex: str, region: Union[str, int]) -> bytes:
        input_color = color_hex
        color_hex = color_hex.lstrip('#')
        if self._is_valid_color_hex(color_hex):
            color_bytes = bytes.fromhex(color_hex)
        else:
            raise MartyCommandException(f"The string '{input_color}' is not a valid hex color code or default color")
        return color_bytes

    def disco_color(self, color: Union[str, Tuple[int, int, int]], add_on: str, region: Union[int, str]) -> bool:
        default_colors = {
            'white'  : 'FFFFFF',
            'red'    : 'FF0000',
            'blue'   : '0000FF',
            'yellow' : 'FFFF00',
            'green'  : '008000',
            'teal'   : '008080',
            'pink'   : 'eb1362',
            'purple' : '7800c8',
            'orange' : '961900'
        }
        if type(color) is str:
            colorStr = default_colors.get(color.lower(), color)
            colorTupleOrBytes = self._parse_color_hex(colorStr, region)
        elif type(color) is tuple:
            if len(color) != 3:
                raise MartyCommandException(f'RGB tuple must be 3 numbers, instead of: {color}. Please enter a valid color.')
            colorTupleOrBytes = color
        else:
            raise MartyCommandException(f"Color must be of string or tuple form, not {type(color)}")
        colorBytes = self._downscale_color(colorTupleOrBytes)
        regionBytes = self._region_to_bytes(region)
        command = regionBytes + colorBytes
        if self._is_valid_disco_addon(add_on):
            response = self.add_on_query(add_on, command, 0)
            return response.get("rslt", "") == "ok"
        return False

    def disco_group_operation(self, disco_operation: Callable, whoamis: set, operation_kwargs: dict) -> bool:
        '''
        Calls disco operations in groups for multiple add ons :two:
        Args:
            disco_operation: function for disco add on
            whoami_type_codes: the add ons that the function applies to
            operation_kwargs: additional arguments that need to be passed into the operation
        Returns:
            True if Marty accepted all requests
        '''
        result = True
        for attached_add_on in self.get_add_ons_status().values():
            if type(attached_add_on) == dict and attached_add_on['whoAmI'] in whoamis:
                addon_name = attached_add_on['name']
                result = result and disco_operation(add_on=addon_name, **operation_kwargs)
        return result

    def register_logging_callback(self, loggingCallback: Callable[[str],None]) -> None:
        '''
        Register a callback function to be called on every log message from RIC.
        Log messages are used mainly for debugging and error reporting.
        Args:
            messageCallback: a callback function (with one string argument - the log message)
        Returns:
            None
        '''
        self.loggingCallback = loggingCallback

    def register_publish_callback(self, messageCallback: Callable[[int],None]) -> None:
        '''
        Register a callback function to be called on every message published by RIC.
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
        self.publishedMsgCallback = messageCallback

    def register_report_callback(self, messageCallback: Callable[[str],None]) -> None:
        '''
        Register a callback function to be called on every report message recieved from RIC.
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
        self.reportMsgCallback = messageCallback

    def get_interface_stats(self) -> Dict:
        ricIFStats = self.ricIF.getStats()
        publishInfo = self.ricHardware.getPublishStats()
        ricIFStats.update(publishInfo)
        return ricIFStats

    def preException(self, isFatal: bool) -> None:
        if isFatal:
            self.ricIF.close()
        logger.warning(f"Pre-exception isFatal {isFatal}")

    def _rxDecodedMsg(self, decodedMsg: DecodedMsg, interface: RICInterface):
        if decodedMsg.protocolID == RICProtocols.PROTOCOL_ROSSERIAL:
            if self.DEBUG_RECEIVE_PUBLISHED_MSG:
                logger.debug(f"ROSSERIAL message received {len(decodedMsg.payload) if decodedMsg.payload else 0}")
            self.lastRICSerialMsgTime = time.time()
            if decodedMsg.payload:
                RICROSSerial.decode(decodedMsg.payload, 0, self._rxPublishedMsg)
        elif decodedMsg.protocolID == RICProtocols.PROTOCOL_RICREST:
            if self.DEBUG_RECEIVE_RICREST_MSGS:
                logger.debug(f"RICREST message received {decodedMsg.payload}")
            # Callback for REPORT messages
            if (self.reportMsgCallback is not None) and (decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_REPORT) and (decodedMsg.payload is not None):
                try:
                    self.reportMsgCallback(decodedMsg.payload.decode("utf-8"))
                except:
                    logger.exception("Report callback failed:")
        elif decodedMsg.protocolID == RICProtocols.PROTOCOL_BRIDGE_RICREST:
            if self.DEBUG_RECEIVE_BRIDGE_RICREST_MSGS:
                logger.debug(f"BRIDGE_RICREST message received {decodedMsg.payload}")
        else:
            logger.info(f"RIC UNKNOWN message received {decodedMsg.payload}")
            pass

    def _rxPublishedMsg(self, topicID: int, payload: bytes):
        # Decode the message
        self.ricHardware.updateWithROSSerialMsg(topicID, payload)
        # Callback on published messages
        if self.publishedMsgCallback is not None:
            try:
                self.publishedMsgCallback(topicID)
            except:
                logger.exception("Publish callback failed:")

    def _logDebugMsg(self, logMsg: str) -> None:
        if self.loggingCallback:
            try:
                self.loggingCallback(logMsg)
            except:
                logger.exception("Logging callback failed:")

    def _msgTimerCallback(self) -> None:
        if self.isClosing:
            return
        self._subscribeToPubMessages(False)

    def _getRICVersion(self) -> bool:
        # Retries here to allow for baud-rate changes, etc
        for retries in range(self._numHwStatusRetries):
            # logger.debug(f"_getRICVersion attempt {retries+1}")
            self.ricSystemInfo = self.ricIF.cmdRICRESTURLSync("v")
            if self.ricSystemInfo.get("rslt", "") == "ok":
                break
        if self.DEBUG_GET_RIC_VERSION:
            logger.debug(f"_getRICVersion rslt {self.ricSystemInfo.get('rslt', '')} self.ricSystemInfo {self.ricSystemInfo}")
        return self.ricSystemInfo.get("rslt", "") == "ok"

    def _updateHwElemsInfo(self):
        hwElemsInfo = self.ricIF.cmdRICRESTURLSync("hwstatus")
        if hwElemsInfo.get("rslt", "") == "ok":
            self.ricHwElemsList = hwElemsInfo.get("hw", [])
            self.ricHwElemsInfoByIDNo = {}
            for el in self.ricHwElemsList:
                if "IDNo" in el:
                    self.ricHwElemsInfoByIDNo[el["IDNo"]] = el
            if self.DEBUG_GET_HW_ELEMS_INFO:
                logger.debug(f"_updateHwElemsInfo found {len(self.ricHwElemsList)} elems")

    def get_test_output(self) -> dict:
        return self.ricIF.getTestOutput()

    def _systemVersionGtEq(self, compareToVersion):
        if self.ricSystemInfo is None:
            return False
        versInfo = self.ricSystemInfo.get("SystemVersion","0.0.0")
        return version.parse(versInfo) >= version.parse(compareToVersion)

    def _subscribeToPubMessages(self, forceResubscribe: bool):
        versOk = self._systemVersionGtEq(self._minSysVersForSubscribeAPI)
        timeForSubscr = self.lastRICSerialMsgTime is None or time.time() > self.lastRICSerialMsgTime + self.maxTimeBetweenPubs
        resubscrReqd = self.lastSubscrReqMsgTime is None or time.time() > self.lastSubscrReqMsgTime + self.minTimeBetweenSubReqs
        if versOk and self._initComplete and self.subscribeRateHz != 0 and (forceResubscribe or (timeForSubscr and resubscrReqd)):
            # Subscribe for publication messages
            if self.DEBUG_SUBSCRIBE_TO_PUB_MSGS:
                logger.debug(f"Subscribe to published messages")
            self.ricIF.sendRICRESTCmdFrame('{"cmdName":"subscription","action":"update",' + \
                            '"pubRecs":[' + \
                                '{' + f'"name":"MultiStatus","rateHz":{self.subscribeRateHz},' + '}' + \
                                '{"name":"PowerStatus","rateHz":1.0},' + \
                                '{' + f'"name":"AddOnStatus","rateHz":{self.subscribeRateHz}' + '}' + \
                            ']}')
            self.lastSubscrReqMsgTime = time.time()

    def _unsubscribeFromPubMessages(self):
        # Send unsubscribe request
        self.ricIF.sendRICRESTCmdFrame('{"cmdName":"subscription","action":"update",' + \
            '"pubRecs":[' + \
                '{"name":"MultiStatus","rateHz":0},' + \
                '{"name":"PowerStatus","rateHz":0},' + \
                '{"name":"AddOnStatus","rateHz":0}' + \
            ']}')
        # Allow message to be sent
        time.sleep(0.5)

    def _onReconnect(self):
        self._subscribeToPubMessages(True)

    def _sendFileProgressAdapter(self, fileSize: int, bytesSent: int, ricInterface: RICInterface) -> bool:
        if self._sendFileProgressCB:
            return self._sendFileProgressCB(fileSize, bytesSent)
        return True

    def send_file(self, filename: str,  
                progress_callback: Union[Callable[[int, int], bool], None] = None,
                file_dest:str = "fs") -> bool:
        self._sendFileProgressCB = progress_callback
        return self.ricIF.sendFile(filename, self._sendFileProgressAdapter, file_dest)

    def _recvFileProgressAdapter(self, fileSize: int, bytesSent: int, ricInterface: RICInterface) -> bool:
        if self._recvFileProgressCB:
            return self._recvFileProgressCB(fileSize, bytesSent)
        return True
    
    def get_file_contents(self, filename: str,
                progress_callback: Union[Callable[[int, int], bool], None] = None,
                file_src: str = 'fs') -> bytes | None:
        self._recvFileProgressCB = progress_callback
        return self.ricIF.getFileContents(filename, self._recvFileProgressAdapter, file_src)
    
    def _playMP3ProgressAdapter(self, fileSize: int, bytesSent: int, ricInterface: RICInterface) -> bool:
        if self._playMP3ProgressCB:
            return self._playMP3ProgressCB(fileSize, bytesSent)
        return True

    def play_mp3(self, filename: str, ricInterface: RICInterface,
                progress_callback: Union[Callable[[int, int], bool], None] = None) -> bool:
        self._playMP3ProgressCB = progress_callback
        return self.ricIF.streamSoundFile(filename, "streamaudio", self._playMP3ProgressAdapter)

    def get_file_list(self) -> List[str]:
        result = self.ricIF.cmdRICRESTURLSync("filelist", timeOutSecs=5)
        if result.get("rslt", "") == "ok":
            return result.get("files", [])
        return []

    def delete_file(self, filename: str) -> bool:
        result = self.ricIF.cmdRICRESTURLSync(f"filedelete/local/{filename}", timeOutSecs=5)
        return result.get("rslt", "") == "ok"
