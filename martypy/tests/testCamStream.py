import martypy
import sys
import pathlib
import logging
import time

CHECK_TEST_DATA = False
SHOW_IMAGE_USING_PIL = True

if SHOW_IMAGE_USING_PIL:
    from PIL import Image
    from io import BytesIO

cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.parent.resolve()))

stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                handlers=[stdout_handler])

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
        # Convert the msgBuf into a PIL image and show it
        img = Image.open(BytesIO(msgBuf))
        img.show()

marty = martypy.Marty("wifi", "192.168.1.14")

marty.register_publish_callback(pubMsgCB)

marty.send_ric_rest_cmd_sync("subscription?action=update&name=Camera&rateHz=1.0", msgDebugStr="SubCamStream")

time.sleep(6)

marty.close()

time.sleep(1)
