'''
RICInterface
'''
from typing import Callable, Dict, Union, Optional
import time
import threading
import logging
import json
import os

from .ValueAverager import ValueAverager
from .RICProtocols import DecodedMsg, RICProtocols
from .RICCommsBase import RICCommsBase
from .RateAverager import RateAverager

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
        # File handling
        from .RICFileHandler import RICFileHandler
        self._ricFileHandler = RICFileHandler(self)
        # Streaming
        from .RICStreamHandler import RICStreamHandler
        self._ricStreamHandler = RICStreamHandler(self)
        # Debug
        self.DEBUG_RIC_SEND_MSG = False
        self.DEBUG_RIC_RECEIVE_MSG = False
        self.DEBUG_PERFORMANCE = False
        self.DEBUG_RIC_RECEIVE_MSG_ROSSERIAL = False
        self.DEBUG_RIC_RECEIVE_SHOW_CONTENT = False
        self.DEBUG_RIC_RECEIVE_UNNUMBERED_MSG = False

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

        # Set default timeout based on interface
        self.msgRespTimeoutSecs = self.commsHandler.getMsgRespTimeoutSecs(self.msgRespTimeoutSecs)

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

    def isOpen(self) -> bool:
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
        if self.DEBUG_RIC_SEND_MSG:
            logger.debug(f"sendRICRESTURL msgNum {msgNum} time {time.time()} msg {msg}")
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
        msgSendTime = time.time()
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        if self.DEBUG_RIC_SEND_MSG:
            logger.debug(f"cmdRICRESTURLSync msgNum {msgNum} timeout {timeOutSecs} msg {msg}")
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": msgSendTime, "timeOutSecs": timeOutSecs, "awaited":True}
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        # Wait for result
        return self.waitForSyncResult(msgNum, msgSendTime, timeOutSecs)

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

    def sendRICRESTCmdFrameNoResp(self, msg: Union[str,bytes], 
                    payload: Union[bytes, str, None] = None) -> bool:
        '''
        Send RICREST command frame message without expecting a response
        Args:
            msg: string or bytes containing command frame
            payload: optional payload
        Returns:
            True if message sent
        '''
        ricRestMsg, msgNum = self.ricProtocols.encodeRICRESTCmdFrame(msg, payload)
        if self.DEBUG_RIC_SEND_MSG:
            logger.debug(f"sendRICRESTCmdFrameNoResp msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        return True

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
        if self.DEBUG_RIC_SEND_MSG:
            logger.debug(f"sendRICRESTCmdFrame msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": time.time(), "timeOutSecs": timeOutSecs}
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        return True

    def sendRICRESTCmdFrameSync(self, msg: Union[str,bytes], 
                    payload: Union[bytes, str] | None = None,
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
        if self.DEBUG_RIC_SEND_MSG:
            logger.debug(f"sendRICRESTCmdFrameSync msgNum {msgNum} len {len(ricRestMsg)} msg {msg}")
        msgSendTime = time.time()
        timeOutSecs = timeOutSecs if timeOutSecs is not None else self.msgRespTimeoutSecs
        with self._msgsOutstandingLock:
            self._msgsOutstanding[msgNum] = {"timeSent": msgSendTime, "timeOutSecs": timeOutSecs, "awaited":True}
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        # Wait for result
        return self.waitForSyncResult(msgNum, msgSendTime, timeOutSecs)

    def waitForSyncResult(self, msgNum: int, msgSendTime: float, timeOutSecs: float):
        while time.time() < msgSendTime + timeOutSecs:
            with self._msgsOutstandingLock:
                # Should be an outstanding message - if not there's a problem
                if msgNum not in self._msgsOutstanding:
                    logger.warning(f"sendRICRESTURLSync msgNum {msgNum} not in _msgsOutstanding")
                    return {"rslt":"failResponse"}
                # Check if response received
                if self._msgsOutstanding[msgNum].get("respValid", False):
                    respStr = DecodedMsg()
                    try:
                        # Get response
                        respStr = self._msgsOutstanding[msgNum].get("resp", None)
                        respObj = {}
                        if respStr:
                            respObj = json.loads(respStr.payload.decode("utf-8"))
                        # debugMsgRespTime = self._msgsOutstanding[msgNum].get("respTime", 0)
                        # logger.debug(f"waitForSyncResult msgNum {msgNum} msg {msg} resp {json.dumps(respObj)} sendTime {msgSendTime} respTime {debugMsgRespTime}")
                        return respObj
                    except Exception as excp:
                        logger.warning(f"sendRICRESTURLSync msgNum {msgNum} response is not JSON {respStr.payload}", exc_info=True)
            time.sleep(0.01)
        # Debug - if we get here we timed out
        logger.warning(f"waitForSyncResult failTimeout msgNum {msgNum} sendTime {msgSendTime} timeNow {time.time()} timeout {timeOutSecs}")
        return {"rslt":"failTimeout"}

    # Send RICREST response
    def sendRICRESTResp(self, msgNum: int, msg: str) -> bool:
        '''
        Send RICREST response message
        Args:
            msgNum: message number
            msg: string containing response
            payload: optional payload
        Returns:
            True if message sent
        '''
        # Encode frame
        ricRestMsg, _ = self.ricProtocols.encodeRICRESTResp(msgNum, msg)
        self.commsHandler.send(ricRestMsg)
        self.msgTxRate.addSample()
        return True
    
    # Send RICREST file block
    def sendRICRESTFileBlock(self, data: bytes) -> bool:
        '''
        Send RICREST file block
        Args:
            data: bytes of file data
        Returns:
            True if message sent
        '''
        ricRestMsg, _ = self.ricProtocols.encodeRICRESTFileBlock(data)
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
        if self.DEBUG_PERFORMANCE:
            logger.debug(f"RTTime {self.roundTripInfo.getAvg()}")

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

    def sendFile(self, filename: str, 
                progressCB: Callable[[int, int, 'RICInterface'], bool] | None = None,
                fileDest: str = "fs", reqStr: str = '') -> bool:
        '''
        Send a file (from the file system)
        Args:
            filename: name of file to send
            progressCB: callback used to indicate how file send is progressing, callable takes three params
                    which are bytesSent, totalBytes and the interface to RIC (of type RICInterface) and
                    returns a bool which should be True to continue the file upload or False to abort
            fileDest: "fs" to upload to file system, "ricfw" for new RIC firmware
            reqStr: API request used for transfer, if left blank this is inferred from fileDest, other
                    values include "fileupload" and "espfwupdate" - see RIC documentation for API
        Returns:
            True if operation succeeded
        Throws:
            OSError: operating system exceptions
            May throw other exceptions so include a general exception handler
        '''
        return self._ricFileHandler.sendFile(filename, progressCB, fileDest, reqStr)
    
    def getFileContents(self, filename: str,
                progressCB: Callable[[int, int, 'RICInterface'], bool] | None = None,
                file_src: str = 'fs',
                req_str: str = '') -> bytearray | None:
        '''
        Send a file (from the file system)
        Args:
            filename: name of file to send
            progressCB: callback used to indicate how file send is progressing, callable takes three params
                    which are bytesSent, totalBytes and the interface to RIC (of type RICInterface) and
                    returns a bool which should be True to continue the file upload or False to abort
            file_src: "fs" to download from file system, "martycam" for camera files
            req_str: API request used for transfer, if left blank this is inferred from fileDest, other
                    values include "filedownload" and "martycam"
        Returns:
            True if operation succeeded
        Throws:
            OSError: operating system exceptions
            May throw other exceptions so include a general exception handler
        '''
        return self._ricFileHandler.getFileContents(filename, progressCB, file_src, req_str)

    def streamSoundFile(self, fileName: str, targetEndpoint: str,
                progressCB: Callable[[int, int, 'RICInterface'], bool] | None = None) -> bool:
        '''
        Stream sound from the file system
        Args:
            fileName: The file to stream
            progressCB: callback used to indicate how stream is progressing, callable takes three params
                    which are bytesSent, totalBytes and the interface to RIC (of type RICInterface) and
                    returns a bool which should be True to continue the stream or False to abort
        Returns:
            True if operation succeeded
        Throws:
            OSError: operating system exceptions
            May throw other exceptions so include a general exception handler
        '''
        return self._ricStreamHandler.streamSoundFile(fileName, targetEndpoint, progressCB)

    def getStats(self) -> Dict:
        return {
            "roundTripAvgMS":self.roundTripInfo.getAvg()*1000,
            "msgRxRatePS":self.msgRxRate.getAvg(),
            "msgTxRatePS":self.msgTxRate.getAvg(),
            "unmatched":self.statsUnMatched,
            "matched":self.statsMatched,
            "unnumbered":self.statsUnNumbered,
            "timedOut":self.statsTimedOut,
            "uploadBPS":self._ricFileHandler.getUploadBytesPS(),
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

        # Keep track of whether a callback is needed after decoding the message
        doRxCallback = True

        # Update stats
        self.msgRxRate.addSample()

        # Decode the message
        decodedMsg = self.ricProtocols.decodeRICFrame(frame)

        # Debugging
        if self.DEBUG_RIC_RECEIVE_MSG and \
            ((decodedMsg.protocolID != RICProtocols.PROTOCOL_ROSSERIAL) or self.DEBUG_RIC_RECEIVE_MSG_ROSSERIAL):
            # logger.debug(f"_onRxFrameCB {decodedMsg.toString()} data {frame.hex()}")
            # if decodedMsg.protocolID != RICProtocols.PROTOCOL_ROSSERIAL:
            logger.debug(f"_onRxFrameCB {decodedMsg.toString()}" + 
                    (f" data {frame.hex()}" if self.DEBUG_RIC_RECEIVE_SHOW_CONTENT else ""))

        # Handle numbered messages (these are used for commands and responses)
        if decodedMsg.msgNum != 0:

            # Numbered message - generally a response to a REST API command
            if self.DEBUG_RIC_RECEIVE_MSG:
                logger.debug(f"_onRxFrameCB msgNum {decodedMsg.msgNum} {decodedMsg.payload}")

            # Update tracking of outstanding numbered messages
            isUnmatched = False
            with self._msgsOutstandingLock:
                if decodedMsg.msgNum in self._msgsOutstanding:

                    # Message matches a request we sent
                    msgRec = self._msgsOutstanding[decodedMsg.msgNum]
                    roundTripTime = time.time() - msgRec["timeSent"]
                    self.newRoundTrip(roundTripTime)
                    if not msgRec.get("awaited", False):

                        # Message response was not awaited
                        self._msgsOutstanding.pop(decodedMsg.msgNum)
                    else:

                        # Message response expected so update with response data
                        msgRec["resp"] = decodedMsg
                        msgRec["respValid"] = True
                        msgRec["respTime"] = time.time()

                    # Update stats
                    self.statsMatched += 1
                else:

                    # Message does not match a request we sent
                    isUnmatched = True
                    self.statsUnMatched += 1

            # Warn on unmatched messages
            if isUnmatched:
                logger.warning(f"_onRxFrameCB Unmatched msgNum {decodedMsg.msgNum}")

            # Perform a callback if the message was unmatched
            doRxCallback = isUnmatched

        # Unnumbered messages (reports, some responses and data blocks are unnumbered)
        elif decodedMsg.payload is not None:

            # Debug
            if self.DEBUG_RIC_RECEIVE_UNNUMBERED_MSG:
                logger.debug(f"_onRxFrameCB unnumbered {decodedMsg.toString()}")

            # Handle reports
            if decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_REPORT:

                # Report message - this can include results of accessing addOns
                # Report messages have JSON payloads
                # logger.debug(f"_onRxFrameCB REPORT {decodedMsg.payload}")
                reptObj = {}
                try:
                    reptObj = json.loads(decodedMsg.payload.decode("utf-8"))
                except Exception as excp:
                    logger.warning(f"_onRxFrameCB REPORT is not JSON {excp}")

                # Check for a message key (this is used to match a message sent to a HWElem)
                msgKey = reptObj.get("msgKey", '')
                if type(msgKey) is str:
                    try:
                        msgKey = int(msgKey)
                    except:
                        msgKey = 0

                # Message key should not be 0
                if msgKey != 0:

                    # Match up with a Raw Query message (used to query HWElem data)
                    isUnmatched = False
                    with self._rawQueryOutstandingLock:
                        if msgKey in self._rawQueryOutstanding:
                            msgRec = self._rawQueryOutstanding[msgKey]
                            if not msgRec.get("awaited", False):

                                # Not awaited so remove from outstanding list
                                self._rawQueryOutstanding.pop(msgKey)
                            else:

                                # Update with response data
                                msgRec["reptObj"] = reptObj
                                msgRec["reptValid"] = True
                        else:
                            isUnmatched = True

                    # Unmatched messages are logged
                    if isUnmatched:
                        logger.debug(f"Unmatched msgKey {msgKey}")
                    doRxCallback = isUnmatched

            # Response messages - used in file transfers and streaming
            elif decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_RESPONSE:

                # Debug
                if self.DEBUG_RIC_RECEIVE_MSG:
                    logger.debug(f"RESPONSE received {decodedMsg.payload}")

                # Check for okto/sokto messages used for streaming/transfer
                # These have JSON payloads
                reptObj = {}
                try:
                    reptObj = json.loads(decodedMsg.payload.decode("utf-8"))
                except Exception as excp:
                    logger.warning(f"_onRxFrameCB RESPONSE is not JSON {excp}")

                # Check for okto/sokto messages
                if "okto" in reptObj:
                    self._ricFileHandler.onOkto(reptObj)
                elif "sokto" in reptObj:
                    self._ricStreamHandler.onSokto(reptObj)

                # Check if cmdName is present
                elif "cmdName" in reptObj:

                    # Handle stream/transfer messages
                    cmdName = reptObj.get("cmdName","")
                    reason = "Unknown"
                    cmdNameList = ["ufBlock", "ufStatus", "ufCancel", "dfBlock", "dfStatus", "dfCancel"]
                    if cmdName in cmdNameList:
                        reason = self._ricFileHandler.onCmd(reptObj)
                    logger.warning(f"_onRxFrameCB {cmdName} reason {reason}")

                # Check for rslt messages
                elif "rslt" in reptObj:

                    # Handle failures
                    if reptObj["rslt"].startswith("fail"):
                        logger.warning(f"_onRxFrameCB {reptObj['rslt']}")
                        self._ricStreamHandler.onFail(reptObj)
                        self._ricFileHandler.onFail(reptObj)

                # Not a response we can handle
                else:
                    logger.warning(f"_onRxFrameCB response not OkTo or fileUpload ... {decodedMsg.payload}")

            # Data block messages
            elif decodedMsg.msgTypeCode == RICProtocols.MSG_TYPE_COMMAND:

                # Check for a data block
                if decodedMsg.restType == RICProtocols.RICREST_ELEM_CODE_FILE_BLOCK:

                    # Handle data block
                    self._ricFileHandler.onDataBlock(decodedMsg)


            # Stats update
            self.statsUnNumbered += 1

        # Call the decoded-message callback with the message if required
        if doRxCallback and self.decodedMsgCB is not None:
            self.decodedMsgCB(decodedMsg, self)

    def _onLogLineCB(self, line: str) -> None:
        if self.logLineCB:
            self.logLineCB(line.rstrip())

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

        # Hint to comms layer if messages are failing
        if len(msgIdxsTimedOut) > 0:
            self.commsHandler.hintMsgTimeout(len(msgIdxsTimedOut))

        # Debug
        for msgIdx in msgIdxsTimedOut:
            logger.warning(f"Message {msgIdx} timed out timeSent {self._msgsOutstanding[msgIdx].get('timeSent',0)} timeNow {time.time()}")

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
            logger.warning(f"rawQuery {msgKey} timed out at time {time.time()}")
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

