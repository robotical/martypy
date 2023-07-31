'''
RICProtocols
'''
import json
import logging
import struct
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
        self.payload : Union[bytes, None] = None
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

    def setPayload(self, payload: bytes) -> None:
        self.payload = payload

    def getFilePos(self) -> int:
        if self.restType == RICProtocols.RICREST_ELEM_CODE_FILE_BLOCK:
            filePosStart = RICProtocols.RICREST_FILEBLOCK_FILEPOS_POS
            filePosEnd = filePosStart + RICProtocols.RICREST_FILEBLOCK_FILEPOS_POS_BYTES
            if self.payload is not None and len(self.payload) >= filePosEnd:
                filePos = struct.unpack(">I", self.payload[filePosStart:filePosEnd])
                return filePos[0]
        return 0
    
    def getBlockContents(self) -> bytes:
        if self.restType == RICProtocols.RICREST_ELEM_CODE_FILE_BLOCK:
            if self.payload is not None and len(self.payload) >= RICProtocols.RICREST_FILEBLOCK_PAYLOAD_POS:
                return self.payload[RICProtocols.RICREST_FILEBLOCK_PAYLOAD_POS:]
        return b""

    def getJSONDict(self) -> Dict:
        msgContent = {}
        if self.payload is not None:
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
        if self.payload is not None:
            msgStr += f"PayloadLen: {len(self.payload)}"
        return msgStr

