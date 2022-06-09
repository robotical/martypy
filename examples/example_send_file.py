'''
A program to send a file to marty's file system
'''

# See README.md for instructions on how to run this

import sys    
import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.resolve()))

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

def loggingCB(log_message):
    print(f"{log_message}")

# Register logging callback
my_marty.register_logging_callback(loggingCB)

# Function used for callback
def progressCB(bytesSent, totalBytes):
    print(f"Progress {bytesSent}/{totalBytes}")
    return True

# Test file
fileName = "completed_tone_low_br.mp3"

# Delete file initially
result = my_marty.delete_file(fileName)
if not result:
    print(f"Error deleting file {fileName}")
    sys.exit(1)

# Send a file to marty's file system
my_marty.send_file(cur_path.joinpath(fileName), progressCB)

# Get the file list
fileList = my_marty.get_file_list()
fileSendOk = False
print(fileList)
for file in fileList:
    if file["name"] == fileName:
        print(f"File {file['name']} was sent successfully size is {file['size']}")
        fileSendOk = True

# Check if file was sent successfully
if not fileSendOk:
    print(f"File {fileName} was not sent successfully")

# Disconnect from Marty
my_marty.close()
