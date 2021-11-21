import sys    
import logging

import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.parent.resolve()))

from martypy import Marty
import time

# Setup logging
logging.basicConfig(format='%(levelname)s: %(asctime)s %(funcName)s(%(lineno)d) -- %(message)s', level=logging.DEBUG)
logger = logging.getLogger("testBaudRateSelection")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

mm = Marty("usb", "COM19")

# time.sleep(2)

for i in range(100):
    try:
        onGroundL = mm.foot_on_ground('left')
        onGroundR = mm.foot_on_ground('right')
        print(f"onGroundL = {onGroundL}, onGroundR = {onGroundR}")
    except Exception as e:
        print(f"Failed to get addon values")        
    time.sleep(.2)

# try:
# mm = Marty("wifi://192.168.86.81")
# except Exception as excp:
#     print(f"Couldn't connect to marty")
#     exit()



# time.sleep(5)

mm.close()
