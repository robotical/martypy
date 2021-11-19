import sys    
import logging

import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(cur_path.parent.parent.resolve()))

from martypy import Marty
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def publishCallback(topic):
    logger.debug(f"publishCallback {topic}") 

def reportCallback(report_info):
    logger.debug(f"reportCallback {report_info}")

my_marty = Marty("wifi://192.168.86.18", blocking=True, subscribeRateHz=1)
my_marty.register_publish_callback(publishCallback)
my_marty.register_report_callback(reportCallback)

my_marty.eyes(100)
my_marty.eyes(0)

for i in range(5):
    my_marty.walk(1)
time.sleep(10)

my_marty.close()

