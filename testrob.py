import time
import logging
from martypy.marty import Marty

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger("TestRob")

# mymarty = Marty('socket://192.168.86.41')
mymarty = Marty('usb://dev/asm00', debug=True)

# print("Get ready")
# mymarty.get_ready()
# time.sleep(5)

# print("Circle Dance")
# mymarty.circle_dance()
# time.sleep(5)

# print("Dance")
# mymarty.dance()
# time.sleep(5)

# print("Eyes excited")
# mymarty.eyes('excited')
# time.sleep(2)

# print("Eyes wide")
# mymarty.eyes('wide')
# time.sleep(2)

# print("Eyes angry")
# mymarty.eyes('angry')
# time.sleep(2)

# print("Eyes normal")
# mymarty.eyes('normal')
# time.sleep(1)

# print("Eyes wiggle")
# mymarty.eyes('wiggle')
# time.sleep(2)

# time.sleep(2)

# print("Kick left")
# mymarty.kick('green')
# time.sleep(3)

# print("Kick right")
# mymarty.kick('right')
# time.sleep(2)

# mymarty.stop('ssdf')
# mymarty.move_joint('asdasd')
# print(mymarty.is_moving())
# mymarty.walk()
# for i in range(10):
#     print(mymarty.is_moving())
#     time.sleep(0.5)
mymarty.walk()
mymarty.arms(45, 45, 500)
mymarty.arms(0, 0, 500)
mymarty.hold_position(6000)
mymarty.arms(45, 45, 500)
mymarty.arms(0, 0, 500)
mymarty.walk()
time.sleep(10)

# for i in range(5):
#     # print(mymarty.get_joint_position(0), mymarty.get_accelerometer('x'), mymarty.get_accelerometer('y'), mymarty.get_accelerometer('z'))
#     print(mymarty.get_joint_position(0), mymarty.get_accelerometer())
#     time.sleep(1)
# mymarty.close()
