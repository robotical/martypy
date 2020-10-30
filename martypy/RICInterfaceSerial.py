'''
RICInterfaceSerial
'''
from __future__ import annotations
from martypy.RICHWElems import RICHwAddOnStatus
import time
import threading
from typing import Callable, Dict
import logging
import json
from .RICProtocols import DecodedMsg, RICProtocols
from .RICCommsSerial import RICCommsSerial
from .ValueAverager import ValueAverager

logger = logging.getLogger(__name__)

class RICInterfaceSerial:
    '''
    RICInterfaceSerial
    RIC access via a serial interface
    '''
    def __init__(self) -> None:
        '''
        Initialise RICInterfaceSerial
        '''
        self.commsHandler = RICCommsSerial()
        self.ricProtocols = RICProtocols()
        self.decodedMsgCB = None
        self.logLineCB = None
        self.msgTimerCB = None
        self._msgsOutstanding: Dict = {}
        self.roundTripInfo = ValueAverager()
        self.msgRespTimeoutSecs = 3
        self.ricSystemInfo = None

    def __del__(self) -> None:
        self.commsHandler.close()

    def close(self) -> None:
        self.commsHandler.close()

    def setDecodedMsgCB(self, onDecodedMsg: Callable[[DecodedMsg, RICInterfaceSerial], None]) -> None:
        '''
        Set callback on decoded message received from RIC

        Args:
            cb: callback function (takes 2 parameters: decoded message and this object)

        Returns:
            None
        '''
        self.decodedMsgCB = onDecodedMsg

    def setLogLineCB(self, onLogLine: Callable[[str], None]) -> None:
        '''
        Set callback on logging line received

        Args:
            onLogLine: callback function (takes 1 parameter which is the line of logging information)

        Returns:
            None
        '''
        self.logLineCB = onLogLine

    def setTimerCB(self, onMsgTimerCB: Callable[[], None]) -> None:
        '''
        Set callback which can be used to check for message types (e.g. publish) 

        Args:
            onMsgTimerCB: callback function (takes 0 parameters)

        Returns:
            None
        '''
        self.msgTimerCB = onMsgTimerCB

    def open(self, openParams: Dict) -> bool:
        '''
        Open serial interface to RIC
        Protocol can be plain (if the port is not used for any other purpose) or
        overascii (if the port is also used for logging information)

        Args:
            openParams: dict containing params used to open the port - "serialPort", 
                        "serialBaud" and "ifType". "ifType" should be "plain" or 
                        "overascii"

        Returns:
            True if open succeeded or port is already open

        Throws:
            SerialException: if the serial port cannot be opened
        '''
        self.commsHandler.setRxFrameCB(self._onRxFrameCB)
        self.commsHandler.setRxLogLineCB(self._onLogLineCB)
        openOk = self.commsHandler.open(openParams)

        # Start timer to check message completion
        self.msgTimeoutCheckTimer = threading.Timer(1.0, self._msgTimeoutCheck)
        self.msgTimeoutCheckTimer.daemon = True
        self.msgTimeoutCheckTimer.start()
        return openOk

    def close(self) -> None:
        '''
        Close serial interface to RIC

        Args:
            none

        Returns:
            None
        '''
        self.commsHandler.close()

    def sendRICRESTURL(self, msg: str) -> bool:
        '''
        Send RICREST URL message

        Args:
            msg: string containing command URL

        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTURL(msg)
        self._msgsOutstanding[msgNum] = {"timeSent": time.time()}
        logger.debug(f"sendRICRESTURL msgNum {msgNum} len {len(ricRestMsg)} time {time.time()}")
        self.commsHandler.send(ricRestMsg)
        return True

    def sendRICRESTURLSync(self, msg: bytes) -> Dict:
        '''
        Send RICREST URL message and wait for response

        Args:
            msg: string containing command URL

        Returns:
            Response turned into a dictionary (from JSON)
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTURL(msg)
        logger.debug(f"sendRICRESTURLSync msgNum {msgNum} len {len(ricRestMsg)} time {time.time()}")
        timeNow = time.time()
        self._msgsOutstanding[msgNum] = {"timeSent": timeNow,"awaited":True}
        self.commsHandler.send(ricRestMsg)
        # Wait for result
        while time.time() < timeNow + self.msgRespTimeoutSecs:
            if msgNum not in self._msgsOutstanding:
                return {}
            if self._msgsOutstanding[msgNum].get("respValid", False):
                try:
                    resp = self._msgsOutstanding[msgNum].get("resp", None)
                    if resp:
                        return json.loads(resp.payload.rstrip('\0'))
                    return {}
                except Exception as excp:
                    logger.debug(f"sendRICRESTURLSync response is not JSON {excp}", )
            time.sleep(0.01)
        return {}

    def sendRICRESTCmdFrame(self, msg: bytes) -> bool:
        '''
        Send RICREST command frame message

        Args:
            msg: string containing command

        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTCmdFrame(msg)
        logger.debug(f"sendRICRESTCmdFrame msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        self._msgsOutstanding[msgNum] = {"timeSent": time.time()}
        self.commsHandler.send(ricRestMsg)
        return True

    def sendRICRESTFileBlock(self, data: bytes) -> bool:
        '''
        Send RICREST file block

        Args:
            data: bytes of file data

        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTFileBlock(msg)
        # logger.debug(f"sendRICRESTFileBlock msgNum {msgNum} len {len(ricRestMsg)}")
        self._msgsOutstanding[msgNum] = {"timeSent": time.time()}
        self.commsHandler.send(ricRestMsg)
        return True

    def newRoundTrip(self, rtTime:int) -> None:
        '''
        Indicate a new round-trip for a message is complete - this is 
        for statistics gathering

        Args:
            rtTime: time taken for round-trip in seconds

        Returns:
            None
        '''
        self.roundTripInfo.add(rtTime)
        # logger.debug(f"RTTime {self.roundTripInfo.getAvg()}")

    def sendTestMsgs(self, numMsgs:int, bytesPerMsg: int) -> None:
        '''
        Send a batch of test messages

        Args:
            numMsgs: number of messages to send
            bytesPerMsg: bytes in each message

        Returns:
            None
        '''
        dataBlock = bytearray(bytesPerMsg)
        for i in range(numMsgs):
            self.commsHandler.send(dataBlock)

    def sendFile(self, filename: str, isEspFirmware: bool) -> None:
        '''
        Send a file (from the file system) over serial connection

        Args:
            filename: name of file to send
            isEspFirmware: False for a normal file, True for new RIC firmware

        Returns:
            None

        Throws:
            OSError: operating system exceptions
            May throw other exceptions so include a general exception handler
        '''
        # Send new firmware in the bin folder using the CommandHandler protocol
        with open(filename, "rb") as f:

            # Read firmware
            binaryImage = f.read()
            binaryImageLen = len(binaryImage)
            # logger.debug(f"File {filename} is {binaryImageLen} bytes long")

            # Frames follow the approach used in the web interface start, block..., end
            time.sleep(1.0)
            fileType = "fs"
            uploadType = "fileupload"
            if isEspFirmware:
                fileType = "ricfw"
                uploadType = "espFwUpdate"
            self.sendRICRESTCmdFrame('{' + f'"cmdName":"ufStart","reqStr":"{uploadType}","fileType":"{fileType}",' + \
                            f'fileName":"{filename}","fileLen":{str(binaryImageLen)}' + '}\0')
            time.sleep(1.0)

            # Split the file into blocks
            blockMaxSize = 200
            numBlocks = binaryImageLen//blockMaxSize + (0 if (binaryImageLen % blockMaxSize == 0) else 1)
            # logger.debug(f"Sending file in {numBlocks} blocks of {blockMaxSize} max bytes")
            for i in range(numBlocks):
                blockStart = i*blockMaxSize
                blockToSend = binaryImage[blockStart:blockStart+blockMaxSize]
                self.sendRICRESTFileBlock(blockStart.to_bytes(4, 'big') + blockToSend)
                time.sleep(0.01)
                # if i % 10 == 9:
                #     logger.debug(f"SendFile Progress {i * 100 / numBlocks:0.1f}%")

            # End frame            
            time.sleep(1.0)
            self.sendRICRESTCmdFrame('{' + f'"cmdName":"ufEnd","reqStr":"fileupload","fileType":"{fileType}",' + \
                            f'"fileName":"{filename}","fileLen":{str(binaryImageLen)},' + \
                            f'"blockCount":{str(numBlocks)}' + '}\0')

            # logger.debug(f"Endframe sent")

            # # Check for end frame acknowledged
            # prevTime = time.time()
            # while True:
            #     if uploadAck:
            #         break
            #     if time.time() - prevTime > 2:
            #         break

    def getRICSystemInfo(self) -> None:
        self.ricSystemInfo = self.sendRICRESTURLSync("v")

    def getRICName(self) -> None:
        self.ricSystemInfo = self.sendRICRESTURLSync("friendlyname")

    def getRICCalibInfo(self) -> None:
        self.ricSystemInfo = self.sendRICRESTURLSync("calibrate")

    def getHWElemList(self) -> None:
        self.ricSystemInfo = self.sendRICRESTURLSync("hwstatus")

    def _onRxFrameCB(self, frame: bytes) -> None:
        # logger.debug(f"Frame Rx len {len(frame)}")
        decodedMsg = self.ricProtocols.decodeRICFrame(frame)
        if decodedMsg.msgNum != 0:
            if decodedMsg.msgNum in self._msgsOutstanding:
                roundTripTime = time.time() - self._msgsOutstanding[decodedMsg.msgNum]["timeSent"]
                self.newRoundTrip(roundTripTime)
                if not self._msgsOutstanding[decodedMsg.msgNum].get("awaited", False):
                    del self._msgsOutstanding[decodedMsg.msgNum]
                else:
                    self._msgsOutstanding[decodedMsg.msgNum]["resp"] = decodedMsg
                    self._msgsOutstanding[decodedMsg.msgNum]["respValid"] = True
            else:
                logger.debug(f"Unmatched msgNum {decodedMsg.msgNum}")
        if self.decodedMsgCB is not None:
            self.decodedMsgCB(decodedMsg, self)

    def _onLogLineCB(self, line: str) -> None:
        if self.logLineCB:
            self.logLineCB(line)

    def _msgTimeoutCheck(self) -> None:
        # Check messages outstanding
        # logger.debug("Check outstanding messages")
        msgIdxsToRemove = []
        for msgItem in self._msgsOutstanding.items():
            timeSinceSent = time.time() - msgItem[1].get("timeSent", 0)
            if timeSinceSent > self.msgRespTimeoutSecs:
                if not msgItem[1].get("respValid", False):
                    logger.debug(f"Message {msgItem[0]} timed out at time {time.time()}")
                msgIdxsToRemove.append(msgItem[0])

        # Remove timed-out messages
        for msgIdx in msgIdxsToRemove:
            self._msgsOutstanding.pop(msgIdx)
        
        # Restart timer
        if self.commsHandler is not None and self.commsHandler.isOpen:
            self.msgTimeoutCheckTimer = threading.Timer(1.0, self._msgTimeoutCheck)
            self.msgTimeoutCheckTimer.start()

        # Callback on timer if required
        if self.msgTimerCB:
            self.msgTimerCB()

