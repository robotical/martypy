from martypy import Marty

my_marty = Marty("wifi", "192.168.86.11")

# Ask Marty to walk
my_marty.walk(20)
my_marty.dance()

# Do something while marty is walking
while my_marty.is_moving():
    if my_marty.get_distance_sensor() < 20:
        my_marty.stop()