class RICProtocols:
    '''
    RICProtocols
    Implements protocols used by RIC including RICSerial and RICREST
    '''
    # Robotical RIC Protocol definitions
    PROTOCOL_ROSSERIAL = 0x00
    PROTOCOL_M1SC = 0x01
    PROTOCOL_RICREST = 0x02
    PROTOCOL_BRIDGE_RICREST = 0x03
    RICREST_ELEM_CODE_URL = 0x00
    RICREST_ELEM_CODE_CMDRESPJSON = 0x01
    RICREST_ELEM_CODE_BODY = 0x02
    RICREST_ELEM_CODE_CMD_FRAME = 0x03
    RICREST_ELEM_CODE_FILE_BLOCK = 0x04
    REST_COMMANDS = ["url", "json", "body", "cmd", "fileBlk"]
    MSG_TYPE_COMMAND = 0x00
    MSG_TYPE_RESPONSE = 0x01
    MSG_TYPE_PUBLISH = 0x02
    MSG_TYPE_REPORT = 0x03
    MSG_TYPE_STRS = ["cmd", "resp", "publish", "report"]
    MSG_TYPE_BIT_POS = 6
    COMMSMSG_MSG_NUM_POS = 0
    COMMSMSG_PROTOCOL_POS = 1
    COMMSMSG_PAYLOAD_POS = 2
    RICREST_ELEM_CODE_POS = 0
    RICREST_PAYLOAD_POS = 1
    ROSSERIAL_PAYLOAD_POS = 0
    RICREST_FILEBLOCK_CHANNEL_POS = 0
    RICREST_FILEBLOCK_FILEPOS_POS = 0
    RICREST_FILEBLOCK_FILEPOS_POS_BYTES = 4
    RICREST_FILEBLOCK_PAYLOAD_POS = 4

    def __init__(self) -> None:
        self.ricSerialMsgNum = 1
        pass

    def encodeRICRESTURL(self, cmdStr: str) -> Tuple[bytes, int]:
        # RICSerial URL
        msgNum = self.ricSerialMsgNum
        cmdFrame = bytearray(
            [
                msgNum, 
                (self.MSG_TYPE_COMMAND << self.MSG_TYPE_BIT_POS) + self.PROTOCOL_RICREST, 
                self.RICREST_ELEM_CODE_URL
            ]
        )
        cmdFrame += cmdStr.encode() + b"\0"
        self.ricSerialMsgNum += 1
        if self.ricSerialMsgNum > 255:
            self.ricSerialMsgNum = 1
        return cmdFrame, msgNum

    def encodeRICRESTCmdFrame(self, cmdStr: Union[str,bytes], payload: Union[Union[bytes, str], None] = None) -> Tuple[bytes, int]:
        # RICSerial command frame
        msgNum = self.ricSerialMsgNum
        cmdFrame = bytearray(
            [
                msgNum, 
                (self.MSG_TYPE_COMMAND << self.MSG_TYPE_BIT_POS) + self.PROTOCOL_RICREST, 
                self.RICREST_ELEM_CODE_CMD_FRAME
            ]
        )
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
    
    def encodeRICRESTResp(self, msgNum: int, respStr: str) -> Tuple[bytes, int]:
        # RICSerial response
        cmdFrame = bytearray(
            [
                msgNum, 
                (self.MSG_TYPE_RESPONSE << self.MSG_TYPE_BIT_POS) + self.PROTOCOL_RICREST, 
                self.RICREST_ELEM_CODE_CMDRESPJSON
            ]
        )
        cmdFrame += respStr.encode() + b"\0"
        return cmdFrame, msgNum

    def encodeRICRESTFileBlock(self, cmdBuf: bytes) -> Tuple[bytes, int]:
        # RICSerial file block - not numbered
        cmdFrame = bytearray(
            [
                0, 
                (self.MSG_TYPE_COMMAND << self.MSG_TYPE_BIT_POS) + self.PROTOCOL_RICREST, 
                self.RICREST_ELEM_CODE_FILE_BLOCK
            ]
        )
        cmdFrame += cmdBuf
        return cmdFrame, 0
    
    def encodeBridgeMsg(self, msgToWrap: bytes, bridgeID: int) -> bytes:
        # Wrap a message in a bridge message - not numbered
        bridgeMsg = bytearray(
            [
                0,
                (self.MSG_TYPE_COMMAND << self.MSG_TYPE_BIT_POS) + self.PROTOCOL_BRIDGE_RICREST,
                bridgeID,
            ]
        )
        bridgeMsg += msgToWrap
        return bridgeMsg
    
    def decodeRICFrame(self, fr: bytes) -> DecodedMsg:
        msg = DecodedMsg()
        if len(fr) < 2:
            msg.setError(f"Frame too short {len(fr)} bytes")
        else:
            # Decode header
            msgNum = fr[self.COMMSMSG_MSG_NUM_POS]
            msg.setMsgNum(msgNum)
            protocol = fr[self.COMMSMSG_PROTOCOL_POS] & 0x3f
            msg.setProtocol(protocol)
            msgTypeCode = fr[self.COMMSMSG_PROTOCOL_POS] >> self.MSG_TYPE_BIT_POS
            msg.setMsgTypeCode(msgTypeCode)
            if protocol == self.PROTOCOL_RICREST:
                restElemCode = fr[self.COMMSMSG_PAYLOAD_POS + self.RICREST_ELEM_CODE_POS]
                msg.setRESTElemCode(restElemCode)
                if restElemCode == self.RICREST_ELEM_CODE_URL or restElemCode == self.RICREST_ELEM_CODE_CMDRESPJSON:
                    msg.setPayload(fr[self.COMMSMSG_PAYLOAD_POS + self.RICREST_PAYLOAD_POS:].rstrip(b'\x00'))
                else:
                    msg.setPayload(fr[self.COMMSMSG_PAYLOAD_POS + self.RICREST_PAYLOAD_POS:])
                # logging.debug(f"RICREST {RICProtocols.MSG_TYPE_STRS[msgTypeCode]} msgNum {msgNum} {fr.hex()}")
            elif protocol == self.PROTOCOL_BRIDGE_RICREST:
                # TODO: implement
                pass
            elif protocol == self.PROTOCOL_ROSSERIAL:
                msg.setPayload(fr[self.COMMSMSG_PAYLOAD_POS + self.ROSSERIAL_PAYLOAD_POS:])
            else:
                logging.debug(f"RICProtocols Unknown frame received {fr}")
        return msg
