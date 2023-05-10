'''
A program to send a file to marty's file system
'''

# See README.md for instructions on how to run this

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
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s %(levelname)-8s %(message)s',
                handlers=[file_handler, stdout_handler])

# Arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('conn_method', type=str, help='Connection method (wifi or usb)')
parser.add_argument('locator', type=str, help = 'IP Address for Wifi or Serial Port for USB', nargs='?')
args = parser.parse_args()

# Import Marty from the martypy library
from martypy import Marty

# Debug
logging.info(f"Connecting to marty using {args.conn_method}")

# Connect to a Marty and# use the variable my_marty to refer to that Marty
my_marty = Marty(args.conn_method, args.locator, blocking=True)

# Debug
logging.info(f"Connected to {my_marty.get_marty_name()}")

def logging_callback(log_message):
    logging.info(f"{log_message}")

# Register logging callback
# my_marty.register_logging_callback(logging_callback)

# Function used for callback
def progress_callback(bytes_sent, total_bytes):
    logging.info(f"Progress {bytes_sent}/{total_bytes}")
    return True

# Test file
file_name = "index.html"

# Debug
logging.info(f"Getting contents of file {file_name}")

# Send a file to marty's file system
file_contents = my_marty.get_file_contents(file_name, progress_callback)

# Debug
if file_contents is not None:
    logging.info(f"File received - {len(file_contents)} bytes")
else:
    logging.warning(f"File {file_name} was not received successfully")

# Disconnect from Marty
my_marty.close()
