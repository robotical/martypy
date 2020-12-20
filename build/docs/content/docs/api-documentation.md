---
menu: main
title: API Documentation
---

<a name="martypy.Marty"></a>
# martypy.Marty

Python library to communicate with Marty the Robot V1 and V2 by Robotical

Getting started:  
1) Import Marty from the martypy library  
2) Create a Marty object that connects the way you want  
3) Tell your Marty to dance  

```python
from martypy import Marty  
my_marty = Marty("wifi","192.168.0.53")  
my_marty.dance()
```

The tags :one: and :two: indicate when the method is available for Marty V1 :one: and Marty V2 :two:

<a name="martypy.Marty.Marty"></a>
## Marty Objects

```python
class Marty(object)
```

<a name="martypy.Marty.Marty.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(method: str, locator: str = "", extra_client_types: dict = dict(), *args, **kwargs) -> None
```

Start a connection to Marty :one: :two:

For example:

* `Marty("wifi", "192.168.86.53")` to connect to Marty via WiFi on IP Address 192.168.0.53
* `Marty("usb", "COM2")` on a Windows computer with Marty connected by USB cable to COM2
* `Marty("usb", "/dev/tty.SLAB_USBtoUART")` on a Mac computer with Marty connected by USB cable to /dev/tty.SLAB_USBtoUART
* `Marty("exp", "/dev/ttyAMA0")` on a Raspberry Pi computer with Marty connected by expansion cable to /dev/ttyAMA0

**Arguments**:

- `method` - method of connecting to Marty - it may be: "usb",
  "wifi", "socket" (Marty V1) or "exp" (expansion port used to connect
  to a Raspberry Pi, etc)
- `locator` - location to connect to, depending on the method of connection this
  is the serial port name, network (IP) Address or network name (hostname) of Marty
  that the computer should use to communicate with Marty
  

**Raises**:

  * MartyConfigException if the parameters are invalid
  * MartyConnectException if Marty couldn't be contacted

<a name="martypy.Marty.Marty.dance"></a>
#### dance

```python
 | dance(side: str = 'right', move_time: int = 4500) -> bool
```

Boogie, Marty! :one: :two:

**Arguments**:

- `side` - 'left' or 'right', which side to start on
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.celebrate"></a>
#### celebrate

```python
 | celebrate(move_time: int = 4000) -> bool
```

Do a small celebration :one: :two:

**Arguments**:

- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.wiggle"></a>
#### wiggle

```python
 | wiggle(move_time: int = 5000) -> bool
```

Wiggle :two:

**Arguments**:

- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.circle_dance"></a>
#### circle\_dance

```python
 | circle_dance(side: str = 'right', move_time: int = 2500) -> bool
```

Circle Dance :two:

**Arguments**:

- `side` - 'left' or 'right', which side to start on
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.walk"></a>
#### walk

```python
 | walk(num_steps: int = 2, start_foot: str = 'auto', turn: int = 0, step_length: int = 25, move_time: int = 1500) -> bool
```

Make Marty walk :one: :two:

**Arguments**:

- `num_steps` - how many steps to take
- `start_foot` - 'left', 'right' or 'auto', start walking with this foot Note: :two: Unless
  you specify 'auto', all steps are taken with the same foot so
  it only makes sense to use the start_foot argument with `num_steps=1`.
- `turn` - How much to turn (-100 to 100 in degrees), 0 is straight.
- `step_length` - How far to step (approximately in mm)
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.get_ready"></a>
#### get\_ready

```python
 | get_ready() -> bool
```

Move Marty to the normal standing position :one: :two:

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.eyes"></a>
#### eyes

```python
 | eyes(pose_or_angle: Union[str, int], move_time: int = 1000) -> bool
```

Move the eyes to a pose or an angle :one: :two:

**Arguments**:

- `pose_or_angle` - 'angry', 'excited', 'normal', 'wide', or 'wiggle' :two: - alternatively
  this can be an angle in degrees (which can be a negative number)
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.kick"></a>
#### kick

```python
 | kick(side: str = 'right', twist: int = 0, move_time: int = 2500) -> bool
