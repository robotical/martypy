
import socket
import logging
from typing import Callable, Optional
from .WebSocketFrame import WebSocketFrame
import time

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

class WebSocket():

    maxSocketBytes = 2000
    MAX_RX_PREUPGRADE_LEN = 2000
    SOCKET_AWAITING_UPGRADE = 0
    SOCKET_UPGRADED = 1

    def __init__(self,
            onBinaryFrame: Callable[[bytes], None],
            onTextFrame: Callable[[str], None],
            onError: Callable[[str], None],
            onReconnect: Callable[[], None],
            ipAddrOrHostname: str,
            ipPort: int = 80,
            wsPath: str = "/ws",
            timeout: float = 5.0,
            autoReconnect: bool = True,
            reconnectRepeatSecs: int = 5.0) -> None:
        self.ipAddr = socket.gethostbyname(ipAddrOrHostname)
        self.wsPath = wsPath
        self.ipPort = ipPort
        self.timeout = timeout
        self.autoReconnect = autoReconnect
        self.reconnectRepeatSecs = reconnectRepeatSecs
        self.onBinaryFrame = onBinaryFrame
        self.onTextFrame = onTextFrame
        self.onError = onError
        self.onReconnect = onReconnect
        self._clear()

    def __del__(self) -> None:
        self.close()

    def open(self) -> bool:
        # Clear
        self._clear()
        # Open socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.ipAddr, self.ipPort))
        # Initiate upgrade
        self._sendUpgradeReq()

    def writeBinary(self, inFrame: bytes) -> int:
        if not self.sock:
            return 0
        frame = WebSocketFrame.encode(inFrame, False, WebSocketFrame.OPCODE_BINARY, True)
        # logger.debug(f"WebSocket write {''.join('{:02x}'.format(x) for x in frame)}")
        return self.sock.send(frame)

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except Exception as excp:
                logger.debug("WebSocket exception while closing", exc_info=True)
        self.sock = None

    def _sendUpgradeReq(self) -> None:
        if not self.sock:
            return
        headerStr = f"GET {self.wsPath} HTTP/1.1\r\n" + \
            "Connection: upgrade\r\n" + \
            "Upgrade: websocket\r\n" + \
            "\r\n"
        self.sock.send(headerStr.encode())

    def service(self) -> None:
        # Get any data
        reconnectRequired = False
        try:
            rxData = self.sock.recv(self.maxSocketBytes)
        except Exception as excp:
            logger.debug("WebSocket exception on recv:", exc_info=True)
            if not self.autoReconnect:
                raise excp
            reconnectRequired = True
        # Check for reconnect
        if reconnectRequired:
            if self.reconnectLastTime is None or time.time() > self.reconnectLastTime + self.reconnectRepeatSecs:
                self.close()
                try:
                    if self.onReconnect:
                        self.onReconnect()
                    self.open()
                    logger.debug("WebSocket reopened automatically")
                except Exception as excp:
                    logger.debug("WebSocket exception trying to reopen websocket:", exc_info=True)
                self.reconnectLastTime = time.time()
            else:
                time.sleep(0.01)
            return
        if self.sock is None:
            return
        # Check state of socket connection
        if self.socketState == self.SOCKET_AWAITING_UPGRADE:
            self.rxPreUpgrade += rxData
            # Check for upgrade header complete
            headerEndPos = self.rxPreUpgrade.find(b"\r\n\r\n")
            if headerEndPos > 0:
                # Check upgrade ok
                if b"Sec-WebSocket-Accept" in self.rxPreUpgrade:
                    self.socketState = self.SOCKET_UPGRADED
                    self.wsFrameCodec.addDataToDecode(self.rxPreUpgrade[headerEndPos+4:])
                    # logger.debug("WebSocket upgraded")
            elif len(self.rxPreUpgrade) > self.MAX_RX_PREUPGRADE_LEN:
                self.rxPreUpgrade.clear()
        else:
            self.wsFrameCodec.addDataToDecode(rxData)
            checkForData = True
            while checkForData:
                checkForData = False
                # Check for actions required
                if self.wsFrameCodec.getPongRequired():
                    # logging.debug("WebSocket sending pong")
                    self._sendPong()
                    checkForData = True
                binaryFrame = self.wsFrameCodec.getBinaryMsg()
                if binaryFrame:
                    checkForData = True
                    # logger.debug(f"WebSocket proc binary len {len(binaryFrame)}")
                    if self.onBinaryFrame:
                        self.onBinaryFrame(binaryFrame)
                textFrame = self.wsFrameCodec.getTextMsg()
                if textFrame and self.onTextFrame:
                    checkForData = True
                    self.onTextFrame(textFrame)

    def _sendPong(self) -> None:
        if not self.sock:
            return 0
        frame = WebSocketFrame.encode(self.wsFrameCodec.getPongData(),
                    False, WebSocketFrame.OPCODE_PONG, True)
        # logger.debug(f"WebSocket pong {''.join('{:02x}'.format(x) for x in self.wsFrameCodec.getPongData())}")
        return self.sock.send(frame)

    def _clear(self) -> None:
        self.sock = None
        self.socketState = self.SOCKET_AWAITING_UPGRADE
        self.reconnectLastTime = None
        self.rxPreUpgrade = bytearray()
        self.wsFrameCodec = WebSocketFrame()
