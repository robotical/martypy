'''
A program to play an MP3 sound file on Marty
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

# Function used for callback
def progressCB(bytesSent, totalBytes):
    print(f"Progress {bytesSent}/{totalBytes}")
    return True

# Get and set current volume
volume = my_marty.get_volume()
print(f"Marty's volume is {volume}% - change it to 70%")
my_marty.set_volume(70)

# Play an MP3 file
fileName = "completed_tone_low_br.mp3"
my_marty.play_mp3(cur_path.joinpath(fileName), progressCB)

# Disconnect from Marty
my_marty.close()
