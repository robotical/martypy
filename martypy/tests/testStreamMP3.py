import sys    
import logging
import pathlib
import time
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(cur_path.parent.parent.resolve()))

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

# Setup logging
logging.basicConfig(format='%(levelname)s: %(asctime)s %(funcName)s(%(lineno)d) -- %(message)s', level=logging.DEBUG)
logger = logging.getLogger("testBaudRateSelection")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Function used for callback
def progressCB(bytesSent, totalBytes, interface):
    print(f"Progress {bytesSent}/{totalBytes}")
    return True

fileName = "completed_tone_low_br.mp3"
# fileName = "unplgivy.mp3"
# fileName = "unplugged.mp3"
# fileName = "test440ToneQuietShort.mp3"
my_marty.client.ricIF.streamSoundFile(cur_path.joinpath(fileName), progressCB, "streamaudio")

# Disconnect from Marty
my_marty.close()