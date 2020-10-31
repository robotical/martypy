import time
import logging
from martypy.Marty import Marty

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger("TestRob")

# mymarty = Marty('socket://192.168.86.41')
mymarty = Marty("usb", "COM9", debug=True)
# mymarty = Marty('usb:///dev/tty.SLAB_USBtoUART', debug=True)

jointNames = [
    'left hip',
    'left twist',
    'left knee',
    'right hip',
    'right twist',
    'right knee',
    'left arm',
    'right arm', 
    'eyes'   
]

def betweenCommands():
    time.sleep(0.3)

def testBoolCmd(cmdStr: str, cmdRslt: bool):
    print(f"{cmdStr}, rslt = {cmdRslt}")
    betweenCommands()

testBoolCmd("Get ready", mymarty.get_ready())
testBoolCmd("Circle Dance", mymarty.circle_dance())
testBoolCmd("Dance", mymarty.dance())
testBoolCmd("Eyes excited", mymarty.eyes('excited'))
testBoolCmd("Eyes wide", mymarty.eyes('wide'))
testBoolCmd("Eyes angry", mymarty.eyes('angry'))
testBoolCmd("Eyes normal", mymarty.eyes('normal'))
testBoolCmd("Eyes wiggle", mymarty.eyes('wiggle'))
testBoolCmd("Kick left", mymarty.kick('left'))
testBoolCmd("Kick right", mymarty.kick('right'))
testBoolCmd("Stop", mymarty.stop())
testBoolCmd("Arms 45", mymarty.arms(45, 45, 500))
testBoolCmd("Arms 0", mymarty.arms(0, 0, 500))
testBoolCmd("Hold position", mymarty.hold_position(6000))

for i in range(9): 
    testBoolCmd(f"Move joint {i}", mymarty.move_joint(i, i * 10, 500))
for jointName in jointNames: 
    testBoolCmd(f"Move joint {jointName}", mymarty.move_joint(jointName, 123, 500))
testBoolCmd("is_moving", mymarty.is_moving())

print("Accelerometer ", mymarty.get_accelerometer())
print("Joint positions: ", [mymarty.get_joint_position(pos) for pos in range(9)])

time.sleep(5)

mymarty.close()
