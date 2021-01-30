'''
RICInterface
'''
from __future__ import annotations
from typing import Callable, Dict
import time
import threading
import logging
import json
from .RICProtocols import DecodedMsg, RICProtocols
from .RICCommsBase import RICCommsBase
from .ValueAverager import ValueAverager

logger = logging.getLogger(__name__)

class RICInterface:
    '''
    RICInterface
    '''
    def __init__(self, commsHandler: RICCommsBase) -> None:
        '''
        Initialise RICInterface
        '''
        self.commsHandler = commsHandler
        self.ricProtocols = RICProtocols()
        self.decodedMsgCB = None
        self.logLineCB = None
        # Message command/response matching
        self.msgTimerCB = None
        self._msgsOutstanding: Dict = {}
        self._msgsOutstandingLock = threading.Lock()
        self.msgRespTimeoutSecs = 1.5
        # AddOn QueryRaw message matching
        self._rawQueryOutstanding: Dict = {}
        self._rawQueryOutstandingLock = threading.Lock()
        self._rawQueryMsgKey = 1
        # Stats
        self.roundTripInfo = ValueAverager()
        self.statsMatched = 0
        self.statsUnMatched = 0
        self.statsUnNumbered = 0

    def __del__(self) -> None:
        self.commsHandler.close()

    def open(self, openParams: Dict) -> bool:
        '''
        Open interface to RIC
        Args:
            openParams: dict containing params used to open the connection
                    (see RICCommsBase and derived classes for details)
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

    def setDecodedMsgCB(self, onDecodedMsg: Callable[[DecodedMsg, RICInterface], None]) -> None:
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

    def sendRICRESTURL(self, msg: str) -> bool:
        '''
        Send RICREST URL message
        Args:
            msg: string containing command URL
        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTURL(msg)
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": time.time()}
        # logger.debug(f"sendRICRESTURL msgNum {msgNum} time {time.time()} msg {msg}")
        self.commsHandler.send(ricRestMsg)
        return True

    def cmdRICRESTSync(self, msg: str) -> Dict:
        '''
        Send RICREST URL message and wait for response
        Args:
            msg: string containing command URL
        Returns:
            Response turned into a dictionary (from JSON)
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTURL(msg)
        # logger.debug(f"msgNum {msgNum} msg {msg}")
        msgSendTime = time.time()
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": msgSendTime,"awaited":True}
        self.commsHandler.send(ricRestMsg)
        # Wait for result
        while time.time() < msgSendTime + self.msgRespTimeoutSecs:
            with self._msgsOutstandingLock:
                # Should be an outstanding message - if not there's a problem
                if msgNum not in self._msgsOutstanding:
                    return {"rslt":"failResponse"}
                # Check if response received
                if self._msgsOutstanding[msgNum].get("respValid", False):
                    try:
                        # Get response
                        respStr = self._msgsOutstanding[msgNum].get("resp", None)
                        respObj = {}
                        if respStr:
                            respObj = json.loads(respStr.payload.rstrip('\0'))
                        debugMsgRespTime = self._msgsOutstanding[msgNum].get("respTime", 0)
                        # logger.debug(f"msgNum {msgNum} msg {msg} resp {json.dumps(respObj)} sendTime {msgSendTime} respTime {debugMsgRespTime}")
                        return respObj
                    except Exception as excp:
                        logger.debug(f"msgNum {msgNum} response is not JSON {excp}")
            time.sleep(0.01)
        return {"rslt":"failTimeout"}

    def cmdRICRESTRslt(self, msg: str) -> bool:
        '''
        Send RICREST URL message and wait for response
        Args:
            msg: string containing command URL
        Returns:
            Response turned into a dictionary (from JSON)
        '''
        response = self.cmdRICRESTSync(msg)
        return response.get("rslt", "") == "ok"

    def sendRICRESTCmdFrame(self, msg: bytes) -> bool:
        '''
        Send RICREST command frame message
        Args:
            msg: string containing command
        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTCmdFrame(msg)
        # logger.debug(f"sendRICRESTCmdFrame msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        with self._msgsOutstandingLock:
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
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTFileBlock(data)
        # logger.debug(f"sendRICRESTFileBlock msgNum {msgNum} len {len(ricRestMsg)}")
        with self._msgsOutstandingLock:
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

    def getStats(self) -> Dict:
        return {
            "roundTripAvgS":self.roundTripInfo.getAvg(),
            "unmatched":self.statsUnMatched,
            "matched":self.statsMatched,
            "unnumbered":self.statsUnNumbered,
        }

    def addOnQueryRaw(self, addOnName: str, dataToWrite: bytes, numBytesToRead: int) -> Dict:
        '''
        Write and read an addOn directly (raw-mode)
        Args:
            addOnName, name of the addOn (see get_add_ons_status() at the top level or response to
                addon/list REST API command)
            dataToWrite, can be zero length if nothing is to be written, the first byte will generally
                be the register or opcode of the addOn
            numBytesToRead: number of bytes to read from the device - can be zero
        Returns:
            Dict with keys including:
                "rslt" - the result which will be "ok" if the query succeeded
                "dataRead" - the data read from the addOn
        '''
        # Handle msgKey
        msgKey = self._rawQueryMsgKey
        self._rawQueryMsgKey += 1
        if self._rawQueryMsgKey > 99999:
            self._rawQueryMsgKey = 1

        # Form command
        hexWrStr = dataToWrite.hex()
        ricRestCmd = f"elem/{addOnName}/json?cmd=raw&hexWr={hexWrStr}&numToRd={numBytesToRead}&msgKey={msgKey}"

        # Register in raw message matching
        with self._rawQueryOutstandingLock:
            self._rawQueryOutstanding[msgKey] = {"timeSent": time.time(), "awaited":True}

        # Send message
        resp = self.cmdRICRESTSync(ricRestCmd)
        resp["dataRead"] = b""
        if resp.get("rslt", "") != "ok":
            self._rawQueryOutstanding.pop(msgKey)
            return resp

        # Wait for a report message generated by the addOn access process
        msgSendTime = time.time()
        while time.time() < msgSendTime + self.msgRespTimeoutSecs:
            with self._rawQueryOutstandingLock:
                # Should be an outstanding message - if not there's a problem
                if msgKey not in self._rawQueryOutstanding:
                    resp["rslt"] = "failReport"
                    return resp
                # Check if a report received
                if self._rawQueryOutstanding[msgKey].get("reptValid", False):
                    # Get report
                    reptObj = self._rawQueryOutstanding[msgKey].get("reptObj", {})
                    logger.debug(f"msgKey {msgKey} msg {ricRestCmd} rept {json.dumps(reptObj)} sendTime {msgSendTime}")
                    resp["dataRead"] = reptObj.get("hexRd", b"")
                    return resp
            time.sleep(0.01)
        return {"rslt":"failTimeout"}

    def _onRxFrameCB(self, frame: bytes) -> None:
        # logger.debug(f"_onRxFrameCB Rx len {len(frame)} data {frame.hex()}")
        decodedMsg = self.ricProtocols.decodeRICFrame(frame)
        if decodedMsg.msgNum != 0:
            # Numbered message - this is the response to a REST API command
            # logger.debug(f"_onRxFrameCB msgNum {decodedMsg.msgNum} {decodedMsg.payload}")
            isUnmatched = False
            with self._msgsOutstandingLock:
                if decodedMsg.msgNum in self._msgsOutstanding:
                    msgRec = self._msgsOutstanding[decodedMsg.msgNum]
                    roundTripTime = time.time() - msgRec["timeSent"]
                    self.newRoundTrip(roundTripTime)
                    if not msgRec.get("awaited", False):
                        self._msgsOutstanding.pop(decodedMsg.msgNum)
                    else:
                        msgRec["resp"] = decodedMsg
                        msgRec["respValid"] = True
                        msgRec["respTime"] = time.time()
                    self.statsMatched += 1
                else:
                    isUnmatched = True
                    self.statsUnMatched += 1
            if isUnmatched:
                logger.debug(f"_onRxFrameCB Unmatched msgNum {decodedMsg.msgNum}")
        else:
            logger.debug(f"_onRxFrameCB unnumbered restType {decodedMsg.restType} msgType {decodedMsg.msgTypeCode}")
            if decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_REPORT:
                # Report message - this can include results of accessing addOns
                # logger.debug(f"_onRxFrameCB REPORT {decodedMsg.payload}")
                reptObj = {}
                try:
                    reptObj = json.loads(decodedMsg.payload.rstrip('\0'))
                except Exception as excp:
                    logger.debug(f"_onRxFrameCB REPORT is not JSON {excp}")
                msgKey = reptObj.get("msgKey", '')
                if type(msgKey) is str:
                    msgKey = int(msgKey)
                if msgKey != 0:
                    isUnmatched = False
                    with self._rawQueryOutstandingLock:
                        if msgKey in self._rawQueryOutstanding:
                            msgRec = self._rawQueryOutstanding[msgKey]
                            if not msgRec.get("awaited", False):
                                self._rawQueryOutstanding.pop(msgKey)
                            else:
                                msgRec["reptObj"] = reptObj
                                msgRec["reptValid"] = True
                        else:
                            isUnmatched = True
                    if isUnmatched:
                        logger.debug(f"Unmatched msgKey {msgKey}")
                self.statsUnNumbered += 1
        # Call the decoded-message callback with the message
        if self.decodedMsgCB is not None:
            self.decodedMsgCB(decodedMsg, self)

    def _onLogLineCB(self, line: str) -> None:
        if self.logLineCB:
            self.logLineCB(line)

    def _msgTimeoutCheck(self) -> None:
        # Check messages outstanding
        # logger.debug("Check outstanding messages")
        msgIdxsToRemove = []
        msgIdxsTimedOut = []
        with self._msgsOutstandingLock:
            for msgItem in self._msgsOutstanding.items():
                timeSinceSent = time.time() - msgItem[1].get("timeSent", 0)
                if timeSinceSent > self.msgRespTimeoutSecs:
                    if not msgItem[1].get("respValid", False):
                        msgIdxsTimedOut.append(msgItem[0])
                    msgIdxsToRemove.append(msgItem[0])

        # Debug
        for msgIdx in msgIdxsTimedOut:
            logger.debug(f"Message {msgIdx} timed out at time {time.time()}")

        # Remove timed-out messages
        for msgIdx in msgIdxsToRemove:
            with self._msgsOutstandingLock:
                self._msgsOutstanding.pop(msgIdx)

        # Check rawQuery reports outstanding
        # logger.debug("Check rawQuery reports outstanding")
        msgKeysToRemove = []
        msgKeysTimedOut = []
        with self._rawQueryOutstandingLock:
            for msgItem in self._rawQueryOutstanding.items():
                timeSinceSent = time.time() - msgItem[1].get("timeSent", 0)
                if timeSinceSent > self.msgRespTimeoutSecs:
                    if not msgItem[1].get("reptValid", False):
                        msgKeysTimedOut.append(msgItem[0])
                    msgKeysToRemove.append(msgItem[0])

        # Debug
        for msgKey in msgKeysTimedOut:
            logger.debug(f"rawQuery {msgKey} timed out at time {time.time()}")

        # Remove timed-out rawQueries
        for msgKey in msgKeysToRemove:
            with self._rawQueryOutstandingLock:
                self._rawQueryOutstanding.pop(msgKey)

        # Restart timer
        if self.commsHandler is not None and self.commsHandler.isOpen():
            self.msgTimeoutCheckTimer = threading.Timer(1.0, self._msgTimeoutCheck)
            self.msgTimeoutCheckTimer.start()

        # Callback on timer if required
        if self.msgTimerCB:
            self.msgTimerCB()

    def getTestOutput(self) -> dict:
        return self.commsHandler.getTestOutput()
