'''
A program to demonstrate monitoring Marty while it is running.
This uses the blocking: False option so martypy queues up the
movements and sounds and then goes on to show the posiiotn of
marty as it moves
'''

# See README.md for instructions on how to run this

# Arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('connMethod', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
args = parser.parse_args()

# Import Marty from the martypy library and the time library
from martypy import Marty
import time

# Connect to a Marty and use the variable my_marty to refer to that Marty
my_marty = Marty(args.connMethod, args.locator, blocking=False)

# Ask Marty to walk
my_marty.walk(20)
my_marty.dance()
time.sleep(1)

# Do something while marty is walking and dancing
while my_marty.is_moving():
    print(f"Marty's left leg is at {my_marty.get_joints()[0]['pos']}")
    time.sleep(0.5)

# Disconnect from Marty
my_marty.close()
