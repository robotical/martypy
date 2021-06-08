'''
RICInterface
'''
from typing import Callable, Dict, Union, Optional
import time
import threading
import logging
import json
import os
from .RICProtocols import DecodedMsg, RICProtocols
from .RICCommsBase import RICCommsBase
from .RateAverager import RateAverager
from .ValueAverager import ValueAverager
from .Exceptions import MartyTransferException

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
        self.msgRxRate = RateAverager()
        self.msgTxRate = RateAverager()
        self.roundTripInfo = ValueAverager()
        self.statsMatched = 0
        self.statsUnMatched = 0
        self.statsUnNumbered = 0
        self.statsTimedOut = 0
        self.uploadBytesPerSec = ValueAverager()
        # File send vars
        self._fileOTAStartFailed = False
        self._fileOTAStartedOK = False
        self._fileNotStarted = False
        self._fileUserCancel = False
        self._fileSendOkTo = 0
        self._fileSendNewOkTo = False
        self._fileFailedInFirmware = False
        self.BLOCK_ACK_TIMEOUT = 15
        self.BATCH_RETRY_MAX = 3

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
        Close interface to RIC
        Args:
            none
        Returns:
            None
        '''
        self.commsHandler.close()

    def isOpen(self) -> None:
        return self.commsHandler.isOpen()

    def setDecodedMsgCB(self, onDecodedMsg: Callable[[DecodedMsg, 'RICInterface'], None]) -> None:
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

    def sendRICRESTURL(self, msg: str, timeOutSecs: Optional[float] = None) -> bool:
        '''
        Send RICREST URL message
        Args:
            msg: string containing command URL
            timeOutSecs: message time-out override in seconds (or None to use default)
        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTURL(msg)
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": time.time(), "timeOutSecs": timeOutSecs}
        # logger.debug(f"sendRICRESTURL msgNum {msgNum} time {time.time()} msg {msg}")
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        return True

    def cmdRICRESTURLSync(self, msg: str, timeOutSecs: Optional[float] = None) -> Dict:
        '''
        Send RICREST URL message and wait for response
        Args:
            msg: string containing command URL
            timeOutSecs: message time-out override in seconds (or None to use default)
        Returns:
            Response turned into a dictionary (from JSON)
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTURL(msg)
        # logger.debug(f"msgNum {msgNum} msg {msg}")
        msgSendTime = time.time()
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": msgSendTime, "timeOutSecs": timeOutSecs, "awaited":True}
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        # Wait for result
        while time.time() < msgSendTime + timeOutSecs:
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
                        # logger.debug(f"sendRICRESTURLSync msgNum {msgNum} msg {msg} resp {json.dumps(respObj)} sendTime {msgSendTime} respTime {debugMsgRespTime}")
                        return respObj
                    except Exception as excp:
                        logger.warn(f"sendRICRESTURLSync msgNum {msgNum} response is not JSON {excp}")
            time.sleep(0.01)
        return {"rslt":"failTimeout"}

    def cmdRICRESTRslt(self, msg: str, timeOutSecs: Optional[float] = None) -> bool:
        '''
        Send RICREST URL message and wait for response
        Args:
            msg: string containing command URL
            timeOutSecs: message time-out override in seconds (or None to use default)
        Returns:
            Response turned into a dictionary (from JSON)
        '''
        response = self.cmdRICRESTURLSync(msg, timeOutSecs)
        return response.get("rslt", "") == "ok"

    def sendRICRESTCmdFrame(self, msg: Union[str,bytes], 
                    payload: Union[bytes, str, None] = None, timeOutSecs: Optional[float] = None) -> bool:
        '''
        Send RICREST command frame message
        Args:
            msg: string or bytes containing command frame
            payload: optional payload
            timeOutSecs: message time-out override in seconds (or None to use default)
        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTCmdFrame(msg, payload)
        # logger.debug(f"sendRICRESTCmdFrame msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": time.time(), "timeOutSecs": timeOutSecs}
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        return True

    def sendRICRESTCmdFrameSync(self, msg: Union[str,bytes], 
                    payload: Union[bytes, str] = None,
                    timeOutSecs: Optional[float] = None) -> Dict:
        '''
        Send RICREST command frame message and wait for response
        Args:
            msg: string or bytes containing command frame
            payload: optional payload
            timeOutSecs: message time-out override in seconds (or None to use default)
        Returns:
            Response turned into a dictionary (from JSON)
        '''
        # Encode frame
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTCmdFrame(msg, payload)
        # logger.debug(f"sendRICRESTCmdFrameSync msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        msgSendTime = time.time()
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": msgSendTime, "timeOutSecs": timeOutSecs, "awaited":True}
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        # Wait for result
        while time.time() < msgSendTime + timeOutSecs:
            logger.debug(f"sendRICRESTCmdFrameSync while loop")
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
                        # logger.debug(f"sendRICRESTCmdFrameSync msgNum {msgNum} msg {msg} resp {json.dumps(respObj)} sendTime {msgSendTime} respTime {debugMsgRespTime}")
                        return respObj
                    except Exception as excp:
                        logger.debug(f"msgNum {msgNum} response is not JSON {excp}", )
            time.sleep(0.01)
        logger.debug(f"sendRICRESTCmdFrameSync msgNum {msgNum} msg {msg} sendTime {msgSendTime} timeNow {time.time()} timeout {timeOutSecs}")
        return {"rslt":"failTimeout"}

    def sendRICRESTFileBlock(self, data: bytes) -> bool:
        '''
        Send RICREST file block
        Args:
            data: bytes of file data
        Returns:
            True if message sent
        '''
        ricRestMsg, _ = self.ricProtocols.encodeRICRESTFileBlock(data)
        # logger.debug(f"sendRICRESTFileBlock msgNum {msgNum} len {len(ricRestMsg)}")
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
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
            self.msgTxRate.addSample()

    def _sendFileProgressCheckAbort(self, progressCB: Callable[[int, int, 'RICInterface'], bool], 
                    currentPos: int, fileSize: int) -> bool:
        if self._fileOTAStartFailed or self._fileNotStarted or self._fileUserCancel or self._fileFailedInFirmware:
            return True
        if not progressCB:
            return False
        if not progressCB(currentPos, fileSize, self):
            self.sendRICRESTCmdFrameSync('{"cmdName":"ufCancel"}')
            return True
        return False

    def sendFile(self, filename: str, fileDest: str, reqStr: str = '', 
                progressCB: Callable[[int, int, 'RICInterface'], bool] = None) -> bool:
        '''
        Send a file (from the file system)
        Args:
            filename: name of file to send
            fileDest: "fs" to upload to file system, "ricfw" for new RIC firmware
            reqStr: API request used for transfer, if left blank this is inferred from fileDest, other
                    values include "fileupload" and "espfwupdate" - see RIC documentation for API
            progressCB: callback used to indicate how file send is progressing, callable takes three params
                    which are bytesSent, totalBytes and the interface to RIC (of type RICInterface) and
                    returns a bool which should be True to continue the file upload or False to abort
        Returns:
            True if operation succeeded
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

            # Check if we're uploading firmware
            isFirmware = fileDest == "ricfw"
            if reqStr == '':
                reqStr = 'espfwupdate' if isFirmware else 'fileupload'
            uploadName = "fw" if isFirmware else os.path.basename(filename)
            self._fileOTAStartFailed = False
            self._fileOTAStartedOK = False
            self._fileNotStarted = False
            self._fileUserCancel = False
            self._fileFailedInFirmware = False

            # Frames follow the approach used in the web interface start, block..., end
            resp = self.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufStart","reqStr":"{reqStr}","fileType":"{fileDest}",' + \
                            f'"fileName":"{uploadName}","fileLen":{str(binaryImageLen)}' + '}', 
                            timeOutSecs = 10)
            if resp.get("rslt","") != "ok":
                raise MartyTransferException("File transfer start not acknowledged")

            # Block and batch sizes
            blockMaxSize = self.commsHandler.commsParams.fileTransfer.get("fileBlockMax", 5000)
            blockMaxSize = resp.get("batchMsgSize", blockMaxSize)
            batchAckSize = resp.get("batchAckSize", 50)
            self._fileSendOkTo = 0

            # Debug
            # logger.debug(f"ricIF sendFile blockMaxSize {blockMaxSize} batchAckSize {batchAckSize} resp {resp}")

            # Progress and check for abort
            if self._sendFileProgressCheckAbort(progressCB, self._fileSendOkTo, binaryImageLen):
                return False

            # Wait for a period depending on whether we're sending firmware - this is because starting
            # a firmware update involves the ESP32 in a long-running activity and the firmware becomes
            # unresponsive during this time
            if isFirmware:
                for i in range(5):
                    time.sleep(1)
                    if self._sendFileProgressCheckAbort(progressCB, 0, binaryImageLen):
                        return False
                    if self._fileOTAStartedOK:
                        break

            # Debug
            # logger.debug(f"ricIF sendFile starting to send file data ...")

            # Send file blocks
            numBlocks = 0
            batchRetryCount = 0
            while self._fileSendOkTo < binaryImageLen:

                # NOTE: first batch MUST be of size 1 (not batchAckSize) because RIC performs a long-running
                # blocking task immediately after receiving the first message in a firmware
                # update - although this could be relaxed for non-firmware update file uploads
                sendFromPos = self._fileSendOkTo
                batchStartPos = self._fileSendOkTo
                batchStartTime = time.time()
                batchSize = 1 if sendFromPos == 0 else batchAckSize
                batchBlockIdx = 0
                self._fileSendNewOkTo = False
                while batchBlockIdx < batchSize and sendFromPos < binaryImageLen:

                    # Send block
                    blockToSend = binaryImage[sendFromPos:sendFromPos+blockMaxSize]
                    self.sendRICRESTFileBlock(sendFromPos.to_bytes(4, 'big') + blockToSend)
                    sendFromPos += blockMaxSize
                    batchBlockIdx += 1

                    # Check if we have received an error
                    if self._fileNotStarted or self._fileUserCancel or self._fileFailedInFirmware:
                        break

                # Debug
                # logger.debug(f"ricIF sendFile sent batch - start at {batchStartPos} end at {sendFromPos} okto {self._fileSendOkTo}")

                # Wait for response (there is a timeout at the ESP end to ensure a response is always returned
                # even if blocks are dropped on reception at ESP) - the timeout here is for these responses
                # being dropped
                timeNow = time.time()
                while time.time() - timeNow < self.BLOCK_ACK_TIMEOUT:
                    # Progress update
                    if self._sendFileProgressCheckAbort(progressCB, self._fileSendOkTo, binaryImageLen):
                        return False

                    # Debug
                    # logger.debug(f"ricIF sendFile checking for OKTO {self._fileSendOkTo} batchStartPos {batchStartPos}")

                    # Check for okto
                    if self._fileSendNewOkTo:
                        batchRetryCount = 0
                        # Update stats
                        if self._fileSendOkTo > batchStartPos:
                            batchBytesPerSec = (self._fileSendOkTo - batchStartPos) / (time.time() - batchStartTime)
                            self.uploadBytesPerSec.add(batchBytesPerSec)
                        break

                    # Wait
                    time.sleep(1)

                # Check if no okto has been received with a greater position than batchStartPos
                if self._fileSendOkTo <= batchStartPos:
                    batchRetryCount += 1
                    if batchRetryCount > self.BATCH_RETRY_MAX:
                        return False

                # Block count
                numBlocks += 1

            # Debug
            # logger.debug(f"ricIF sendFile sending END")

            # End frame
            resp = self.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufEnd","reqStr":"fileupload","fileType":"{fileDest}",' + \
                            f'"fileName":"{filename}","fileLen":{str(binaryImageLen)},' + \
                            f'"blockCount":{str(numBlocks)}' + '}', 
                            timeOutSecs = 5)
            if resp.get("rslt","") != "ok":
                return False
            return True

    def getStats(self) -> Dict:
        return {
            "roundTripAvgMS":self.roundTripInfo.getAvg()*1000,
            "msgRxRatePS":self.msgRxRate.getAvg(),
            "msgTxRatePS":self.msgTxRate.getAvg(),
            "unmatched":self.statsUnMatched,
            "matched":self.statsMatched,
            "unnumbered":self.statsUnNumbered,
            "timedOut":self.statsTimedOut,
            "uploadBPS":self.uploadBytesPerSec.getAvg(),
            "rxCount":self.msgRxRate.getTotal(),
            "txCount":self.msgTxRate.getTotal(),
        }

    def addOnQueryRaw(self, addOnName: str, dataToWrite: bytes, numBytesToRead: int,
                        timeOutSecs: Optional[float] = None) -> Dict:
        '''
        Write and read an addOn directly (raw-mode)
        Args:
            addOnName, name of the addOn (see get_add_ons_status() at the top level or response to
                addon/list REST API command)
            dataToWrite, can be zero length if nothing is to be written, the first byte will generally
                be the register or opcode of the addOn
            numBytesToRead: number of bytes to read from the device - can be zero
            timeOutSecs: message time-out override in seconds (or None to use default)
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
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._rawQueryOutstandingLock:
            self._rawQueryOutstanding[msgKey] = {"timeSent": time.time(), "timeOutSecs": timeOutSecs, "awaited":True}

        # Send message
        resp = self.cmdRICRESTURLSync(ricRestCmd)
        resp["dataRead"] = b""
        if resp.get("rslt", "") != "ok":
            self._rawQueryOutstanding.pop(msgKey)
            return resp

        # Wait for a report message generated by the addOn access process
        msgSendTime = time.time()
        while time.time() < msgSendTime + timeOutSecs:
            with self._rawQueryOutstandingLock:
                # Should be an outstanding message - if not there's a problem
                if msgKey not in self._rawQueryOutstanding:
                    resp["rslt"] = "failReport"
                    return resp
                # Check if a report received
                if self._rawQueryOutstanding[msgKey].get("reptValid", False):
                    # Get report
                    reptObj = self._rawQueryOutstanding[msgKey].get("reptObj", {})
                    # logger.debug(f"msgKey {msgKey} msg {ricRestCmd} rept {json.dumps(reptObj)} sendTime {msgSendTime}")
                    resp["dataRead"] = reptObj.get("hexRd", b"")
                    return resp
            time.sleep(0.01)
        return {"rslt":"failTimeout"}

    def _onRxFrameCB(self, frame: bytes) -> None:
        # logger.debug(f"_onRxFrameCB Rx len {len(frame)} data {frame.hex()}")
        self.msgRxRate.addSample()
        decodedMsg = self.ricProtocols.decodeRICFrame(frame)
        doRxCallback = True
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
                logger.warn(f"_onRxFrameCB Unmatched msgNum {decodedMsg.msgNum}")
            doRxCallback = isUnmatched
        else:
            # logger.debug(f"_onRxFrameCB unnumbered restType {decodedMsg.restType} msgType {decodedMsg.msgTypeCode}")
            if decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_REPORT:
                # Report message - this can include results of accessing addOns
                # logger.debug(f"_onRxFrameCB REPORT {decodedMsg.payload}")
                reptObj = {}
                try:
                    reptObj = json.loads(decodedMsg.payload.rstrip('\0'))
                except Exception as excp:
                    logger.warn(f"_onRxFrameCB REPORT is not JSON {excp}")
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
                    doRxCallback = isUnmatched
            elif decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_RESPONSE:
                # logger.debug(f"RESPONSE {decodedMsg.payload}")
                # Check for okto message
                reptObj = {}
                try:
                    reptObj = json.loads(decodedMsg.payload.rstrip('\0'))
                except Exception as excp:
                    logger.warn(f"_onRxFrameCB REPORT is not JSON {excp}")
                if "okto" in reptObj:
                    okto = reptObj.get("okto", -1)
                    if self._fileSendOkTo < okto:
                        self._fileSendOkTo = okto
                    self._fileSendNewOkTo = True
                    # logger.debug(f"OKTO MESSAGE {reptObj['okto']}")
                elif "cmdName" in reptObj:
                    cmdName = reptObj.get("cmdName","")
                    if cmdName == "ufBlock" or cmdName == "ufStatus" or cmdName == "ufCancel":
                        reason = reptObj.get("reason","")
                        if reason == "OTAStartFailed":
                            self._fileOTAStartFailed = True
                        elif reason == "OTAStartedOK":
                            self._fileOTAStartedOK = True
                        elif reason == "notStarted":
                            self._fileNotStarted = True
                        elif reason == "userCancel":
                            self._fileUserCancel = True
                        elif reason == "failRetries" or reason == "failTimeout":
                            self._fileFailedInFirmware = True
                    logger.warn(f"_onRxFrameCB {cmdName} reason {reason}")
                else:
                    logger.warn(f"_onRxFrameCB response not OkTo or fileUpload ... {decodedMsg.payload}")

            self.statsUnNumbered += 1
        # Call the decoded-message callback with the message
        if doRxCallback and self.decodedMsgCB is not None:
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
                if timeSinceSent > msgItem[1].get("timeOutSecs", self.msgRespTimeoutSecs):
                    if not msgItem[1].get("respValid", False):
                        msgIdxsTimedOut.append(msgItem[0])
                    msgIdxsToRemove.append(msgItem[0])

        # Debug
        for msgIdx in msgIdxsTimedOut:
            logger.warn(f"Message {msgIdx} timed out timeSent {self._msgsOutstanding[msgIdx].get('timeSent',0)} timeNow {time.time()}")

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
                if timeSinceSent > msgItem[1].get("timeOutSecs", self.msgRespTimeoutSecs):
                    if not msgItem[1].get("reptValid", False):
                        msgKeysTimedOut.append(msgItem[0])
                    msgKeysToRemove.append(msgItem[0])

        # Debug
        for msgKey in msgKeysTimedOut:
            logger.warn(f"rawQuery {msgKey} timed out at time {time.time()}")
            self.statsTimedOut += 1

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
