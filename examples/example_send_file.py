'''
A program to send a file to marty's file system
'''

# See README.md for instructions on how to run this

import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()

USE_LOCAL_MARTYPY_CODE = False
import sys
if USE_LOCAL_MARTYPY_CODE:
    import pathlib
    cur_path = pathlib.Path(__file__).parent.resolve()
    sys.path.insert(0, str(cur_path.parent.resolve()))

# Create logger
import logging
file_handler = logging.FileHandler(filename='logToFile.log')
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stdout_handler])

# Arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('connMethod', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
args = parser.parse_args()

# Import Marty from the martypy library
from martypy import Marty

# Debug
logging.info(f"Connecting to marty using {args.connMethod}")

# Connect to a Marty and# use the variable my_marty to refer to that Marty
my_marty = Marty(args.connMethod, args.locator, blocking=True)

# Test file
fileName = "completed_tone_low_br.mp3"

# Debug
logging.info(f"Connected to {my_marty.get_marty_name()}")

def loggingCB(log_message):
    logging.info(f"{log_message}")

# Register logging callback
my_marty.register_logging_callback(loggingCB)

# Function used for callback
def progressCB(bytesSent, totalBytes):
    logging.info(f"Progress {bytesSent}/{totalBytes}")
    return True

# Debug
logging.info(f"Deleting file {fileName}")

# Delete file initially
result = my_marty.delete_file(fileName)
if not result:
    logging.warning(f"Error deleting file {fileName}")
    sys.exit(1)

# Debug
logging.info(f"File {fileName} deleted successfully")

# Debug
logging.info(f"Sending file {fileName}")

# Send a file to marty's file system
my_marty.send_file(cur_path.joinpath(fileName), progressCB)

# Debug
logging.info(f"File sent - getting file list")

# Get the file list
fileList = my_marty.get_file_list()
fileSendOk = False
logging.info(f"fileList {fileList}")
for file in fileList:
    if file["name"] == fileName:
        logging.info(f"File {file['name']} was sent successfully size is {file['size']}")
        fileSendOk = True

# Check if file was sent successfully
if not fileSendOk:
    logging.warning(f"File {fileName} was not sent successfully")

# Disconnect from Marty
my_marty.close()
