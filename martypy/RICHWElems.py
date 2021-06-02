'''
RICHWElems
Class supporting the hardware on RIC
'''

import logging
import time
from .RICROSSerial import RICROSSerial
from typing import Dict, List, Tuple, Union
from .ValueAverager import ValueAverager

logger = logging.getLogger(__name__)

class RICHwSmartServos:
    def __init__(self) -> None:
        self.latestMsg: bytes = None
        self.latestMsgTime: float = None
        self.validForSecs = 3

    def update(self, msgPayload: bytes) -> None:
        self.latestMsg = msgPayload
        self.latestMsgTime = time.time()

    def status(self, dictOfHwElemsByIdNo: Dict) -> Dict:
        if self.latestMsgTime is None or time.time() > self.latestMsgTime + self.validForSecs:
            return {}
        servosStatus = RICROSSerial.extractSmartServos(self.latestMsg)
        fieldsToCopy = ["name"]
        for IDNo in servosStatus:
            if IDNo in dictOfHwElemsByIdNo:
                for field in fieldsToCopy:
                    if field in dictOfHwElemsByIdNo[IDNo]:
                        servosStatus[IDNo][field] = dictOfHwElemsByIdNo[IDNo][field]
        return servosStatus

    def servoStatus(self, servoId: int, dictOfHwElemsByIdNo: Dict) -> Dict:
        status = self.status(dictOfHwElemsByIdNo)
        return status.get(servoId, {})

class RICHwIMU:
    def __init__(self) -> None:
        self.latestMsg: bytes = None
        self.latestMsgTime: float = None
        self.validForSecs = 3

    def update(self, msgPayload: bytes) -> None:
        if len(msgPayload) < RICROSSerial.ROS_ACCEL_BYTES:
            return
        self.latestMsg = msgPayload
        self.latestMsgTime = time.time()
        # logger.debug(f"IMU update len {len(msgPayload)}")

    def xyz(self) -> Tuple[float, float, float]:
        if self.latestMsgTime is None:
            return (0,0,0)
        return RICROSSerial.extractAccel(self.latestMsg)

    def axisVal(self, axisCode: int) -> float:
        if self.latestMsgTime is None or time.time() > self.latestMsgTime + self.validForSecs:
            return 0
        xyzTuple = RICROSSerial.extractAccel(self.latestMsg)
        return xyzTuple[axisCode]

class RICHwPowerStatus:
    def __init__(self) -> None:
        self.latestMsg: bytes = None
        self.latestMsgTime: float = None
        self.validForSecs = 5

    def update(self, msgPayload: bytes) -> None:
        if len(msgPayload) < RICROSSerial.ROS_POWER_STATUS_BYTES:
            return
        self.latestMsg = msgPayload
        self.latestMsgTime = time.time()

    def powerStatus(self) -> Dict:
        if self.latestMsgTime is None or time.time() > self.latestMsgTime + self.validForSecs:
            return {}
        return RICROSSerial.extractPowerStatus(self.latestMsg)

class RICHwAddOnStatus:
    def __init__(self):
        self.latestMsg: bytes = None
        self.latestMsgTime: float = None
        self.addOnNameToIdMap = {}
        self.validForSecs = 3

    def update(self, msgPayload: bytes) -> None:
        self.latestMsg = msgPayload
        self.latestMsgTime = time.time()

    def status(self, dictOfHwElemsByIdNo: Dict) -> Dict:
        if self.latestMsgTime is None or time.time() > self.latestMsgTime + self.validForSecs:
            return {}
        addOnStatus = RICROSSerial.extractAddOnStatus(self.latestMsg)
        fieldsToCopy = ["name", "type", "whoAmITypeCode"]
        for IDNo in addOnStatus:
            if IDNo in dictOfHwElemsByIdNo:
                for field in fieldsToCopy:
                    if field in dictOfHwElemsByIdNo[IDNo]:
                        addOnStatus[IDNo][field] = dictOfHwElemsByIdNo[IDNo][field]
        return addOnStatus

    def addOnStatus(self, addOnNameOrId: Union[int, str], dictOfHwElemsByIdNo: Dict) -> Dict:
        status = self.status(dictOfHwElemsByIdNo)
        addOnId = 0
        if type(addOnNameOrId) is str:
            if addOnNameOrId in self.addOnNameToIdMap:
                addOnId = self.addOnNameToIdMap.get(addOnNameOrId, 0)
        else:
            addOnId = addOnNameOrId
        return status.get(addOnId, {})

class RICHwRobotStatus:
    def __init__(self):
        self.latestMsg: bytes = None
        self.latestMsgTime: float = None
        self.validForSecs = 3

    def update(self, msgPayload: bytes) -> None:
        if len(msgPayload) < RICROSSerial.ROS_ROBOT_STATUS_BYTES_MINIMAL:
            return
        self.latestMsg = msgPayload
        self.latestMsgTime = time.time()

    def status(self) -> Dict:
        if self.latestMsgTime is None or time.time() > self.latestMsgTime + self.validForSecs:
            return {}
        return RICROSSerial.extractRobotStatus(self.latestMsg)

