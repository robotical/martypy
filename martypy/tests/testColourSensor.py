import sys    
import logging

import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.parent.resolve()))

from martypy import Marty
import time

# Setup logging
logging.basicConfig(format='%(levelname)s: %(asctime)s %(funcName)s(%(lineno)d) -- %(message)s', level=logging.DEBUG)
logger = logging.getLogger("testColourSensor")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

mm = Marty("usb")

# time.sleep(2)

for i in range(100):
    try:
        onGroundL = mm.foot_on_ground('left')
        onGroundR = mm.foot_on_ground('right')
        obstacleL = mm.foot_obstacle_sensed('left')
        obstacleR = mm.foot_obstacle_sensed('right')
        obstSensorL = mm.get_obstacle_sensor_reading('left')
        obstSensorR = mm.get_obstacle_sensor_reading('right')
        groundSensorL = mm.get_ground_sensor_reading('left')
        groundSensorR = mm.get_ground_sensor_reading('right')
        print(
            f"onGroundL={onGroundL!s:<5} onGroundR={onGroundR!s:<5} | "
            f"obstacleL={obstacleL!s:<5} obstacleR={obstacleR!s:<5} || "
            f"obstSensorL={obstSensorL:5} obstSensorR={obstSensorR:5} | "
            f"groundSensorL={groundSensorL:5} groundSensorR={groundSensorR:5}"
        )
    except Exception as e:
        logger.exception(f"Failed to get addon values")        
    time.sleep(.2)

# try:
# mm = Marty("wifi://192.168.86.81")
# except Exception as excp:
#     print(f"Couldn't connect to marty")
#     exit()


# time.sleep(5)

mm.close()
