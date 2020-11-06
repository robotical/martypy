'''
A program to demonstrate Marty and Python
'''

# Import Marty from the martypy library
from martypy import Marty

# Connect to a Marty and
# use the variable my_marty to refer to that Marty
my_marty = Marty("wifi", "192.168.86.11")

# Ask Marty to dance
my_marty.dance()