```

Kick one of Marty's feet :one: :two:

**Arguments**:

- `side` - 'left' or 'right', which foot to use
- `twist` - the amount of twisting do do while kicking (in degrees)
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.arms"></a>
#### arms

```python
 | arms(left_angle: int, right_angle: int, move_time: int) -> bool
```

Move both of Marty's arms to angles you specify :one: :two:

**Arguments**:

- `left_angle` - Angle of the left arm (degrees -100 to 100)
- `right_angle` - Position of the right arm (degrees -100 to 100)
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.lean"></a>
#### lean

```python
 | lean(direction: str, amount: int, move_time: int) -> bool
```

Lean over in a direction :one: :two:

**Arguments**:

- `direction` - 'left', 'right', 'forward', 'back', or 'auto'
- `amount` - percentage amount to lean
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.sidestep"></a>
#### sidestep

```python
 | sidestep(side: str, steps: int = 1, step_length: int = 50, move_time: int = 1000) -> bool
```

Take sidesteps :one: :two:

**Arguments**:

- `side` - 'left' or 'right', direction to step in
- `steps` - number of steps to take
- `step_length` - how broad the steps are (up to 127)
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.play_sound"></a>
#### play\_sound

```python
 | play_sound(name_or_freq_start: Union[str,int], freq_end: Optional[int] = None, duration: Optional[int] = None) -> bool
```

Play a named sound (Marty V2 :two:) or make a tone (Marty V1 :one:)

**Arguments**:

- `name_or_freq_start` - name of the sound, e.g. 'excited' or 'no_way' :two:
- `name_or_freq_start` - starting frequency, Hz :one:
- `freq_end` - ending frequency, Hz :one:
- `duration` - milliseconds, maximum 5000 :one:

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.get_accelerometer"></a>
#### get\_accelerometer

```python
 | get_accelerometer(axis: Optional[str] = None) -> float
```

Get the latest value from the Marty's accelerometer :one: :two:

**Arguments**:

- `axis` - (optional) 'x', 'y' or 'z' OR no parameter at all (see returns below)

**Returns**:

  * The acceleration value from the axis (if axis specified)
  * A tuple containing x, y and z values (if no axis) :two:
  Note that the returned value will be 0 if no value is available

**Raises**:

  MartyCommandException if the axis is unknown

<a name="martypy.Marty.Marty.is_moving"></a>
#### is\_moving

```python
 | is_moving() -> bool
```

Check if Marty is moving :two:

**Arguments**:

  none

**Returns**:

  True if Marty is moving

<a name="martypy.Marty.Marty.stop"></a>
#### stop

```python
 | stop(stop_type: Optional[str] = None) -> bool
```

Stop Marty's movement  :one: :two:

You can also control what way to "stop" you want with the parameter stop_type. For instance:

* 'clear queue' to finish the current movement before stopping (clear any queued movements)
* 'clear and stop' stop immediately (and clear queues)
* 'clear and disable' :one: stop and disable the robot
* 'clear and zero' stop and move back to get_ready pose
* 'pause' pause motion
* 'pause and disable' :one: pause motion and disable the robot

**Arguments**:

- `stop_type` - the way to stop - see the options above
  

**Raises**:

  MartyCommandException if the stop_type is unknown

<a name="martypy.Marty.Marty.resume"></a>
#### resume

```python
 | resume() -> bool
```

Resume Marty's movement after a pause :two:

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.hold_position"></a>
#### hold\_position

```python
 | hold_position(hold_time: int) -> bool
```

Hold Marty at its current position :two:

**Arguments**:

  hold_time, time to hold position in milli-seconds

**Returns**:

  True if Marty accepted the request

<a name="martypy.Marty.Marty.is_paused"></a>
#### is\_paused

```python
 | is_paused() -> bool
```

Check if Marty is paused :two:

**Returns**:

  True if Marty is paused

<a name="martypy.Marty.Marty.move_joint"></a>
#### move\_joint

```python
 | move_joint(joint_name_or_num: Union[int, str], position: int, move_time: int) -> bool
