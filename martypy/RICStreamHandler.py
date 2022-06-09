'''
RICStreamHandler
'''
from typing import Callable
from .Exceptions import MartyTransferException
import logging
import os
import time

logger = logging.getLogger(__name__)

class RICStreamHandler:

    def __init__(self, ricInterface: 'RICInterface'):
        # Stream vars
        self._ricInterface = ricInterface
        self._streamId: int = None

    def streamSoundFile(self, fileName: str, targetEndpoint: str,
                progressCB: Callable[[int, int, 'RICInterface'], bool] = None) -> bool:
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
            fileStat = os.stat(fileName)
        except OSError as e:
            raise MartyTransferException("File not found")

        # Open the file
        with open(fileName, 'rb') as soundFile:

            # Setup file info 
            streamLength = fileStat.st_size
            streamType = "rtstream"
            streamName = os.path.basename(fileName)

            # Establish a maximum duration for streaming based on the assumption
            # that the file is encoded at at 10Kbits/s so a 1K file has 1s duration
            # with a 50% margin of error
            maxStreamDuration = streamLength / 1024 * 1.5

            # Send stream start message
            streamStartMsg = f'"cmdName":"ufStart","reqStr":"ufStart","fileType":"{streamType}","fileName":"{streamName}","endpoint":"{targetEndpoint}"'
            streamStartMsg += f',"fileLen":{streamLength}'
            resp = self._ricInterface.sendRICRESTCmdFrameSync('{' + streamStartMsg + '}')
            if resp.get("rslt","") != "ok":
                raise MartyTransferException("Stream start not acknowledged")
            self._ricInterface._streamStart()

            # Get stream details
            logger.debug(f"Stream started {resp}")
            self._streamId = resp.get("streamID", -1)
            maxBlockSize = resp.get("maxBlkSize", 1024)

            # Check streamId is valid
            if self._streamId < 0:
                raise MartyTransferException("Stream ID invalid")

            # File pos
            filePos = 0

            # Rate estimation
            msgRateWindow = []
            streamLastSoktoPos = 0
            intraMessageTime = 0.05
            lastMsgSentTime = 0
            lastMsgSent = False

            # Send stream data
            streamStartTime = time.time()
            while time.time() - streamStartTime < maxStreamDuration:

                # Wait for intra message time
                time.sleep(0.05 if intraMessageTime < 0.25 else intraMessageTime - 0.15)

                # # Reduce intra message time on each block to ensure we don't starve the connection
                # intraMessageTime -= 0.05

                # Check for sokto message
                isNewSokto, streamOkTo, streamClosed = self._ricInterface._streamGetLatest()
                if streamClosed:
                    # logger.debug("streamSoundFile stream closed")
                    break
                elif isNewSokto:
                    if streamOkTo >= streamLength:
                        # logger.debug(f"streamSoundFile sokto stream end reached")
                        break
                    else:
                        # logger.debug(f"streamSoundFile sokto not last message")
                        lastMsgSent = False
                    filePos = streamOkTo
                    if streamLastSoktoPos != filePos:
                        msgRateWindow.append((filePos, time.time()))
                        streamLastSoktoPos = filePos
                        if len(msgRateWindow) > 5:
                            msgRateWindow.pop(0)
                        msgRateWindowLen = len(msgRateWindow)
                        if msgRateWindowLen > 1:
                            timeBetweenOkTo = msgRateWindow[-1][1] - msgRateWindow[0][1]
                            bytesBetweenOkTo = msgRateWindow[-1][0] - msgRateWindow[0][0]
                            dataRate = bytesBetweenOkTo / timeBetweenOkTo
                            intraMessageTime = maxBlockSize / dataRate
                            if intraMessageTime > 1.0:
                                intraMessageTime = 1.0
                            # Debug
                            # logger.debug(f"streamSoundFile recalc {bytesBetweenOkTo} between {round(timeBetweenOkTo,2)}s rate {round(dataRate,0)}bytesps intraMsg {round(intraMessageTime,2)}s")

                # Progress and check for abort
                if self._sendStreamProgressCheckAbort(progressCB, filePos, streamLength):
                    # logger.debug("streamSoundFile progressCB aborted")
                    break

                # Read block
                soundFile.seek(filePos)
                fileBlock = soundFile.read(maxBlockSize)

                # Stream data
                if len(fileBlock) > 0:
                    if not self._ricInterface.sendRICRESTFileBlock(self._streamId.to_bytes(1, 'big') +
                            filePos.to_bytes(3, 'big') + fileBlock):
                        break

                    # Bump file pos
                    filePos += len(fileBlock)
                else:
                    # logger.debug(f"streamSoundFile end of file")
                    lastMsgSent = True
                    lastMsgSentTime = time.time()

                # Check for timeout on last frame sent
                if lastMsgSent and time.time() - lastMsgSentTime > 2:
                    # logger.debug(f"streamSoundFile timeout")
                    break

            # End frame
            resp = self._ricInterface.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufEnd","reqStr":"ufEnd","streamId":"{self._streamId}"' + '}')
            if resp.get("rslt","") != "ok":
                return False
        return True

    def _sendStreamProgressCheckAbort(self, progressCB: Callable[[int, int, 'RICInterface'], bool], 
                    currentPos: int, fileSize: int) -> bool:
        if not progressCB:
            return False
        if not self._ricInterface.isOpen():
            return True
        if not progressCB(currentPos, fileSize, self):
            self._ricInterface.sendRICRESTCmdFrameSync('{' + f'"cmdName":"ufCancel", "streamId":"{self._streamId}"' + '}')
            return True
        return False

