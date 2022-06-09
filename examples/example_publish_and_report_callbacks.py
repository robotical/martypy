# See README.md for instructions on how to run this

# Import Marty from the martypy library and other libraries
from martypy import Marty
import time

# Arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('connMethod', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
args = parser.parse_args()

# Callback function for when a publish message is received
# Example is new servo positions, accelerometer data, etc.
def publish_callback(topic):
    topic_name = (
        "SERVOS" if topic == Marty.PUBLISH_TOPIC_SERVOS else
        "ACCELEROMETER" if topic == Marty.PUBLISH_TOPIC_ACCELEROMETER else
        "POWER" if topic == Marty.PUBLISH_TOPIC_POWER else
        "ADDONS" if topic == Marty.PUBLISH_TOPIC_ADDONS else
        "ROBOT_STATUS" if topic == Marty.PUBLISH_TOPIC_ROBOT_STATUS else
        "UNKNOWN_TOPIC"
    )
    print(f"publish_callback {topic} ({topic_name})")

# Callback function for when a report message is received
# Example is free-fall or over-current detected
def report_callback(report_info):
    print(f"report_callback {report_info}")

# Start Marty
# This code can be blocking because we're going to be getting messages
# via the callbacks.
# We also set the subscribe rate to 1Hz (normally its 10Hz) to reduce the
# number of callbacks we get with published information
# Connect to a Marty and use the variable my_marty to refer to that Marty
my_marty = Marty(args.connMethod, args.locator, blocking=True, subscribeRateHz=1)

# Register callbacks
my_marty.register_publish_callback(publish_callback)
my_marty.register_report_callback(report_callback)

# Move Marty's eyes
my_marty.eyes(100)
my_marty.eyes(0)

# Walk a little
for i in range(5):
    my_marty.walk(1)
time.sleep(10)

# Disconnect from Marty
my_marty.close()
