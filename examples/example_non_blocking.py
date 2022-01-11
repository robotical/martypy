'''
A program to demonstrate monitoring Marty while it is running.
This uses the blocking: False option so martypy queues up the
movements and sounds and then goes on to show the posiiotn of
marty as it moves
'''

# See README.md for instructions on how to run this

# Import Marty from the martypy library and the time library
from martypy import Marty
import time

# Connect to a Marty and# use the variable my_marty to refer to that Marty
# This assumes you are connecting via WiFi - check the documentation for other options
# You will need to set the ip_address variable with the IP address of your Marty
connection_method = "wifi"
ip_address = "192.168.86.18"
my_marty = Marty(connection_method, ip_address, blocking=False)

# Ask Marty to walk
my_marty.walk(20)
my_marty.dance()
time.sleep(1)

# Do something while marty is walking
while my_marty.is_moving():
    print(f"Marty's left leg is at {my_marty.get_joints()[0]['pos']}")
    time.sleep(0.5)

# Disconnect from Marty
my_marty.close()
