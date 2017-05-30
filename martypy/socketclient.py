import six
import sys
import socket
import struct
from .genericclient import GenericClient
from .exceptions import (MartyConnectException,
                         MartyCommandException,
                         ArgumentOutOfRangeException)


class SocketClient(GenericClient):
    '''
    Lower level interface class between the `Marty` abstracted
    control class and the Rick socket interface
    '''

    SOCKET_PORT = 24
    
    def __init__(self, proto, loc, port=None, timeout=5.0, *args, **kwargs):
        '''
        Initialise connection to remote Marty over a IPv4 socket by name 'loc' over port 24

        Args:
            loc, type str, must either resolve to an IP or be an IP address

        Raises:
            MartyConnectException if the socket failed to make the connection to the host
        '''
        GenericClient.__init__(self)
        if port is None:
            self.port = self.SOCKET_PORT
        else:
            self.port = port

        self.loc = loc
        self.timeout = timeout
        
        self.sock = self.socket_factory()

        # Extend basis LUT with specific handlers
        self.register_commands({
            'battery'            : self.simple_sensor,
            'accel'              : self.select_sensor,
            'motorcurrent'       : self.select_sensor,
            'gpio'               : self.select_sensor,
            'hello'              : self.fixed_command,
            'lean'               : self.fixed_command,
            'walk'               : self.fixed_command,
            'eyes'               : self.fixed_command,
            'kick'               : self.fixed_command,
            'lift_leg'           : self.fixed_command,
            'lower_leg'          : self.fixed_command,
            'celebrate'          : self.fixed_command,
            'arms'               : self.fixed_command,
            'sidestep'           : self.fixed_command,
            'stand_straight'     : self.fixed_command,
            'play_sound'         : self.fixed_command,
            'stop'               : self.fixed_command,
            'move_joint'         : self.fixed_command,
            'enable_motors'      : self.fixed_command,
            'disable_motors'     : self.fixed_command,
            'fall_protection'    : self.toggle_command,
            'motor_protection'   : self.toggle_command,
            'battery_protection' : self.toggle_command,
            'buzz_prevention'    : self.toggle_command,
            'save_calibration'   : self.fixed_command,
            'ros_command'        : self.command,
        })



    def socket_factory(self):
        '''
        Generate a new socket connection
        '''
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            loc_ip = socket.gethostbyname(self.loc)
            sock.connect((loc_ip, self.port))
        except Exception as e:
            raise MartyConnectException(e)

        sock.settimeout(self.timeout)

        if sys.platform == 'linux':
            # Configure socket in keepalive mode
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Time to wait before sending a keepalive
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
            # Interval between keepalives
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            # Number of keepalive fails before declaring the connection broken
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)

        elif sys.platform == 'windows':
            # Keep alive, 5 sec timeout, 1 sec interval
            sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 5000, 1000))

        return sock



    def __repr__(self):
        return '{}.{}{}'.format(self.__module__,
                             self.__class__.__name__,
                             self.sock.getsockname())


    # Encodes Command Type flag, LSB size, MSB size, Data
    CMD_OPCODES = {
        'battery'            : [0x01, 0x01, 0x00],       # OK
        'accel'              : [0x01, 0x02],             # OK, but CHECK AXES
        'motorcurrent'       : [0x01, 0x03],             # OK
        'gpio'               : [0x01, 0x04],             # OK
        'hello'              : [0x02, 0x01, 0x00, 0x00], # OK
        'lean'               : [0x02, 0x05, 0x00, 0x02], # 
        'walk'               : [0x02, 0x07, 0x00, 0x03], # 
        'eyes'               : [0x02, 0x02, 0x00, 0x04], # OK
        'kick'               : [0x02, 0x05, 0x00, 0x05], # 
        'lift_leg'           : [0x02, 0x06, 0x00, 0x06], # NotImplemented on board
        'lower_leg'          : [0x02, 0x06, 0x00, 0x07], # NotImplemented on board
        'celebrate'          : [0x02, 0x03, 0x00, 0x08], # OK
        'arms'               : [0x02, 0x05, 0x00, 0x0B], # 
        'sidestep'           : [0x02, 0x06, 0x00, 0x0E], # 
        'stand_straight'     : [0x02, 0x03, 0x00, 0x0F], # NotImplemented on board
        'play_sound'         : [0x02, 0x07, 0x00, 0x10], # OK
        'stop'               : [0x02, 0x02, 0x00, 0x11], # 
        'move_joint'         : [0x02, 0x05, 0x00, 0x12], # 
        'enable_motors'      : [0x02, 0x01, 0x00, 0x13], # OK, Subject to change
        'disable_motors'     : [0x02, 0x01, 0x00, 0x14], # OK, Subject to change
        'fall_protection'    : [0x02, 0x02, 0x00, 0x15], # 
        'motor_protection'   : [0x02, 0x02, 0x00, 0x16], # OK
        'battery_protection' : [0x02, 0x02, 0x00, 0x17], # OK
        'buzz_prevention'    : [0x02, 0x02, 0x00, 0x18], # OK
        'save_calibration'   : [0x02, 0x01, 0x00, 0xFF], # 
        'ros_command'        : [0x03],                   # Variable Length
    }


    def pack(self, characters):
        '''
        Pack characters list into a byte string
        '''
        try:
            return six.b("".join(map(chr, characters)))
        except UnicodeEncodeError:
            raise ArgumentOutOfRangeException('Argument(s) overflowed int')


    def little_endian(self, integer):
        '''
        Return the little endian 'short' (2 byte) encoding of the int
        '''
        return struct.pack('<h', integer)


    def fixed_command(self, *args, **kwargs):
        '''
        Send a command with a fixed (preknown) number of arguments
        that does not expect a response.
        NB!: Assumes data (args[2:]) is broken into 8-bit bytes
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd]
        datalen = opcode[1] + (opcode[2] << 8) - 1
        data = list(args[2:])
        if len(data) != datalen:
            raise TypeError('{} takes {} arguments but {} were given'
                            ''.format(cmd, datalen, len(data)))
        self.sock.send(self.pack(opcode + data))
        return True



    def command(self, *args, **kwargs):
        '''
        Pipes args down the socket whilst calculating the payload length
        Args:
            *args of length at least 3
        TODO: test for too-large payloads
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd][0]
        data = list(args[2:])
        datalen = struct.pack('<i', len(data))
        payload = six.int2byte(opcode) + datalen + self.pack(data)
        self.sock.send(payload)
        return True



    def toggle_command(self, *args, **kwargs):
        '''
        Takes a python Boolean and toggles a switch on the board
        '''
        cmd = args[1]
        toggle = 0x01 if args[2] == True else 0x00
        opcode = self.CMD_OPCODES[cmd]
        self.sock.send(self.pack(opcode + [toggle]))
        return toggle


    def simple_sensor(self, *args, **kwargs):
        '''
        Read a simple sensor and give its value
        Args:
            cmd
        '''
        cmd = args[1]
        self.sock.send(self.pack(self.CMD_OPCODES[cmd]))
        data = self.sock.recv(4)
        return struct.unpack('f', data)[0]


    def select_sensor(self, *args, **kwargs):
        '''
        Read a sensor that takes an argument and give its value
        Args:
            cmd, index
        '''
        cmd = args[1]
        index = int(args[2])
        self.sock.send(self.pack(self.CMD_OPCODES[cmd] + [index]))
        data = self.sock.recv(4)
        return struct.unpack('f', data)[0]

