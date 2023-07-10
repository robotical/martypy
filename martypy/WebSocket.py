
import socket
import logging
from typing import Callable, Optional
from .WebSocketLink import WebSocketLink
import time

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

class WebSocket():

    maxSocketBytes = 10000
    MAX_RX_PREUPGRADE_LEN = 10000
    SOCKET_AWAITING_UPGRADE = 0
    SOCKET_UPGRADED = 1
    CONN_TIMEOUT_IF_NON_BLOCKING_SECS = 5.0
    SEND_TIMEOUT_IF_NON_BLOCKING_SECS = 0.5

    # Debug
    DEBUG_WEBSOCKET_OPEN_CLOSE = False
    DEBUG_RECEIVE_ERRORS = False
    DEBUG_WEBSOCKET_DETAIL = False

    def __init__(self,
            onBinaryFrame: Callable[[bytes], None],
            onTextFrame: Callable[[str], None],
            onError: Callable[[str], None],
            onReconnect: Callable[[], None],
            ipAddrOrHostname: str,
            ipPort: int = 80,
            wsPath: str = "/ws",
            timeout: float = 0.0,
            autoReconnect: bool = True,
            reconnectRepeatSecs: float = 5.0) -> None:
        try:
            self.ipAddr = socket.gethostbyname(ipAddrOrHostname)
        except socket.error as e:
            logger.error(f"WebSocket failed to get IP address {e}")
            # Ignore the error at this point and fail later as failure in the
            # constructor can be very confusing
        self.wsPath = wsPath
        self.ipPort = ipPort
        self.timeout = timeout
        self.autoReconnect = autoReconnect
        self.reconnectRepeatSecs = reconnectRepeatSecs
        self.onBinaryFrame = onBinaryFrame
        self.onTextFrame = onTextFrame
        self.onError = onError
        self.onReconnect = onReconnect
        self.sock = None
        self.socketState = self.SOCKET_AWAITING_UPGRADE
        self.reconnectLastTime = None
        self.rxPreUpgrade = bytearray()
        self.webSocketLink = WebSocketLink()

    def __del__(self) -> None:
        self.close()

    def open(self) -> bool:
        # Debug
        debugStartTime = time.time()

        # Reinit
        self.socketState = self.SOCKET_AWAITING_UPGRADE
        self.reconnectLastTime = None
        self.rxPreUpgrade = bytearray()
        self.webSocketLink = WebSocketLink()

        # Create socket
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as e: 
            logger.error(f"WebSocket failed to create socket {e}")
            return False

        # Set timeout for connection
        if self.timeout == 0:
            self.sock.settimeout(self.CONN_TIMEOUT_IF_NON_BLOCKING_SECS)
        else:
            self.sock.settimeout(self.timeout)

        # Connect socket
        try:
            self.sock.connect((self.ipAddr, self.ipPort))
        except socket.error as e:
            logger.error(f"WebSocket failed to connect to {self.ipAddr}:{self.ipPort} {e}")
            return False

        # Set timeout (0.0 sets non-blocking mode)
        try:
            self.sock.settimeout(self.timeout)
            if self.DEBUG_WEBSOCKET_OPEN_CLOSE:
                logger.debug(f"WebSocket timeout set to {self.timeout}{' == non-blocking' if self.timeout == 0 else ' === blocking'}")
        except socket.error as e:
            logger.warning(f"WebSocket failed to set timeout {e}")
        
        # Debug
        if self.DEBUG_WEBSOCKET_OPEN_CLOSE:
            logger.debug(f"WebSocket open {self.ipAddr}:{self.ipPort} took {time.time() - debugStartTime}")

        # Initiate upgrade
        debugStartTime = time.time()
        return self._sendUpgradeReq()

    def writeBinary(self, inFrame: bytes) -> int:
        if not self.sock:
            return 0
        frame = WebSocketLink.encode(inFrame, False, WebSocketLink.OPCODE_BINARY, True)
        # logger.debug(f"WebSocket write {frame.hex()}")
        return self._sendToSocket(frame)

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
                if self.DEBUG_WEBSOCKET_OPEN_CLOSE:
                    logger.debug(f"WebSocket closed socket")
            except Exception as excp:
                logger.warn("WebSocket exception while closing", exc_info=True)
        self.sock = None

    def _sendUpgradeReq(self) -> bool:
        if not self.sock:
            return False
        headerStr = f"GET {self.wsPath} HTTP/1.1\r\n" + \
            "Connection: upgrade\r\n" + \
            "Upgrade: websocket\r\n" + \
            "\r\n"
        try:
            self._sendToSocket(headerStr.encode())
        except socket.error as e:
            logger.error(f"WebSocket failed to upgrade {e}")
            return False
        return True

    def service(self) -> None:
        # Get any data
        reconnectRequired = False
        rxData = None
        if self.sock is None:
            return
        try:
            rxData = self.sock.recv(self.maxSocketBytes)
            if self.DEBUG_WEBSOCKET_DETAIL and len(rxData) > 0:
                logger.debug(f"WebSocket recv {len(rxData)} bytes {rxData.hex()}")
        except TimeoutError:
            pass
        except BlockingIOError:
            pass
        except ConnectionResetError as excp:
            if self.DEBUG_WEBSOCKET_DETAIL:
                logger.debug(f"WebSocket recv connection reset ------------------------------")
            if not self.autoReconnect:
                raise excp
            reconnectRequired = True
        except Exception as excp:
            if self.DEBUG_RECEIVE_ERRORS:
                logger.debug("WebSocket exception on recv:", exc_info=True)
            if not self.autoReconnect:
                raise excp
            reconnectRequired = True
            logger.debug("WebSocket reconnect required")
        # Check for reconnect
        if reconnectRequired:
            if self.reconnectLastTime is None or time.time() > self.reconnectLastTime + self.reconnectRepeatSecs:
                logger.debug("WebSocket closing for reconnect attempt")
                self.close()
                try:
                    logger.debug("WebSocket attempting to reopen")
                    self.open()
                    if self.onReconnect:
                        self.onReconnect()
                    logger.debug("WebSocket reopened automatically")
                except Exception as excp:
                    logger.debug("WebSocket exception trying to reopen websocket:", exc_info=True)
                self.reconnectLastTime = time.time()
            else:
                time.sleep(0.01)
            return
        if self.sock is None or rxData is None or len(rxData) == 0:
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
                    self.webSocketLink.add_data_to_decode(self.rxPreUpgrade[headerEndPos+4:])
                    # logger.debug("WebSocket upgraded")
            elif len(self.rxPreUpgrade) > self.MAX_RX_PREUPGRADE_LEN:
                self.rxPreUpgrade.clear()
        else:
            if self.DEBUG_WEBSOCKET_DETAIL:
                logger.debug(f"WebSocket processing data len {len(rxData)}")
            self.webSocketLink.add_data_to_decode(rxData)
            checkForData = True
            while checkForData:
                checkForData = False
                # Check for actions required
                if self.webSocketLink.getPongRequired():
                    # logging.debug("WebSocket sending pong")
                    self._sendPong()
                    checkForData = True
                binaryFrame = self.webSocketLink.getBinaryMsg()
                if binaryFrame:
                    checkForData = True
                    if self.DEBUG_WEBSOCKET_DETAIL:
                        logger.debug(f"WebSocket proc binary len {len(binaryFrame)}")
                    if self.onBinaryFrame:
                        self.onBinaryFrame(binaryFrame)
                textFrame = self.webSocketLink.getTextMsg()
                if textFrame:
                    checkForData = True
                    if self.DEBUG_WEBSOCKET_DETAIL:
                        logger.debug(f"WebSocket proc text len {len(textFrame)}")
                    if self.onTextFrame:
                        self.onTextFrame(textFrame)

    def _sendPong(self) -> None:
        if self.sock is None:
            return
        frame = WebSocketLink.encode(self.webSocketLink.getPongData(),
                    False, WebSocketLink.OPCODE_PONG, True)
        if self.DEBUG_WEBSOCKET_DETAIL:
            logger.debug(f"WebSocket pong {frame.hex()}")
        self._sendToSocket(frame)

    def _sendToSocket(self, frame: bytes) -> int:
        if self.DEBUG_WEBSOCKET_DETAIL:
            logger.debug(f"WebSocket send {len(frame)} bytes {frame.hex()}")
        if self.sock is None:
            return 0
        time_start = time.time()
        while time.time() - time_start < self.SEND_TIMEOUT_IF_NON_BLOCKING_SECS:
            try:
                return self.sock.send(frame)
            except BlockingIOError:
                pass
        return 0
