'''
Serial communications with a Robotical RIC
'''
from threading import Thread
from typing import Callable, Dict, Union
import serial
import time
import logging

from serial.serialutil import SerialException
from .LikeHDLC import LikeHDLC
from .ProtocolOverAscii import ProtocolOverAscii

logger = logging.getLogger(__name__)

class RICCommsSerial:
    '''
    RICCommsSerial
    Provides a serial interface for RIC communications
    '''
    def __init__(self) -> None:
        '''
        Initialise RICCommsSerial
        '''
        self.isOpen = False
        self.serialReader = None
        self.serialDevice = None
        self.serialThreadEn = False
        self.rxFrameCB = None
        self.logLineCB = None
        self._hdlc = LikeHDLC(self._onHDLCFrame, self._onHDLCError)
        self.overAscii = False
        self.serialLogLine = ""
        self.serialPortErrors = 0

    def __del__(self) -> None:
        '''
        Destructor
        '''
        self.close()

    def setRxFrameCB(self, onFrame: Callable[[Union[bytes, str]], None]) -> None:
        '''
        Set callback on frame received
        Args:
            onFrame: callback function (takes 1 parameter which is a received frame)
        Returns:
            None
        '''
        self.rxFrameCB = onFrame

    def setRxLogLineCB(self, onLogLine: Callable[[str], None]) -> None:
        '''
        Set callback on logging line received
        Args:
            onLogLine: callback function (takes 1 parameter which is the line of logging information)
        Returns:
            None
        '''
        self.logLineCB = onLogLine

    def open(self, openParams: Dict) -> bool:
        '''
        Open serial port
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
        # Check not already open
        if self.isOpen:
            return True

        # Get params
        serialPort = openParams.get("serialPort", "")
        serialBaud = openParams.get("serialBaud", 115200)
        self.overAscii = openParams.get("ifType", "plain") != "plain"
        if self.overAscii:
            self.protocolOverAscii = ProtocolOverAscii()

        # Validate
        if len(serialPort) == 0:
            return False

        # Open serial port
        self.serialDevice = serial.Serial(port=None, baudrate=serialBaud)
        self.serialDevice.port = serialPort
        self.serialDevice.rts = 0
        self.serialDevice.dtr = 0
        self.serialDevice.dsrdtr = False
        self.serialDevice.open()

        # Start receive loop
        self.serialThreadEn = True
        self.serialReader = Thread(target=self._serialRxLoop)
        self.serialReader.daemon = True
        self.serialReader.start()
        self.isOpen = True
        return True

    def close(self) -> None:
        '''
        Close serial port
        '''
        if not self.isOpen:
            return
        if self.serialReader is not None:
            self.serialThreadEn = False
            time.sleep(0.01)
            self.serialReader.join()
            self.serialReader = None
        if self.serialDevice is not None:
            self.serialDevice.close()
            self.serialDevice = None
        self.isOpen = False

    def send(self, data: bytes) -> None:
        '''
        Send data to serial port
        Args:
            data: bytes to send on serial port
        Returns:
            none
        Throws:
            SerialException: if the serial port has an error
        '''
        # logger.debug(f"Sending to IF len {len(bytesToSend)} {str(bytesToSend)}")
        hdlcEncoded = self._hdlc.encode(data)
        if self.overAscii:
            encodedFrame = ProtocolOverAscii.encode(hdlcEncoded)
            self._sendBytesToIF(encodedFrame)
            # logger.debug(f"{time.time()} {''.join('{:02x}'.format(x) for x in encodedFrame)}")
        else:
            self._sendBytesToIF(hdlcEncoded)

    def _serialRxLoop(self) -> None:
        '''
        Thread function used to process serial port data
        '''
        while self.serialThreadEn:
            i = self.serialDevice.in_waiting
            if i < 1:
                time.sleep(0.001)
                continue
            byt = self.serialDevice.read(i)
            for b in byt:
                if self.overAscii:
                    if b >= 128:
                        decodedVal = self.protocolOverAscii.decodeByte(b)
                        if decodedVal >= 0:
                            # logger.debug(f"{decodedVal:02x}")
                            self._hdlc.decodeData(decodedVal)
                    else:
                        if b == 0x0a:
                            if self.logLineCB:
                                self.logLineCB(self.serialLogLine)
                            self.serialLogLine = ""
                        else:
                            self.serialLogLine += chr(b)
                else:
                    self._hdlc.decodeData(b)
            # logger.debug(f"{time.time()} {''.join('{:02x}'.format(x) for x in byt)}")
        # logger.debug("Exiting serialRxLoop")

    def _onHDLCFrame(self, frame: bytes) -> None:
        if self.rxFrameCB is not None:
            self.rxFrameCB(frame)
        
    def _onHDLCError(self) -> None:
        pass
        
    def _sendBytesToIF(self, bytesToSend: bytes) -> None:
        # logger.debug(f"Sending to IF len {len(bytesToSend)} {str(bytesToSend)}")
        if not self.isOpen:
            return
        # logger.debug(f"{time.time()} {''.join('{:02x}'.format(x) for x in bytesToSend)}")
        if self.serialDevice is not None:
            try:
                self.serialDevice.write(bytesToSend)
            except SerialException as excp:
                # The port has connected but now failing to send characters
                # This may sort itself out or require user intervention
                self.serialPortErrors += 1
                pass
