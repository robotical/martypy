'''
RICProtocols
'''
import json
import logging
from typing import Dict, Tuple, Union

logger = logging.getLogger(__name__)

class DecodedMsg:
    '''
    DecodedMsg
    A message decoded from RIC
    '''
    def __init__(self) -> None:
        self.errMsg = ""
        self.msgNum = None
        self.protocolID = None
        self.isText = None
        self.payload : bytes | None = None
        self.restType = None
        self.msgTypeCode = None

    def setError(self, errMsg: str) -> None:
        self.errMsg = errMsg

    def setMsgNum(self, msgNum: int) -> None:
        self.msgNum = msgNum

    def setProtocol(self, protocolID: int) -> None:
        self.protocolID = protocolID

    def setMsgTypeCode(self, msgTypeCode: int) -> None:
        self.msgTypeCode = msgTypeCode

    def setRESTElemCode(self, restType: int) -> None:
        self.restType = restType

    def setPayload(self, isText: bool, payload: bytes) -> None:
        self.isText = isText
        self.payload = payload

    def getJSONDict(self) -> Dict:
        msgContent = {}
        if self.isText and self.payload is not None:
            try:
                payloadStr = self.payload.decode("utf-8")
                termPos = payloadStr.find("\0") if self.payload is not None else -1
                frameJson = self.payload
                if termPos >= 0:
                    frameJson = payloadStr[0:termPos]
                    binData = payloadStr[termPos+1:len(payloadStr)-1]
                else:
                    return msgContent
                msgContent = json.loads(frameJson)
            except Exception as excp:
                logging.debug("RICProtocols getJSONDict failed to extract JSON from", 
                            self.payload, "error", excp)
        # logging.debug("msgContent ", msgContent)
        return msgContent

    def toString(self) -> str:
        msgStr = ""
        if self.msgNum is not None:
            msgStr += f"MsgNum: {self.msgNum} "
        if self.protocolID is not None:
            msgStr += "Protocol:"
            if self.protocolID == RICProtocols.PROTOCOL_RICREST:
                msgStr += "RICREST"
            elif self.protocolID == RICProtocols.PROTOCOL_M1SC:
                msgStr += "M1SC"
            elif self.protocolID == RICProtocols.PROTOCOL_ROSSERIAL:
                msgStr += "ROSSERIAL"
            else:
                msgStr += f"OTHER {self.protocolID}"
            msgStr += " "
        if self.msgTypeCode is not None:
            msgStr += "MsgType:"
            if self.msgTypeCode >= 0 and self.msgTypeCode < len(RICProtocols.MSG_TYPE_STRS):
                msgStr += RICProtocols.MSG_TYPE_STRS[self.msgTypeCode]
            else:
                msgStr += f"OTHER {self.msgTypeCode}"
            msgStr += " "
        if self.restType is not None:
            msgStr += "Type:"
            if self.restType >= 0 and self.restType < len(RICProtocols.REST_COMMANDS):
                msgStr += RICProtocols.REST_COMMANDS[self.restType]
            else:
                msgStr += f"OTHER {self.restType}"
            msgStr += " "
        if self.isText is not None:
            if self.isText:
                msgStr += "Payload:" + str(self.payload)
            elif self.payload is not None:
                msgStr += f"PayloadLen: {len(self.payload)} "
        return msgStr

