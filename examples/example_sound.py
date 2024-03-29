'''
A program to play one of the sounds built into Marty
'''

# See README.md for instructions on how to run this

# Arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('connMethod', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
args = parser.parse_args()

# Import Marty from the martypy library
from martypy import Marty

# Connect to a Marty and# use the variable my_marty to refer to that Marty
my_marty = Marty(args.connMethod, args.locator, blocking=True)

# Ask Marty to play a sound
my_marty.play_sound("no_way")

# Disconnect from Marty
my_marty.close()
