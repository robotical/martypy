import time
import logging
from martypy import Marty

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
    time.sleep(3)

def testBoolCmd(cmdStr: str, cmdRslt: bool):
    print(f"{cmdStr}, rslt = {cmdRslt}")
    betweenCommands()

martySysInfo = mymarty.get_system_info()
martyVersion2 = martySysInfo.get("HardwareVersion", "1.0") == "2.0"

testBoolCmd("Get ready", mymarty.get_ready())
testBoolCmd("Circle Dance", mymarty.circle_dance())
testBoolCmd("Eyes excited", mymarty.eyes('excited'))
testBoolCmd("Eyes wide", mymarty.eyes('wide'))
testBoolCmd("Eyes angry", mymarty.eyes('angry'))
testBoolCmd("Eyes normal", mymarty.eyes('normal'))
testBoolCmd("Kick left", mymarty.kick('left'))
testBoolCmd("Kick right", mymarty.kick('right'))
testBoolCmd("Stop", mymarty.stop())
testBoolCmd("Arms 45", mymarty.arms(45, 45, 500))
testBoolCmd("Arms 0", mymarty.arms(0, 0, 500))

for i in range(9): 
    testBoolCmd(f"Move joint {i}", mymarty.move_joint(i, i * 10, 500))
for jointName in jointNames: 
    testBoolCmd(f"Move joint {jointName}", mymarty.move_joint(jointName, 123, 500))

print("Accelerometer x", mymarty.get_accelerometer('x'))
print("Accelerometer y", mymarty.get_accelerometer('y'))
print("Accelerometer z", mymarty.get_accelerometer('z'))

if martyVersion2:
    testBoolCmd("Dance", mymarty.dance())
    testBoolCmd("Eyes wiggle", mymarty.eyes('wiggle'))
    testBoolCmd("Hold position", mymarty.hold_position(6000))
    testBoolCmd("is_moving", mymarty.is_moving())
    print("Joint positions: ", [mymarty.get_joint_position(pos) for pos in range(9)])

time.sleep(5)

mymarty.close()
