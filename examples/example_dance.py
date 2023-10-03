'''
A program to demonstrate Marty and Python
'''

# See README.md for instructions on how to run this

# Arguments
import argparse
import sys
sys.path.append('/Users/ntheodoropoulos/Robotical/martypy/martypy')

parser = argparse.ArgumentParser()
parser.add_argument('connMethod', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
args = parser.parse_args()

# Import Marty from the martypy library
from martypy import Marty

# Connect to a Marty and use the variable my_marty to refer to that Marty
martypy = Marty(args.connMethod, args.locator, blocking=True)
martypy.get_ready()
martypy.speak('Hello, I am Marty!')
import pdb; pdb.set_trace()

# Ask Marty to dance
martypy.dance()

# Disconnect from Marty
martypy.close()