```

Move a specific joint to a position :one: :two:

**Arguments**:

- `joint_name_or_num` - joint to move, see the Marty.JOINT_IDS dictionary (can be name or number)
- `position` - angle in degrees
- `move_time` - how long this movement should last, in milliseconds

**Returns**:

  True if Marty accepted the request

**Raises**:

  MartyCommandException if the joint_name_or_num is unknown

<a name="martypy.Marty.Marty.get_joint_position"></a>
#### get\_joint\_position

```python
 | get_joint_position(joint_name_or_num: Union[int, str]) -> float
```

Get the position (angle in degrees) of a joint :two:

**Arguments**:

- `joint_name_or_num` - see the Marty.JOINT_IDS dictionary (can be name or number)

**Returns**:

  Angle of the joint in degrees

**Raises**:

  MartyCommandException if the joint_name_or_num is unknown

<a name="martypy.Marty.Marty.get_joint_current"></a>
#### get\_joint\_current

```python
 | get_joint_current(joint_name_or_num: Union[int, str]) -> float
```

Get the current (in milli-Amps) of a joint :one: :two:
This can be useful in detecting when the joint is working hard and is related
to the force which the joint's motor is exerting to stay where it is

**Arguments**:

- `joint_name_or_num` - see the Marty.JOINT_IDS dictionary (can be name or number)

**Returns**:

  the current of the joint in milli-Amps (this will be 0 if the joint current is unknown)

**Raises**:

  MartyCommandException if the joint_name_or_num is unknown

<a name="martypy.Marty.Marty.get_joint_status"></a>
#### get\_joint\_status

```python
 | get_joint_status(joint_name_or_num: Union[int, str]) -> int
```

Get information about a joint :two:
This can be helpful to find out if the joint is working correctly and if it is
moving at the moment, etc

**Arguments**:

- `joint_name_or_num` - see the Marty.JOINT_IDS dictionary (can be name or number)

**Returns**:

  a code number which is the sum of codes in the Marty.JOINT_STATUS dictionary
  will be 0 if the joint status is unknown

**Raises**:

  MartyCommandException if the joint_name_or_num is unknown

<a name="martypy.Marty.Marty.get_distance_sensor"></a>
#### get\_distance\_sensor

```python
 | get_distance_sensor() -> float
```

Get the latest value from the distance sensor :one: :two:

**Returns**:

  The distance sensor reading (will return 0 if no distance sensor is found)

<a name="martypy.Marty.Marty.get_battery_remaining"></a>
#### get\_battery\_remaining

```python
 | get_battery_remaining() -> float
```

Get the battery remaining percentage :two:

**Returns**:

  The battery remaining capacity in percent

<a name="martypy.Marty.Marty.save_calibration"></a>
#### save\_calibration

```python
 | save_calibration() -> bool
```

Set the current motor positions as the zero positions :one: :two:
BE CAREFUL, this can cause unexpected movement or self-interference

<a name="martypy.Marty.Marty.clear_calibration"></a>
#### clear\_calibration

```python
 | clear_calibration() -> bool
```

Tell Marty to forget it's calibration :one: :two:
BE CAREFUL, this can cause unexpected movement or self-interference

<a name="martypy.Marty.Marty.is_calibrated"></a>
#### is\_calibrated

```python
 | is_calibrated() -> bool
```

Check if Marty is calibrated :two:

<a name="martypy.Marty.Marty.get_robot_status"></a>
#### get\_robot\_status

```python
 | get_robot_status() -> Dict
```

Get status of Marty the Robot :two:

**Arguments**:

  none

**Returns**:

  Dictionary containing:
  "workQCount" number of work items (movements) that are queued up
- `"isMoving"` - True if Marty is moving
- `"isPaused"` - True if Marty is paused
- `"isFwUpdating"` - True if Marty is doing an update

<a name="martypy.Marty.Marty.get_joints"></a>
#### get\_joints

```python
 | get_joints() -> Dict
```

Get information on all of Marty's joints :two:

**Arguments**:

  none

**Returns**:

  Dictionary containing dictionaries (one for each joint) each of which contain:
- `"IDNo"` - the joint identification number (see Marty.JOINT_IDS)
- `"name"` - the name of the joint
- `"pos"` - the angle of the joint
- `"current"` - the joint current (in milli-Amps)
- `"enabled"` - True if the servo is enabled
- `"commsOK"` - True if the servo is communicating ok
- `"flags"` - joint status flags (see Marty.JOINT_STATUS)

<a name="martypy.Marty.Marty.get_power_status"></a>
#### get\_power\_status

```python
 | get_power_status() -> Dict
