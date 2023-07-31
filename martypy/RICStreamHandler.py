'''
RICStreamHandler
'''
from typing import Callable, Union, Optional
from martypy import RICInterface
from .Exceptions import MartyTransferException
import logging
import os
import time

logger = logging.getLogger(__name__)

class RICStreamHandler:

    def __init__(self, ricInterface: 'RICInterface.RICInterface'):
        # Stream vars
        self._ricInterface = ricInterface
        self._stream_id: Optional[int] = None
        self._stream_cur_sokto = 0
        self._stream_closed = False
        self._stream_new_sokto_flag = False
        self.DEBUG_RIC_STREAM = False

    def streamSoundFile(self, file_name: str, targetEndpoint: str,
                progressCB: Optional[Callable[[int, int, 'RICInterface.RICInterface'], bool]] = None) -> bool:
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
        # Check validity
        try:
            file_stat = os.stat(file_name)
        except OSError as e:
            raise MartyTransferException("File not found")

        # Open the file
        with open(file_name, 'rb') as file_obj:

            # Setup file info 
            stream_length = file_stat.st_size
            stream_type = "rtstream"
            stream_name = os.path.basename(file_name)

            # Establish a maximum duration for streaming based on the assumption
            # that the file is encoded at at 10Kbits/s so a 1K file has 1s duration
            # with a 50% margin of error
            max_stream_duration = stream_length / 1024 * 1.5

            # Send stream start message
            stream_start_msg = f'"cmdName":"ufStart","reqStr":"ufStart","fileType":"{stream_type}","fileName":"{stream_name}","endpoint":"{targetEndpoint}"'
            stream_start_msg += f',"fileLen":{stream_length}'
            resp = self._ricInterface.sendRICRESTCmdFrameSync('{' + stream_start_msg + '}')
            if resp.get("rslt","") != "ok":
                raise MartyTransferException("Stream start not acknowledged")
            self._streamStart()

            # Get stream details
            logger.debug(f"Stream started {resp}")
            self._stream_id = resp.get("streamID", -1)
            max_block_size = resp.get("maxBlkSize", 1024)

            # Check streamId is valid
            if self._stream_id < 0:
                raise MartyTransferException("Stream ID invalid")

            # File pos
            file_pos = 0

            # Rate estimation
            msg_rate_window = []
            stream_last_sokto_pos = 0
            intra_message_secs = 0.05
            last_msg_sent_time = 0
            last_msg_sent_flag = False

            # Send stream data
            stream_start_time = time.time()
            while time.time() - stream_start_time < max_stream_duration:

                # Wait for intra message time
                time.sleep(0.05 if intra_message_secs < 0.25 else intra_message_secs - 0.15)

                # # Reduce intra message time on each block to ensure we don't starve the connection
                # intraMessageTime -= 0.05

                # Check for sokto message
                is_new_sokto, stream_ok_to, stream_closed = self._streamGetLatest()
                if stream_closed:
                    # logger.debug("streamSoundFile stream closed")
                    break
                elif is_new_sokto:
                    if stream_ok_to >= stream_length:
                        # logger.debug(f"streamSoundFile sokto stream end reached")
                        break
                    else:
                        # logger.debug(f"streamSoundFile sokto not last message")
                        last_msg_sent_flag = False
                    file_pos = stream_ok_to
                    if stream_last_sokto_pos != file_pos:
                        msg_rate_window.append((file_pos, time.time()))
                        stream_last_sokto_pos = file_pos
                        if len(msg_rate_window) > 5:
                            msg_rate_window.pop(0)
                        msg_rate_window_len = len(msg_rate_window)
                        if msg_rate_window_len > 1:
                            time_between_soktos = msg_rate_window[-1][1] - msg_rate_window[0][1]
                            bytes_between_soktos = msg_rate_window[-1][0] - msg_rate_window[0][0]
                            data_rate = bytes_between_soktos / time_between_soktos
                            intra_message_secs = max_block_size / data_rate
                            if intra_message_secs > 1.0:
                                intra_message_secs = 1.0
                            # Debug
                            # logger.debug(f"streamSoundFile recalc {bytes_between_soktos} between {round(time_between_soktos,2)}s rate {round(data_rate,0)}bytesps intraMsgSecs {round(intra_message_secs,2)}s")

                # Progress and check for abort
                if self._sendStreamProgressCheckAbort(progressCB, file_pos, stream_length):
                    # logger.debug("streamSoundFile progressCB aborted")
                    break

                # Read block
                file_obj.seek(file_pos)
                block_to_send = file_obj.read(max_block_size)

                # Stream data
                if len(block_to_send) > 0:
                    if not self._ricInterface.sendRICRESTFileBlock(self._stream_id.to_bytes(1, 'big') +
                            file_pos.to_bytes(3, 'big') + block_to_send):
                        break

                    # Bump file pos
                    file_pos += len(block_to_send)
                else:
                    # logger.debug(f"streamSoundFile end of file")
                    last_msg_sent_flag = True
                    last_msg_sent_time = time.time()

                # Check for timeout on last frame sent
                if last_msg_sent_flag and time.time() - last_msg_sent_time > 2:
                    # logger.debug(f"streamSoundFile timeout")
                    break

            # End frame
            resp = self._ricInterface.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufEnd","reqStr":"ufEnd","streamId":"{self._stream_id}"' + '}')
            if resp.get("rslt","") != "ok":
                return False
        return True

    def _sendStreamProgressCheckAbort(self, progressCB: Optional[Callable[[int, int, 'RICInterface.RICInterface'], bool]], 
                    currentPos: int, fileSize: int) -> bool:
        if not progressCB:
            return False
        if not self._ricInterface.isOpen():
            return True
        if not progressCB(currentPos, fileSize, self._ricInterface):
            self._ricInterface.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufCancel", "streamId":"{self._stream_id}"' + '}')
            return True
        return False
    
    def onSokto(self, reptObj: dict):
        sokto = reptObj.get("sokto", -1)
        if self._stream_cur_sokto < sokto:
            self._stream_cur_sokto = sokto
        self._stream_new_sokto_flag = True
        if self.DEBUG_RIC_STREAM:
            logger.debug(f"SOKTO MESSAGE {reptObj['sokto']}")

    def onFail(self, reptObj: dict):
        if self.DEBUG_RIC_STREAM:
            logger.debug(f"FAIL MESSAGE {reptObj}")
        self._stream_closed = True

    def _streamStart(self):
        self._stream_cur_sokto = 0
        self._stream_new_sokto_flag = False
        self._stream_closed = False

    def _streamGetLatest(self):
        isNew = self._stream_new_sokto_flag
        self._stream_new_sokto_flag = False
        return isNew, self._stream_cur_sokto, self._stream_closed