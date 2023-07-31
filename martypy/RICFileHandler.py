'''
RICFileHandler
'''
import threading
from typing import Callable, Union
from martypy import RICInterface
from .RICProtocols import DecodedMsg
from .Exceptions import MartyTransferException
import logging
import os
import time
from .ValueAverager import ValueAverager

logger = logging.getLogger(__name__)

class RICFileHandler:

    def __init__(self, ricInterface: 'RICInterface.RICInterface'):
        # Stream vars
        self._ricInterface = ricInterface
        # File send vars
        self._send_file_failed = False
        self._send_file_fail_reason = ""
        self._ota_update_start_ok = False
        self._file_send_ok_to = 0
        self._file_send_new_ok_to_received = False
        # File receive vars
        self._file_recv_last_block = bytearray()
        self._file_recv_last_pos = 0
        self._file_recv_lock = threading.Lock()
        self._file_recv_bridgeID = None
        # File transfer settings
        self.OVERALL_FILE_TRANSFER_TIMEOUT = 600
        self.BLOCK_ACK_TIMEOUT = 15
        self.BATCH_RETRY_MAX = 3
        # Debug
        self.DEBUG_SEND_FILE_BLOCK = False
        self.DEBUG_SEND_FILE = False
        self.DEBUG_RECEIVE_FILE_BLOCK = False
        self.DEBUG_RECEIVE_FILE = False
        # Stats
        self.uploadBytesPerSec = ValueAverager()

    def sendFile(self, file_name: str, 
                progressCB: Union[Callable[[int, int, 'RICInterface.RICInterface'], bool], None] = None,
                fileDest: str = "fs", req_str: str = '') -> bool:
        
        # Check validity
        try:
            file_stat = os.stat(file_name)
        except OSError as e:
            raise MartyTransferException("File not found")
                
        # Send the file using the file upload
        with open(file_name, "rb") as file_obj:

            # Get file info
            file_length = file_stat.st_size

            # Debug
            if self.DEBUG_SEND_FILE:
                logger.debug(f"File {file_name} is {file_length} bytes long")

            # Check if we're uploading firmware
            is_firmware = fileDest == "ricfw"
            if req_str == '':
                req_str = 'espfwupdate' if is_firmware else 'fileupload'
            upload_name = "fw" if is_firmware else os.path.basename(file_name)
            self._send_file_failed = False
            self._send_file_fail_reason = ""
            self._ota_update_start_ok = False

            # Block and batch sizes
            block_max_size = self._ricInterface.commsHandler.commsParams.fileTransfer.get("fileBlockMax", 5000)
            batch_ack_size = self._ricInterface.commsHandler.commsParams.fileTransfer.get("fileBatchAck", 1)

            # Debug
            if self.DEBUG_SEND_FILE:
                logger.debug(f"ricIF sendFile ideal blockMaxSize {block_max_size} batchAckSize {batch_ack_size}")

            # Frames follow the approach used in the web interface start, block..., end
            send_file_req = '{' + f'"cmdName":"ufStart","reqStr":"{req_str}","fileType":"{fileDest}",' + \
                            f'"batchMsgSize":{block_max_size},"batchAckSize":{batch_ack_size},' + \
                            f'"fileName":"{upload_name}","fileLen":{str(file_length)}' + '}'
            resp = self._ricInterface.sendRICRESTCmdFrameSync(send_file_req, timeOutSecs = 10)
            if resp.get("rslt","") != "ok":
                raise MartyTransferException("File transfer start not acknowledged")

            # Block and batch sizes
            block_max_size = resp.get("batchMsgSize", block_max_size)
            batch_ack_size = resp.get("batchAckSize", 50)
            self._file_send_ok_to = 0

            # Debug
            if self.DEBUG_SEND_FILE:
                logger.debug(f"ricIF sendFile negotiated blockMaxSize {block_max_size} batchAckSize {batch_ack_size} resp {resp}")

            # Progress and check for abort
            if self._sendFileProgressCheckAbort(progressCB, self._file_send_ok_to, file_length):
                return False

            # Wait for a period depending on whether we're sending firmware - this is because starting
            # a firmware update involves the ESP32 in a long-running activity and the firmware becomes
            # unresponsive during this time
            if is_firmware:
                for i in range(5):
                    time.sleep(1)
                    if self._sendFileProgressCheckAbort(progressCB, 0, file_length):
                        return False
                    if self._ota_update_start_ok:
                        break

            # Debug
            if self.DEBUG_SEND_FILE:
                logger.debug(f"ricIF sendFile starting to send file data ...")

            # Send file blocks
            num_blocks = 0
            batch_retry_count = 0
            while self._file_send_ok_to < file_length:

                # NOTE: first batch MUST be of size 1 (not batchAckSize) because RIC performs a long-running
                # blocking task immediately after receiving the first message in a firmware
                # update - although this could be relaxed for non-firmware update file uploads
                send_from_pos = self._file_send_ok_to
                batch_start_pos = self._file_send_ok_to
                batch_start_time = time.time()
                batch_size = 1 if send_from_pos == 0 else batch_ack_size
                batch_block_idx = 0
                self._file_send_new_ok_to_received = False
                while batch_block_idx < batch_size and send_from_pos < file_length:

                    # Read block
                    file_obj.seek(send_from_pos)
                    block_to_send = file_obj.read(block_max_size)
                    
                    # Send block
                    self._ricInterface.sendRICRESTFileBlock(send_from_pos.to_bytes(4, 'big') + block_to_send)
                    if self.DEBUG_SEND_FILE_BLOCK:
                        logger.debug(f"sendRICRESTFileBlock data len {len(block_to_send)}")
                    send_from_pos += block_max_size
                    batch_block_idx += 1

                    # Check if we have received an error
                    if self._send_file_failed:
                        break

                # Debug
                if self.DEBUG_SEND_FILE:
                    logger.debug(f"ricIF sendFile sent batch - start at {batch_start_pos} end at {send_from_pos} len {send_from_pos-batch_start_pos} okto {self._file_send_ok_to}")

                # Wait for response (there is a timeout at the ESP end to ensure a response is always returned
                # even if blocks are dropped on reception at ESP) - the timeout here is for these responses
                # being dropped
                timeNow = time.time()
                while time.time() - timeNow < self.BLOCK_ACK_TIMEOUT:
                    # Progress update
                    if self._sendFileProgressCheckAbort(progressCB, self._file_send_ok_to, file_length):
                        return False

                    # Debug
                    if self.DEBUG_SEND_FILE:
                        logger.debug(f"ricIF sendFile checking for OKTO {self._file_send_ok_to} batchStartPos {batch_start_pos}")

                    # Check for okto
                    if self._file_send_new_ok_to_received:
                        batch_retry_count = 0
                        # Update stats
                        if self._file_send_ok_to > batch_start_pos:
                            elapsedTime = time.time() - batch_start_time
                            if elapsedTime > 0:
                                batchBytesPerSec = (self._file_send_ok_to - batch_start_pos) / elapsedTime
                                self.uploadBytesPerSec.add(batchBytesPerSec)
                        break

                    # Wait
                    time.sleep(1)

                # Check if no okto has been received with a greater position than batchStartPos
                if self._file_send_ok_to <= batch_start_pos:
                    batch_retry_count += 1
                    if batch_retry_count > self.BATCH_RETRY_MAX:
                        return False

                # Block count
                num_blocks += 1

            # Debug
            if self.DEBUG_SEND_FILE:
                logger.debug(f"ricIF sendFile sending END")

            # End frame
            resp = self._ricInterface.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufEnd","reqStr":"fileupload","fileType":"{fileDest}",' + \
                            f'"fileName":"{upload_name}","fileLen":{str(file_length)},' + \
                            f'"blockCount":{str(num_blocks)}' + '}', 
                            timeOutSecs = 5)
            if resp.get("rslt","") != "ok":
                return False
            return True
        
    def _sendFileProgressCheckAbort(self, progressCB: Callable[[int, int, 'RICInterface.RICInterface'], bool] | None, 
                    currentPos: int, fileSize: int) -> bool:
        if self._send_file_failed:
            return True
        if progressCB is None:
            return False
        if not progressCB(currentPos, fileSize, self._ricInterface):
            self._ricInterface.sendRICRESTCmdFrameSync('{"cmdName":"ufCancel"}')
            return True
        return False

    def getFileContents(self, filename: str, 
                progressCB: Callable[[int, int, 'RICInterface.RICInterface'], bool] | None,
                file_src: str,
                req_str: str
                ) -> bytearray | None:
        
        # Block and batch sizes
        block_max_size = self._ricInterface.commsHandler.commsParams.fileTransfer.get("fileBlockMax", 5000)
        batch_ack_size = self._ricInterface.commsHandler.commsParams.fileTransfer.get("fileBatchAck", 1)
        
        # Check if bridge protocol is required - martycam files are always transferred using bridge protocol
        self._file_recv_bridgeID = None
        if file_src == "martycam":

            # Establish a bridge connection
            martycam_serial_port_name = "Serial1"
            result = self._ricInterface.cmdRICRESTURLSync(f"commandserial/bridge/setup?port={martycam_serial_port_name}&name=MartyCam")
            if result.get("rslt", "") != "ok":
                raise MartyTransferException("MartyCam bridge setup failed")
            
            # Commands need to be sent using the bridge protocol
            self._file_recv_bridgeID = int(result.get("bridgeID", 0))
            logger.debug(f"getFileContents from martycam bridgeID {self._file_recv_bridgeID}")

        # Request file transfer
        # Frames follow the approach used in the web interface start, block..., end
        recv_file_req = '{' + f'"cmdName":"dfStart","reqStr":"{req_str}","fileType":"{file_src}",' + \
                        f'"batchMsgSize":{block_max_size},"batchAckSize":{batch_ack_size},' + \
                        f'"fileName":"{filename}"' + '}'
        resp = self._ricInterface.sendRICRESTCmdFrameSync(recv_file_req, bridgeID=self._file_recv_bridgeID, timeOutSecs = 10)
        if resp.get("rslt","") != "ok":
            self._removeBridge()
            raise MartyTransferException("File transfer start not acknowledged")
        
        # Extract file length and CRC info
        file_length = int(resp.get("fileLen", 0))
        file_crc: Union[int, None] = None
        file_crc_str = resp.get("crc16", None)
        if file_crc_str is not None:
            file_crc = int(file_crc_str, 16)
        stream_id = resp.get("streamID", 0)

        # logger.info(f"getFileContents: {resp} block_max_size {block_max_size} batch_ack_size {batch_ack_size} recv_file_req {recv_file_req}")

        # Iterate over blocks
        file_contents = bytearray()
        block_pos = 0
        last_progress_block_pos = 0
        start_time = time.time()
        last_block_time = time.time()
        block_ack_retry_count = 0
        batch_count_since_ack_sent = 0
        while True:

            # Check for timeout
            if time.time() - start_time > self.OVERALL_FILE_TRANSFER_TIMEOUT:
                self._removeBridge()
                raise MartyTransferException("File transfer timeout")
            
            # Check for timeout on last block
            if time.time() - last_block_time > self.BLOCK_ACK_TIMEOUT:
                block_ack_retry_count += 1
                if block_ack_retry_count > self.BATCH_RETRY_MAX:
                    self._removeBridge()
                    raise MartyTransferException("File transfer block timeout")

                # Send okto
                self._ricInterface.sendRICRESTCmdFrameNoResp(
                        "{" + f'"cmdName":"dfAck","okto":{block_pos},"streamID":{stream_id},"rslt":"ok"' + "}",
                        bridgeID=self._file_recv_bridgeID)
                continue
            
            # Check for new data received
            with self._file_recv_lock:
                if self._file_recv_last_block is not None and len(self._file_recv_last_block) > 0:

                    if self.DEBUG_RECEIVE_FILE_BLOCK:
                        logger.info(f"getFileContents received blockPos {self._file_recv_last_pos} expectedPos {block_pos} length {len(self._file_recv_last_block)}")

                    if self._file_recv_last_pos == block_pos:

                        # Reset retry count
                        block_ack_retry_count = 0

                        # Append to file contents
                        file_contents.extend(self._file_recv_last_block)
                        block_pos = self._file_recv_last_pos + len(self._file_recv_last_block)

                        # Check if okto needed
                        batch_count_since_ack_sent += 1
                        if batch_count_since_ack_sent >= batch_ack_size or block_pos >= file_length:
                            # Send okto
                            self._ricInterface.sendRICRESTCmdFrameNoResp(
                                "{" + f'"cmdName":"dfAck","okto":{block_pos},"streamID":{stream_id},"rslt":"ok"' + "}",
                                bridgeID=self._file_recv_bridgeID)
                            if self.DEBUG_RECEIVE_FILE:
                                logger.info(f"getFileContents sentOKTO block {block_pos} length {len(file_contents)}")
                            batch_count_since_ack_sent = 0 

                    self._file_recv_last_block.clear()

            # Check if entire file received
            if block_pos >= file_length:

                # Progress update
                if progressCB is not None:
                    progressCB(file_length, file_length, self._ricInterface)

                # Send end
                self._ricInterface.sendRICRESTCmdFrame(
                        "{" + f'"cmdName":"dfEnd","okto":{block_pos},"streamID":{stream_id},"rslt":"ok"' + "}",
                        bridgeID=self._file_recv_bridgeID)
                break

            # Progress update
            if progressCB is not None and block_pos != last_progress_block_pos:
                last_progress_block_pos = block_pos
                if not progressCB(block_pos, file_length, self._ricInterface):
                    self._ricInterface.sendRICRESTCmdFrameNoResp(
                        "{" + f'"cmdName":"dfCancel","streamID":{stream_id}' + "}",
                        bridgeID=self._file_recv_bridgeID)
                    self._removeBridge()
                    return None

        # Remove bridge if used
        self._removeBridge()
        return file_contents
    
    def onCmd(self, reptObj: dict) -> str:
        failReasons = ["OTAStartFailed", "notStarted", "userCancel", "failRetries", "failTimeout", "failFileWrite"]
        reason = reptObj.get("reason","")
        if reason == "OTAStartedOK":
            self._ota_update_start_ok = True
        elif reason in failReasons:
            self._send_file_failed = True
            self._send_file_fail_reason = reason
        return reason

    def onOkto(self, reptObj: dict):
        okto = reptObj.get("okto", -1)
        if self._file_send_ok_to < okto:
            self._file_send_ok_to = okto
        self._file_send_new_ok_to_received = True
        if self.DEBUG_SEND_FILE:
            logger.info(f"RICFileHandler OKTO msg {reptObj['okto']}")

    def onFail(self, reptObj: dict):
        if self.DEBUG_SEND_FILE:
            logger.info(f"RICFileHandler FAIL msg {reptObj}")
        self._streamClosed = True

    def onDataBlock(self, decodedMsg: DecodedMsg):
        if self.DEBUG_RECEIVE_FILE_BLOCK:
            logger.info(f"RICFileHandler DATA filePos {decodedMsg.getFilePos()} len {len(decodedMsg.getBlockContents())}")
        if decodedMsg.payload is not None:
            with self._file_recv_lock:
                self._file_recv_last_block = bytearray(decodedMsg.getBlockContents())
                self._file_recv_last_pos = decodedMsg.getFilePos()
        
    def getUploadBytesPS(self) -> float:
        return self.uploadBytesPerSec.getAvg()
    
    def _removeBridge(self) -> None:
        if self._file_recv_bridgeID is not None:
            self._ricInterface.cmdRICRESTURLSync(f"commandserial/bridge/remove?bridgeID={self._file_recv_bridgeID}")
            self._file_recv_bridgeID = None