```

Get information on Marty's battery and power supply :two:

**Arguments**:

  none

**Returns**:

  Dictionary containing:
  "remCapPC" remaining battery capacity in percent
- `"tempDegC"` - battery temperature in degrees C
- `"remCapMAH"` - remaining battery capacity in milli-Amp-Hours
- `"fullCapMAH"` - capacity of the battery when full in milli-Amp-Hours
- `"currentMA"` - current the battery is supplying (or being charged with) milli-Amps
- `"power5VOnTimeSecs"` - number of seconds the power to joints and add-ons has been on
- `"isOnUSBPower"` - True if Marty is running on power from the USB connector
- `"is5VOn"` - True if power to the joints and add-ons is turned on

<a name="martypy.Marty.Marty.get_add_ons_status"></a>
#### get\_add\_ons\_status

```python
 | get_add_ons_status() -> Dict
```

Get latest information for all add-ons :two:

**Arguments**:

  none

**Returns**:

  Dictionary containing dictionaries (one for each add-on) each of which contain:
- `"IDNo"` - the add-on identification number
- `"name"` - the name of the add-on
- `"type"` - the type of the add-on (see Marty.ADD_ON_TYPE_NAMES but it may not be in this list)
- `"whoAmITypeCode"` - a code which can be used for further add-on identification
- `"valid"` - True if the data is valid
- `"data"` - 10 bytes of data from the add-on - the format of this data depends
  on the type of add-on

<a name="martypy.Marty.Marty.get_add_on_status"></a>
#### get\_add\_on\_status

```python
 | get_add_on_status(add_on_name_or_id: Union[int, str]) -> Dict
```

Get latest information for a single add-on :two:

**Arguments**:

- `add_on_name_or_id` - either the name or the id (number) of an add-on

**Returns**:

  Dictionary containing:
- `"IDNo"` - the add-on identification number
- `"valid"` - True if the data is valid
- `"data"` - 10 bytes of data from the add-on - the format of this data depends
  on the type of add-on

<a name="martypy.Marty.Marty.get_system_info"></a>
#### get\_system\_info

```python
 | get_system_info() -> Dict
```

Get information about Marty :two:

**Arguments**:

  none

**Returns**:

  Dictionary containing:
- `"HardwareVersion"` - string containing the version of Marty hardware
  "1.0" for Marty V1
  "2.0" for Marty V2
  other values for later versions of Marty
- `"SystemName"` - the name of the physical hardware in Marty - this will be
  RicFirmwareESP32 for Marty V2 and
  MartyV1 for Marty V1
- `"SystemVersion"` - a string in semantic versioning format with the version
  of Marty firmware (e.g. "1.2.3")
- `"SerialNo"` - serial number of this Marty
- `"MAC"` - the base MAC address of the Marty

<a name="martypy.Marty.Marty.set_marty_name"></a>
#### set\_marty\_name

```python
 | set_marty_name(name: str) -> bool
```

Set Marty's name :two:

**Arguments**:

  name to call Marty

**Returns**:

  True if successful in setting the name

<a name="martypy.Marty.Marty.get_marty_name"></a>
#### get\_marty\_name

```python
 | get_marty_name() -> str
```

Get Marty's name :two:

**Arguments**:

  none

**Returns**:

  the name given to Marty

<a name="martypy.Marty.Marty.is_marty_name_set"></a>
#### is\_marty\_name\_set

```python
 | is_marty_name_set() -> bool
```

Check if Marty's name is set :two:

**Arguments**:

  none

**Returns**:

  True if Marty's name is set

<a name="martypy.Marty.Marty.get_hw_elems_list"></a>
#### get\_hw\_elems\_list

```python
 | get_hw_elems_list() -> List
