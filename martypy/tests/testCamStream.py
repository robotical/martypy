import martypy
import sys
import pathlib
import logging
import time
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.parent.resolve()))

stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                handlers=[stdout_handler])

def pubMsgCB(msgId: int, msgBuf: bytes) -> None:
    print(f"Pub msgID {msgId} {len(msgBuf)} {msgBuf.hex()}")

marty = martypy.Marty("wifi", "192.168.1.14")

marty.register_publish_callback(pubMsgCB)

marty.send_ric_rest_cmd_sync("subscription?action=update&name=Camera&rateHz=10.0", msgDebugStr="SubCamStream")

time.sleep(3)

marty.close()

time.sleep(6)
