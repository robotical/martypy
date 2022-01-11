'''
RICROSSerial
'''
import logging
import math
import struct
from typing import Callable, Dict, List, Tuple

logger = logging.getLogger(__name__)

class RICROSSerial:

    # ROSSerial ROSTopics
    ROSTOPIC_V2_SMART_SERVOS = 120
    ROSTOPIC_V2_ACCEL = 121
    ROSTOPIC_V2_POWER_STATUS = 122
    ROSTOPIC_V2_ADDONS = 123
    ROSTOPIC_V2_ROBOT_STATUS = 124

    # ROSSerial message format
    RS_MSG_MIN_LENGTH = 8
    RS_MSG_LEN_LOW_POS = 2
    RS_MSG_LEN_HIGH_POS = 3
    RS_MSG_TOPIC_ID_LOW_POS = 5
    RS_MSG_TOPIC_ID_HIGH_POS = 6
    RS_MSG_PAYLOAD_POS = 7

    # Max payload length
    MAX_VALID_PAYLOAD_LEN = 1000

    # V2 ROSTOPIC SMART_SERVOS message layout
    ROS_SMART_SERVOS_MAX_NUM_SERVOS = 15
    ROS_SMART_SERVOS_ATTR_GROUP_BYTES = 6
    ROS_SMART_SERVOS_ATTR_ID_IDX = 0
    ROS_SMART_SERVOS_ATTR_SERVO_POS_IDX = 1
    ROS_SMART_SERVOS_ATTR_MOTOR_CURRENT_IDX = 3
    ROS_SMART_SERVOS_ATTR_STATUS_IDX = 5
    ROS_SMART_SERVOS_INVALID_POS = -32768
    ROS_SMART_SERVOS_INVALID_CURRENT = -32768

    # V2 ROSTOPIC ACCEL message layout
    ROS_ACCEL_BYTES = 14
    ROS_ACCEL_POS_X = 0
    ROS_ACCEL_POS_Y = 4
    ROS_ACCEL_POS_Z = 8
    ROS_ACCEL_POS_IDNO = 12
    ROS_ACCEL_POS_FLAGS = 13

    # V2 ROSTOPIC POWER STATUS message layout
    ROS_POWER_STATUS_BYTES = 13
    ROS_POWER_STATUS_REMCAPPC = 0
    ROS_POWER_STATUS_BATTTEMPC = 1
    ROS_POWER_STATUS_REMCAPMAH = 2
    ROS_POWER_STATUS_FULLCAPMAH = 4
    ROS_POWER_STATUS_CURRENTMA = 6
    ROS_POWER_STATUS_5V_ON_SECS = 8
    ROS_POWER_STATUS_POWERFLAGS = 10
    ROS_POWER_STATUS_FLAGBIT_USB_POWER = 0
    ROS_POWER_STATUS_FLAGBIT_5V_ON = 1
    ROS_POWER_STATUS_IDNO = 12

    # V2 ROSTOPIC ROBOT STATUS message layout
    ROS_ROBOT_STATUS_BYTES = 24
    ROS_ROBOT_STATUS_BYTES_MINIMAL = 2
    ROS_ROBOT_STATUS_MOTION_FLAGS = 0
    ROS_ROBOT_STATUS_IS_MOVING_MASK = 0x01
    ROS_ROBOT_STATUS_IS_PAUSED_MASK = 0x02
    ROS_ROBOT_STATUS_FW_UPDATE_MASK = 0x04
    ROS_ROBOT_STATUS_QUEUED_WORK_COUNT = 1
    ROS_ROBOT_STATUS_HEAP_FREE_POS = 2
    ROS_ROBOT_STATUS_HEAP_FREE_BYTES = 4
    ROS_ROBOT_STATUS_HEAP_MIN_POS = 6
    ROS_ROBOT_STATUS_HEAP_MIN_BYTES = 4
    ROS_ROBOT_STATUS_INDICATORS_POS = 10
    ROS_ROBOT_STATUS_INDICATOR_BYTES = 4
    ROS_ROBOT_STATUS_INDICATORS_NUM = 3
    ROS_ROBOT_STATUS_SYSMOD_LOOPMS_AVG_POS = 22
    ROS_ROBOT_STATUS_SYSMOD_LOOPMS_AVG_SIZE = 1
    ROS_ROBOT_STATUS_SYSMOD_LOOPMS_MAX_POS = 23
    ROS_ROBOT_STATUS_SYSMOD_LOOPMS_MAX_SIZE = 1

    # V2 ROSTOPIC ADDONS message layout
    ROS_ADDONS_MAX_NUM_ADDONS = 15
    ROS_ADDON_GROUP_BYTES = 12
    ROS_ADDON_IDNO_POS = 0
    ROS_ADDON_FLAGS_POS = 1
    ROS_ADDON_DATAVALID_FLAG_MASK = 0x80
    ROS_ADDON_STATUS_POS = 2
    ROS_ADDON_STATUS_BYTES = 10

    @classmethod
    def decode(cls, rosSerialMsg: bytes, startPos: int, elemDecodeCB: Callable[[int,bytes],None]) -> None:

        # Payload may contain multiple ROSSerial messages
        msgPos = startPos
        while True:
            remainingMsgLen = len(rosSerialMsg) - msgPos

            # logger.debug(f'ROSSerial Decode {remainingMsgLen}')

            if remainingMsgLen < cls.RS_MSG_MIN_LENGTH:
                break

            # Extract header
            payloadLength = rosSerialMsg[msgPos + cls.RS_MSG_LEN_LOW_POS] + \
                    rosSerialMsg[msgPos + cls.RS_MSG_LEN_HIGH_POS] * 256
            topicID = rosSerialMsg[msgPos + cls.RS_MSG_TOPIC_ID_LOW_POS] + \
                rosSerialMsg[msgPos + cls.RS_MSG_TOPIC_ID_HIGH_POS] * 256

            # logger.debug(f'ROSSerial len {payloadLength} topic {topicID}')

            # Check max length
            if payloadLength < 0 or payloadLength > cls.MAX_VALID_PAYLOAD_LEN:
                break

            # Check min length
            if len(rosSerialMsg) < payloadLength + cls.RS_MSG_MIN_LENGTH:
                break

            # Extract payload
            payload = rosSerialMsg[msgPos + cls.RS_MSG_PAYLOAD_POS : msgPos + cls.RS_MSG_PAYLOAD_POS + payloadLength]
            # logger.debug('ROSSerial {}'.format(''.join('{:02x}'.format(x) for x in payload)))

            # Callback with payload
            if elemDecodeCB:
                elemDecodeCB(topicID, payload)

            # Move msgPos on
            msgPos += cls.RS_MSG_PAYLOAD_POS + payloadLength + 1

            # logger.debug(f'ROSSerial decode msgPos {msgPos}')

    @classmethod
    def extractSmartServos(cls, buf: bytes) -> Dict:
        #  Each group of attributes for a servo is a fixed size
        numGroups = math.floor(len(buf) / cls.ROS_SMART_SERVOS_ATTR_GROUP_BYTES)
        servos = {}
        bufPos = 0
        for _ in range(numGroups):
            servoData = struct.unpack(">BhhB", buf[bufPos:bufPos+cls.ROS_SMART_SERVOS_ATTR_GROUP_BYTES])
            servos[servoData[0]] = {
                "IDNo": servoData[0],
                "pos": servoData[1],
                "current": servoData[2],
                "flags": servoData[3],
                "enabled": (servoData[3] & 0x01) != 0,
                "commsOK": (servoData[3] & 0x80) != 0,
            }
            bufPos += cls.ROS_SMART_SERVOS_ATTR_GROUP_BYTES
        return servos

    @classmethod
    def extractAccel(cls, buf: bytes) -> Tuple[float, float, float]:
        xyzTimes1024 = struct.unpack(">fffBB", buf[0:cls.ROS_ACCEL_BYTES])
        return [round(val/1024,2) for val in xyzTimes1024[0:3]]

    @classmethod
    def extractPowerStatus(cls, buf: bytes) -> Dict:
        pst = struct.unpack(">BBHHhHHB", buf[0:cls.ROS_POWER_STATUS_BYTES])
        power5VIsOn = (pst[6] & 0x0002) != 0
        battInfoValid = (pst[6] & 0x0004) == 0
        powerUSBIsValid = (pst[6] & 0x0008) == 0
        powerInfo = {
            "powerFlags": pst[6],
            "power5VIsOn": power5VIsOn,
            "powerUSBIsConnected": (pst[6] & 0x0001) != 0 and powerUSBIsValid,
            "battInfoValid": battInfoValid,
            "powerUSBIsValid": powerUSBIsValid,
            "IDNo": pst[7]
        }
        if battInfoValid:
            powerInfo.update({
                "battRemainCapacityPercent": pst[0],
                "battTempDegC": pst[1],
                "battRemainCapacityMAH": pst[2],
                "battFullCapacityMAH": pst[3],
                "battCurrentMA": pst[4],
            })
        if power5VIsOn:
            powerInfo.update({
                "power5VOnTimeSecs": pst[5]
            })
        return powerInfo

    @classmethod
    def extractRGBT(cls, rgbtVal:int):
        stateVal = rgbtVal & 0xff
        rgbtStates = ["off","on","breathe","override"]
        rgbtState = "unknown"
        if stateVal >= 0 and stateVal < len(rgbtStates):
            rgbtState = rgbtStates[stateVal]
        return {
            "r": (rgbtVal >> 24) & 0xff,
            "g": (rgbtVal >> 16) & 0xff,
            "b": (rgbtVal >> 8) & 0xff,
            "state": rgbtState
        }


    @classmethod
    def extractRobotStatus(cls, buf: bytes) -> Dict:
        if len(buf) >= cls.ROS_ROBOT_STATUS_BYTES:
            robotStat = struct.unpack(">BBIIIIIBB", buf[0:cls.ROS_ROBOT_STATUS_BYTES])
            return {
                "flags": robotStat[0],
                "workQCount": robotStat[1],
                "isMoving": (robotStat[0] & 0x01) != 0,
                "isPaused": (robotStat[0] & 0x02) != 0,
                "isFwUpdating": (robotStat[0] & 0x04) != 0,
                "heapFree": robotStat[2],
                "heapMin": robotStat[3],
                "pixRGBT": list(cls.extractRGBT(robotStat[i+4]) for i in range(3)),
                "loopMsAvg": robotStat[7],
                "loopMsMax": robotStat[8]
            }
        else:
            robotStat = struct.unpack(">BB", buf[0:cls.ROS_ROBOT_STATUS_BYTES_MINIMAL])
            return {
                "flags": robotStat[0],
                "workQCount": robotStat[1],
                "isMoving": (robotStat[0] & 0x01) != 0,
                "isPaused": (robotStat[0] & 0x02) != 0,
                "isFwUpdating": (robotStat[0] & 0x04) != 0,
            }

    @classmethod
    def extractAddOnStatus(cls, buf: bytes) -> List:
        #  Each group of attributes for an add-on is a fixed size
        numGroups = math.floor(len(buf) / cls.ROS_ADDON_GROUP_BYTES)
        addOns = {}
        bufPos = 0
        for _ in range(numGroups):
            adb = buf[bufPos:bufPos+cls.ROS_ADDON_GROUP_BYTES]
            addOns[adb[0]] = {
                "IDNo": adb[0],
                "valid": (adb[1] & 0x80) != 0,
                "data": adb[2:]
            }
            bufPos += cls.ROS_ADDON_GROUP_BYTES
        return addOns
