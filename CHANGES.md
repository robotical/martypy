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