```

Get a list of all of the hardware elements on Marty :two:

**Arguments**:

  none

**Returns**:

  List containing a dictionary for each hardware element, each element is in the form:
- `"name"` - name of the hardware element
- `"type"` - type of element, see Marty.HW_ELEM_TYPES, other types may appear as add-ons
- `"busName"` - name of the bus the element is connected to
- `"addr"` - address of the element if it is connected to a bus
- `"addrValid"` - 1 if the address is valid, else 0
- `"IDNo"` - identification number of the element
- `"whoAmI"` - string from the hardware which may contain additional identification
- `"whoAmITypeCode"` - string indicating the type of hardware
- `"SN"` - serial number of the hardware element
- `"versionStr"` - version string of hardware element in semantic versioning (semver) format
- `"commsOK"` - 1 if the element is communicating ok, 0 if not

<a name="martypy.Marty.Marty.send_ric_rest_cmd"></a>
#### send\_ric\_rest\_cmd

```python
 | send_ric_rest_cmd(ricRestCmd: str) -> None
```

Send a command in RIC REST format to Marty :two:

This is a special purpose command which you can use to do advanced
control of Marty

**Arguments**:

- `ricRestCmd` - string containing the command to send to Marty

**Returns**:

  None

<a name="martypy.Marty.Marty.send_ric_rest_cmd_sync"></a>
#### send\_ric\_rest\_cmd\_sync

```python
 | send_ric_rest_cmd_sync(ricRestCmd: str) -> Dict
```

Send a command in RIC REST format to Marty and wait for reply :two:

This is a special purpose command which you can use to do advanced
control of Marty

**Arguments**:

- `ricRestCmd` - string containing the command to send to Marty

**Returns**:

  Dictionary containing the response received from Marty

<a name="martypy.Marty.Marty.get_motor_current"></a>
#### get\_motor\_current

```python
 | get_motor_current(motor_id: int) -> float
```

Get current flowing through a joint motor :one: :two:

**Arguments**:

  motor_id, integer >= 0 (non-negative) selects which motor to query

**Returns**:

  Instantaneous current sense reading from motor `motor_id`

<a name="martypy.Marty.Marty.enable_motors"></a>
#### enable\_motors

```python
 | enable_motors(enable: bool = True, clear_queue: bool = True) -> bool
```

Toggle power to motors :one:

**Arguments**:

- `enable` - True/False toggle
- `clear_queue` - Default True, prevents unfinished but 'muted' motions
  from jumping as soon as motors are enabled

<a name="martypy.Marty.Marty.enable_safeties"></a>
#### enable\_safeties

```python
 | enable_safeties(enable: bool = True) -> bool
```

Tell the board to turn on 'normal' safeties :one:

<a name="martypy.Marty.Marty.fall_protection"></a>
#### fall\_protection

```python
 | fall_protection(enable: bool = True) -> bool
```

Toggle fall protections :one:

**Arguments**:

- `enable` - True/False toggle

<a name="martypy.Marty.Marty.motor_protection"></a>
#### motor\_protection

```python
 | motor_protection(enable: bool = True) -> bool
```

Toggle motor current protections :one:

**Arguments**:

- `enable` - True/False toggle

<a name="martypy.Marty.Marty.battery_protection"></a>
#### battery\_protection

```python
 | battery_protection(enable: bool = True) -> bool
```

Toggle low battery protections :one:

**Arguments**:

- `enable` - True/False toggle

<a name="martypy.Marty.Marty.buzz_prevention"></a>
#### buzz\_prevention

```python
 | buzz_prevention(enable: bool = True) -> bool
```

Toggle motor buzz prevention :one:

**Arguments**:

- `enable` - True/False toggle

<a name="martypy.Marty.Marty.lifelike_behaviour"></a>
#### lifelike\_behaviour

```python
 | lifelike_behaviour(enable: bool = True) -> bool
```

Tell the robot whether it can or can't move now and then in a lifelike way when idle. :one:

**Arguments**:

- `enable` - True/False toggle

<a name="martypy.Marty.Marty.ros_command"></a>
#### ros\_command

```python
 | ros_command(*byte_array: int) -> bool
