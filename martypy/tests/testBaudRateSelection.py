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

mm = Marty("usb")
# try:
# mm = Marty("wifi://192.168.86.81")
# except Exception as excp:
#     print(f"Couldn't connect to marty")
#     exit()

# mm.eyes(100)
# mm.eyes(0)

logger.info(f"RIC version info 1: {mm.get_system_info()}")
mm.circle_dance()
logger.info(f"RIC version info 2: {mm.get_system_info()}")
time.sleep(5)
logger.info(f"RIC version info 3: {mm.get_system_info()}")

mm.close()
