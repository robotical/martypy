'''
A program to demonstrate Marty and Python
'''

# If you are running this with martypy "pip installed", you can 
# just comment out the following 4 lines
import sys
import pathlib
cur_path = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(cur_path.parent.resolve()))

# Import Marty from the martypy library
from martypy import Marty

# Connect to a Marty and# use the variable my_marty to refer to that Marty
# This assumes you are connecting via WiFi - check the documentation for other options
# You will need to set the ip_address variable with the IP address of your Marty
connection_method = "wifi"
ip_address = "192.168.86.18"
my_marty = Marty(connection_method, ip_address, blocking=True)

# Ask Marty to dance
my_marty.dance()