```

Low level proxied access to the ROS Serial API between 
the modem and main controller :one:

<a name="martypy.Marty.Marty.keyframe"></a>
#### keyframe

```python
 | keyframe(time: float, num_of_msgs: int, msgs) -> List[bytes]
```

Takes in information about movements and generates keyframes
returns a list of bytes :one:

**Arguments**:

- `time` - time (in seconds) taken to complete movement
- `num_of_msgs` - number of commands sent
- `msgs` - commands sent in the following format [(ID CMD), (ID CMD), etc...]

<a name="martypy.Marty.Marty.get_chatter"></a>
#### get\_chatter

```python
 | get_chatter() -> bytes
```

Return chatter topic data (variable length) :one:

<a name="martypy.Marty.Marty.get_firmware_version"></a>
#### get\_firmware\_version

```python
 | get_firmware_version() -> bool
```

Ask the board to print the firmware version over chatter :one:

<a name="martypy.Marty.Marty.ros_serial_formatter"></a>
#### ros\_serial\_formatter

```python
 | ros_serial_formatter(topicID: int, send: bool = False, *message: int) -> List[int]
```

Formats message into ROS serial format and
returns formatted message as a list :one:  

Calls ros_command with the processed message if send is True.
More information about the ROS serial format can be
found here: http://wiki.ros.org/rosserial/Overview/Protocol

<a name="martypy.Marty.Marty.pinmode_gpio"></a>
#### pinmode\_gpio

```python
 | pinmode_gpio(gpio: int, mode: str) -> bool
```

Configure a GPIO pin :one:

**Arguments**:

- `gpio` - pin number between 0 and 7
- `mode` - choose from: 'digital in','analog in' or 'digital out'

<a name="martypy.Marty.Marty.write_gpio"></a>
#### write\_gpio

```python
 | write_gpio(gpio: int, value: int) -> bool
```

Write a value to a GPIO port :one:

<a name="martypy.Marty.Marty.digitalread_gpio"></a>
#### digitalread\_gpio

```python
 | digitalread_gpio(gpio: int) -> bool
```

Read from GPIO :one:

**Arguments**:

  GPIO pin number, >= 0 (non-negative)

**Returns**:

  Returns High/Low state of a GPIO pin

<a name="martypy.Marty.Marty.set_parameter"></a>
#### set\_parameter

```python
 | set_parameter(*byte_array: int) -> bool
```

Set board parameters :one:

**Arguments**:

- `byte_array` - a list in the following format [paramID, params]

<a name="martypy.Marty.Marty.i2c_write"></a>
#### i2c\_write

```python
 | i2c_write(*byte_array: int) -> bool
```

Write a bytestream to the i2c port. :one:  

The first byte should be the address, following from that
the datagram folows standard i2c spec

<a name="martypy.Marty.Marty.i2c_write_to_ric"></a>
#### i2c\_write\_to\_ric

```python
 | i2c_write_to_ric(address: int, byte_array: bytes) -> bool
```

Write a formatted bytestream to the i2c port. :one:  

The bytestream is formatted in the ROS serial format.

address: the other device's address

<a name="martypy.Marty.Marty.i2c_write_to_rick"></a>
#### i2c\_write\_to\_rick

```python
 | i2c_write_to_rick(address: int, byte_array: bytes) -> bool
```

Write a formatted bytestream to the i2c port. :one:  

The bytestream is formatted in the ROS serial format.
address: the other device's address

<a name="martypy.Marty.Marty.get_battery_voltage"></a>
#### get\_battery\_voltage

```python
 | get_battery_voltage() -> float
```

Get the voltage of the battery :one:

**Returns**:

  The battery voltage reading as a float in Volts

<a name="martypy.Marty.Marty.hello"></a>
#### hello

```python
 | hello() -> bool
```

Zero joints and wiggle eyebrows :one:

<a name="martypy.Marty.Marty.discover"></a>
#### discover

```python
 | discover() -> List[str]
```

Try and find us some Martys! :one:

<a name="martypy.Marty.Marty.__del__"></a>
#### \_\_del\_\_

```python
 | __del__() -> None
```

Marty is stopping

<a name="martypy.Marty.Marty.close"></a>
#### close

```python
 | close() -> None
```

Close connection to Marty