class RICHwPublishMonitor:
    
    def __init__(self):
        self._pubRecs = {}

    def update(self, topicID):
        nowTime = time.time()
        if topicID in self._pubRecs:
            pubData = self._pubRecs[topicID]
            lastMsgTime = pubData.get("lastMsgTime", 0)
            timeInterval = nowTime - lastMsgTime
            pubData["averager"].add(timeInterval)
            pubData["lastMsgTime"] = nowTime
        else:
            self._pubRecs[topicID] = {
                "averager": ValueAverager(10),
                "lastMsgTime": nowTime
            }

    def getPublishStats(self):
        pubRateStats = {}
        for topicID in self._pubRecs:
            timeAvgPerMsg = self._pubRecs[topicID]["averager"].getAvg()
            pubRateAvg = 0
            if timeAvgPerMsg > 0:
                pubRateAvg = round(1/timeAvgPerMsg, 2)
            pubRateStats[self.topicIDToStr(topicID)+"PS"] = pubRateAvg
        return pubRateStats

    def topicIDToStr(self, topicID):
        if topicID == RICROSSerial.ROSTOPIC_V2_SMART_SERVOS:
            return "servos"
        elif topicID == RICROSSerial.ROSTOPIC_V2_ACCEL:
            return "imu"
        elif topicID == RICROSSerial.ROSTOPIC_V2_POWER_STATUS:
            return "power"
        elif topicID == RICROSSerial.ROSTOPIC_V2_ADDONS:
            return "addons"
        elif topicID == RICROSSerial.ROSTOPIC_V2_ROBOT_STATUS:
            return "robot"
        return "unknown"
class RICHWElems:

    def __init__(self):
        self._smartServos = RICHwSmartServos()
        self._IMU = RICHwIMU()
        self._powerStatus = RICHwPowerStatus()
        self._addOnsStatus = RICHwAddOnStatus()
        self._robotStatus = RICHwRobotStatus()
        self._publishMonitor = RICHwPublishMonitor()

    def updateWithROSSerialMsg(self, topicID: int, payload: bytes):
        # logger.debug(f"Received ROSSerial topicID {topicID}")
        if topicID == RICROSSerial.ROSTOPIC_V2_SMART_SERVOS:
            self._smartServos.update(payload)
        elif topicID == RICROSSerial.ROSTOPIC_V2_ACCEL:
            self._IMU.update(payload)
        elif topicID == RICROSSerial.ROSTOPIC_V2_POWER_STATUS:
            self._powerStatus.update(payload)
        elif topicID == RICROSSerial.ROSTOPIC_V2_ADDONS:
            self._addOnsStatus.update(payload)
        elif topicID == RICROSSerial.ROSTOPIC_V2_ROBOT_STATUS:
            self._robotStatus.update(payload)
        self._publishMonitor.update(topicID)

    def getServos(self, dictOfHwElemsByIdNo: Dict) -> Dict:
        return self._smartServos.status(dictOfHwElemsByIdNo)

    def getServoPos(self, servoId: int, dictOfHwElemsByIdNo: Dict) -> float:
        return self._smartServos.servoStatus(servoId, dictOfHwElemsByIdNo).get("pos", 0)

    def getServoCurrent(self, servoId: int, dictOfHwElemsByIdNo: Dict) -> float:
        return self._smartServos.servoStatus(servoId, dictOfHwElemsByIdNo).get("current", 0)

    def getServoFlags(self, servoId: int, dictOfHwElemsByIdNo: Dict) -> int:
        return self._smartServos.servoStatus(servoId, dictOfHwElemsByIdNo).get("flags", 0)

    def getIMUAll(self) -> Tuple[float, float, float]:
        return self._IMU.xyz()

    def getIMUAxisValue(self, axisCode: int) -> float:
        return self._IMU.axisVal(axisCode)

    def getPowerStatus(self) -> Dict:
        return self._powerStatus.powerStatus()

    def getRobotStatus(self) -> Dict:
        return self._robotStatus.status()

    def getIsMoving(self) -> bool:
        return self._robotStatus.status().get("isMoving", False)

    def getIsPaused(self) -> bool:
        return self._robotStatus.status().get("isPaused", False)

    def getAddOns(self, dictOfHwElemsByIdNo: Dict) -> List:
        return self._addOnsStatus.status(dictOfHwElemsByIdNo)

    def getAddOn(self, addOnNameOrId: Union[int, str], dictOfHwElemsByIdNo: Dict) -> Dict:
        return self._addOnsStatus.addOnStatus(addOnNameOrId, dictOfHwElemsByIdNo)

    def getPublishStats(self):
        return self._publishMonitor.getPublishStats()

