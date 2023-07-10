from typing import Tuple
import martypy
import sys
import pathlib
import logging
import time
from datetime import datetime
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.parent.resolve()))

# Arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('connMethod', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
parser.add_argument('--fps', type=float, help='Frames per second', default="10.0")
parser.add_argument('--size', type=str, help='Image size (160x120, 320x240, 640x480, 800x600, 1024x768, 1280x1024, 1600x1200)', default="320x240")
parser.add_argument('--quality', type=int, help='Image quality (0-63) - lower is better', default="16")
args = parser.parse_args()

CHECK_TEST_DATA = False
SHOW_IMAGE_USING_PIL = False
SHOW_IMAGE_USING_OPENCV = True

if SHOW_IMAGE_USING_PIL:
    from PIL import Image
    from io import BytesIO
if SHOW_IMAGE_USING_OPENCV:
    import cv2
    import numpy as np

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(f"testCamStream_{datetime.utcnow().strftime('%H%M%S')}.log", mode='w')
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                handlers=[stdout_handler, file_handler])

def extractTimeStamp(msgBuf: bytes) -> Tuple[bytes, datetime, int]:
    # Extract the timestamp from the msgBuf
    esp32Time = datetime.utcfromtimestamp(int.from_bytes(msgBuf[0:8], byteorder="little"))
    esp32Millis = int.from_bytes(msgBuf[8:12], byteorder="little")
    msgBuf = msgBuf[12:]
    print(f"esp32Time {esp32Time} esp32Millis {esp32Millis}")
    return msgBuf, esp32Time, esp32Millis

def pubMsgCB(msgId: int, msgBuf: bytes) -> None:
    if CHECK_TEST_DATA:
        # Check the msbBuf contains consecutive bytes from 00 to FF and wrapping around for the
        # entire length of the msgBuf
        bufDataValid = True
        for i in range(len(msgBuf)):
            if msgBuf[i] != (i & 0xFF):
                bufDataValid = False
                break
        print(f"Pub msgID {msgId} {len(msgBuf)} dataValid {bufDataValid}")
    if SHOW_IMAGE_USING_PIL:
        msgBuf, esp32Time, esp32Millis = extractTimeStamp(msgBuf)
        # Convert the msgBuf into a PIL image and show it
        img = Image.open(BytesIO(msgBuf))
        img.show()
    if SHOW_IMAGE_USING_OPENCV:
        if len(msgBuf) < 12:
            print(f"Pub msgID {msgId} {len(msgBuf)} < 12")
            return
        msgBuf, esp32Time, esp32Millis = extractTimeStamp(msgBuf)
        # Convert the msgBuf into a numpy array and show it
        img = cv2.imdecode(np.frombuffer(msgBuf, np.uint8), cv2.IMREAD_COLOR)
        # Save the image with time formatted file name including milliseconds
        cv2.imwrite(f"img_{datetime.utcnow().strftime('%H%M%S.%f')}_{esp32Time.strftime('%H%M%S')}_{esp32Millis}.jpg", img)
        # Show image
        cv2.imshow("Image", img)
        cv2.waitKey(1)

# Create marty object
marty = martypy.Marty(args.connMethod, args.locator, blocking=True)

# Set camera resolution and quality
cmdStr = "camera/0/set?size=" + args.size + "&quality=" + str(args.quality)
marty.send_ric_rest_cmd_sync(cmdStr, msgDebugStr="SetCamRes")

marty.register_publish_callback(pubMsgCB)

marty.send_ric_rest_cmd_sync("subscription?action=update&name=Camera&rateHz=" + str(args.fps), msgDebugStr="SubCamStream")

time.sleep(20)

marty.close()

time.sleep(1)
