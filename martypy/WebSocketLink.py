'''
WebSocketLink
'''
import io
import struct
import secrets
import itertools
import collections
import logging
import time
from typing import Deque, Tuple

logger = logging.getLogger(__name__)

class WebSocketLink():

    max_size = 200000
    OPCODE_CONT = 0x00
    OPCODE_TEXT = 0x01
    OPCODE_BINARY = 0x02
    OPCODE_CLOSE = 0x08
    OPCODE_PING = 0x09
    OPCODE_PONG = 0x0a

    # DEBUG
    DEBUG_WEBSOCKET_LINK_DETAIL = False
    DEBUG_WEBSOCKET_LINK_FRAME_PROC = False
    DEBUG_WSL_DETAIL = False

    def __init__(self) -> None:
        self.curInputData: bytearray = bytearray()
        self.pongRequired = False
        self.pongData = bytearray()
        self.closeRequired = False
        self.textMsgs: Deque[str] = collections.deque()
        self.binaryMsgs: Deque[bytes] = collections.deque()
        self.statsPings = 0
        self.statsPongs = 0
        self.statsText = 0
        self.statsBinary = 0
        self.currentBinaryFrame = bytearray()
        self.currentTextFrame = str()

    def getPongRequired(self) -> bool:
        tmpPongReq = self.pongRequired
        self.pongRequired = False
        return tmpPongReq

    def getPongData(self) -> bytes:
        return self.pongData

    def getCloseRequired(self) -> bool:
        return self.closeRequired

    def getTextMsg(self) -> str | None:
        if len(self.textMsgs) > 0:
            return self.textMsgs.popleft()
        return None

    def getBinaryMsg(self) -> bytes | None:
        if len(self.binaryMsgs) > 0:
            binaryMsg = self.binaryMsgs.popleft()
            return binaryMsg
        return None
    
    def clear_decode_data(self) -> None:
        self.curInputData.clear()
        self.currentBinaryFrame = bytearray()
        self.currentTextFrame = str()

    def add_data_to_decode(self, data: bytes) -> None:
        '''
        Add data to be decoded
        Args:
            data bytes to add
        Returns:
            None
        '''
        # Add data
        self.curInputData += data
        if self.DEBUG_WEBSOCKET_LINK_DETAIL:
            logger.debug(f"Added len {len(data)}")
        while self._extractFrames():
            pass

    def _extractFrames(self) -> bool:
        # Debug
        # if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
        #     logger.debug(f"false len {len(self.curInputData)}\n{self.curInputData.hex()}")
        
        # Extract header info
        headerValid, fin, opcode, mask, frameLen, curPos = self.extract_header_info()
        if not headerValid:
            return False

        if frameLen > self.max_size:
            self.curInputData.clear()
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"CLEAR frameLen {frameLen} > max_size {self.max_size}")
            return False
        if mask and len(self.curInputData) < curPos + 4:
            return False
        if mask:
            self.mask_bytes = self.curInputData[curPos:curPos+4]
            curPos += 4

        # logger.debug(f"WebSocketLink _extractFrames fin {fin} opcode {opcode} mask {mask} frameLen {frameLen} curPos {curPos} len {len(self.curInputData)}")
                     
        # Check data is present
        if len(self.curInputData) < curPos + frameLen:
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"false len {len(self.curInputData)} < {curPos + frameLen}")
            return False
        rxDataBlock = self.curInputData[curPos : curPos + frameLen]
        if mask:
            rxDataBlock = self.applyMask(rxDataBlock, self.mask_bytes)
        
        # Remove data consumed
        self.curInputData = self.curInputData[curPos + frameLen:]
        if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
            logger.debug(f"GOT DATA BLOCK len {len(rxDataBlock)}")
            logger.debug(f"REMOVE DATA CONSUMED new len {len(self.curInputData)}")

        # Check opcode
        if opcode == self.OPCODE_PING:
            self.pongRequired = True
            self.pongData = rxDataBlock
            self.statsPings += 1
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"PING {rxDataBlock.hex()}")
            return True
        elif opcode == self.OPCODE_PONG:
            self.statsPongs += 1
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"PONG {rxDataBlock.hex()}")
            return True
        elif opcode == self.OPCODE_CLOSE:
            # logger.debug(f"wsFrame CLOSE")
            self.closeRequired = True
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"CLOSE {rxDataBlock.hex()}")
            return True
        elif opcode == self.OPCODE_BINARY:
            self.currentBinaryFrame += rxDataBlock
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"BINARY PART {self.currentBinaryFrame.hex() if self.DEBUG_WSL_DETAIL else ''}")
        elif opcode == self.OPCODE_TEXT:
            self.currentTextFrame += rxDataBlock.decode('latin-1', errors='ignore')
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"TEXT PART {rxDataBlock.hex()}")

        # Add completed frame to queue
        if fin:
            if opcode == self.OPCODE_TEXT:
                self.textMsgs.append(self.currentTextFrame)
                self.statsText += 1
            else:
                # logger.debug(f"wsFrame BINARY DONE {self.rxFrameData.hex()}")
                self.binaryMsgs.append(self.currentBinaryFrame)
                self.statsBinary += 1
            self.currentTextFrame = str()
            self.currentBinaryFrame = bytearray()
        return True
    
    def extract_header_info(self) -> Tuple[bool, bool, int, bool, int, int]:
        # Check at least 2 bytes are present
        if len(self.curInputData) < 2:
            if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                logger.debug(f"false len {len(self.curInputData)} < 2")
            return False, False, 0, False, 0, 0
        
        # Unpack header
        head1, head2 = struct.unpack("!BB", self.curInputData[:2])

        # Extract header info
        fin = (head1 & 0b10000000) != 0
        opcode = head1 & 0b00001111
        mask = (head2 & 0b10000000) != 0
        frameLen = head2 & 0b01111111
        curPos = 2
        if frameLen == 126:
            if len(self.curInputData) < 4:
                if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                    logger.debug(f"false len {len(self.curInputData)} < 4")
                return False, False, 0, False, 0, 0
            (frameLen,) = struct.unpack("!H", self.curInputData[2:4])
            curPos = 4
        elif frameLen == 127:
            if len(self.curInputData) < 10:
                if self.DEBUG_WEBSOCKET_LINK_FRAME_PROC:
                    logger.debug(f"false len {len(self.curInputData)} < 10")
                return False, False, 0, False, 0, 0
            (frameLen,) = struct.unpack("!Q", self.curInputData[2:10])
            curPos = 10
        return True, fin, opcode, mask, frameLen, curPos

    @classmethod
    def encode(cls, inFrame: bytes, useMask: bool,
                opcode: int, fin: bool) -> bytes:

        output = io.BytesIO()

        # Prepare the header.
        head1 = (0b10000000 if fin else 0) | opcode
        head2 = 0b10000000 if useMask else 0
        length = len(inFrame)
        if length < 126:
            output.write(struct.pack("!BB", head1, head2 | length))
        elif length < 65536:
            output.write(struct.pack("!BBH", head1, head2 | 126, length))
        else:
            output.write(struct.pack("!BBQ", head1, head2 | 127, length))

        if useMask:
            mask_bytes = secrets.token_bytes(4)
            output.write(mask_bytes)
            data = cls.applyMask(inFrame, mask_bytes)
        else:
            data = inFrame
        output.write(data)
        return output.getvalue()

    @classmethod
    def applyMask(cls, data: bytes, mask: bytes) -> bytes:
        if len(mask) != 4:
            return data
        return bytes(b ^ m for b, m in zip(data, itertools.cycle(mask)))