class RICProtocols:
    '''
    RICProtocols
    Implements protocols used by RIC including RICSerial and RICREST
    '''
    # Robotical RIC Protocol definitions
    MSG_TYPE_COMMAND = 0x00
    PROTOCOL_ROSSERIAL = 0x00
    PROTOCOL_M1SC = 0x01
    PROTOCOL_RICREST = 0x02
    RICREST_ELEM_CODE_URL = 0x00
    RICREST_ELEM_CODE_JSON = 0x01
    RICREST_ELEM_CODE_BODY = 0x02
    RICREST_ELEM_CODE_CMD_FRAME = 0x03
    RICREST_ELEM_CODE_FILE_BLOCK = 0x04
    REST_COMMANDS = ["url", "json", "body", "cmd", "fileBlk"]
    MSG_TYPE_COMMAND = 0x00
    MSG_TYPE_RESPONSE = 0x01
    MSG_TYPE_PUBLISH = 0x02
    MSG_TYPE_REPORT = 0x03
    MSG_TYPE_STRS = ["cmd", "resp", "publish", "report"]

    def __init__(self) -> None:
        self.ricSerialMsgNum = 1
        pass

    def encodeRICRESTURL(self, cmdStr: str) -> Tuple[bytes, int]:
        # RICSerial URL
        msgNum = self.ricSerialMsgNum
        cmdFrame = bytearray([msgNum, self.MSG_TYPE_COMMAND + self.PROTOCOL_RICREST, self.RICREST_ELEM_CODE_URL])
        cmdFrame += cmdStr.encode() + b"\0"
        self.ricSerialMsgNum += 1
        if self.ricSerialMsgNum > 255:
            self.ricSerialMsgNum = 1
        return cmdFrame, msgNum

    def encodeRICRESTCmdFrame(self, cmdStr: Union[str,bytes], payload: Union[bytes, str] | None = None) -> Tuple[bytes, int]:
        # RICSerial command frame
        msgNum = self.ricSerialMsgNum
        cmdFrame = bytearray([msgNum, self.MSG_TYPE_COMMAND + self.PROTOCOL_RICREST, self.RICREST_ELEM_CODE_CMD_FRAME])
        if type(cmdStr) is str:
            cmdFrame += cmdStr.encode()
        elif type(cmdStr) is bytes:
            cmdFrame += cmdStr
        if cmdFrame[-1] != b"\0":
            cmdFrame = cmdFrame + b"\0"
        if payload is not None:
            if type(payload) is str:
                cmdFrame += payload.encode()
            elif type(payload) is bytes:
                cmdFrame += payload
        self.ricSerialMsgNum += 1
        if self.ricSerialMsgNum > 255:
            self.ricSerialMsgNum = 1
        return cmdFrame, msgNum

    def encodeRICRESTFileBlock(self, cmdBuf: bytes) -> Tuple[bytes, int]:
        # RICSerial file block - not numbered
        cmdFrame = bytearray([0, self.MSG_TYPE_COMMAND + self.PROTOCOL_RICREST, self.RICREST_ELEM_CODE_FILE_BLOCK])
        cmdFrame += cmdBuf
        return cmdFrame, 0

    def decodeRICFrame(self, fr: bytes) -> DecodedMsg:
        msg = DecodedMsg()
        if len(fr) < 2:
            msg.setError(f"Frame too short {len(fr)} bytes")
        else:
            # Decode header
            msgNum = fr[0]
            msg.setMsgNum(msgNum)
            protocol = fr[1] & 0x3f
            msg.setProtocol(protocol)
            msgTypeCode = fr[1] >> 6
            msg.setMsgTypeCode(msgTypeCode)
            if protocol == self.PROTOCOL_RICREST:
                restElemCode = fr[2]
                msg.setRESTElemCode(restElemCode)
                if restElemCode == self.RICREST_ELEM_CODE_URL or restElemCode == self.RICREST_ELEM_CODE_JSON:
                    payload = fr[3:].rstrip(b'\x00')
                    msg.setPayload(True, payload)
                else:
                    msg.setPayload(False, fr[3:])
                # logging.debug(f"RICREST {RICProtocols.MSG_TYPE_STRS[msgTypeCode]} msgNum {msgNum} {fr.hex()}")
            elif protocol == self.PROTOCOL_ROSSERIAL:
                msg.setPayload(False, fr[2:])
            else:
                logging.debug(f"RICProtocols Unknown frame received {fr}")
        return msg
