'''
A program to play a sound on Marty
'''

# See README.md for instructions on how to run this

# Import Marty from the martypy library
from martypy import Marty

# Connect to a Marty and# use the variable my_marty to refer to that Marty
# This assumes you are connecting via WiFi - check the documentation for other options
# You will need to set the ip_address variable with the IP address of your Marty
connection_method = "wifi"
ip_address = "192.168.86.18"
my_marty = Marty(connection_method, ip_address, blocking=True)

# Ask Marty to play a sound
my_marty.play_sound("no_way")

# Disconnect from Marty
my_marty.close()
