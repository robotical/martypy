Version 3.5.0 :
- Add streaming sound support

Version 3.4.0 :
- Support for ground and obstacle detection using the IR/Colour foot sensors
- User callbacks on data received from the robot in the background
- Automatically re-establish the WiFi connection if Marty reboots

Version 3.3.1 :
- Improved connection setup process (preparation for higher USB speeds)

Version 3.3.0 :
- New functions for controlling the disco add-on lights
- New distance sensor function for Marty V2 that returns the distance in mm

Version 3.2.1 :
- Default `movetime` parameter for the `dance()` has been changed to 3000ms instead of 4500ms

Version 3.2.0 :
- New `Marty.add_on_query` method provides low-level access to Marty's addons
- New `Marty.is_conn_ready` method for checking if Marty is connected
- Small changes to the dictionary returned by `get_power_status()`
- Stale power, servo and other information is no longer presented if updates from Marty cease
- Various under-the-hood improvements, bugfixes and preparations for future features

Version 3.1.0 :
- Automatic Marty discovery when connecting over USB

Version 3.0.3 :
- Improved default parameters for `wiggle()` and `sidestep()`

Version 3.0.0 :
- **Blocking Mode**
  - You can now select whether movement commands are blocking or non-blocking.
  - The default behaviour changed from non-blocking to blocking.
- New `stand_straight()` method matching the "Stand straight in <...>" Scratch block.
- Marty V1 can `dance()` now!

Version 2.2.0 :
- Better defaults for movement commands
- Various bugfixes including:
  - The `walk()` command alternates steps by default
  - You can use one `sidestep()` command to take multiple side-steps
  - The `twist` argument to the `kick()` command now works
  - We got a bit confused about which is left and which is right but Marty explained it to us!

Version 2.1
: Fixes a bug when connecting to Marty V1

Version 2.0
: Added Marty V2 support
: Removed unnecessary imports
: Dropped Python 2 support

Version 1.2
: Addresses security issues in `requests` and `urllib3` dependencies

Version 1.1
: Adds ROSClient and Distance Sensor support

Version 1.0
: SocketClient and TestClient provided

Version 0.0.1 (Alpha)
: Adds initial API implementation for Socket-based control. Adds client class structure
