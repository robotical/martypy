import six
import sys
import time
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

    def __init__(self, proto, loc, port=None, timeout=5.0, debug=False, *args, **kwargs):
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

        self.debug = debug

        self.loc = loc
        self.timeout = timeout

        self.sock = self.socket_factory()

        # Extend basis LUT with specific handlers
        self.register_commands({
            'discover'           : self.discover,
            'battery'            : self.simple_sensor,
            'distance'           : self.simple_sensor,
            'accel'              : self.select_sensor,
            'motorcurrent'       : self.select_sensor,
            'gpio'               : self.select_sensor,
            'hello'              : self.fixed_command,
            'lean'               : self.fixed_command,
            'walk'               : self.fixed_command,
            'kick'               : self.fixed_command,
            'celebrate'          : self.fixed_command,
            'arms'               : self.fixed_command,
            'sidestep'           : self.fixed_command,
            'circle_dance'       : self.fixed_command,
            'play_sound'         : self.fixed_command,
            'stop'               : self.fixed_command,
            'move_joint'         : self.fixed_command,
            'enable_motors'      : self.fixed_command,
            'disable_motors'     : self.fixed_command,
            'enable_safeties'    : self.fixed_command,
            'fall_protection'    : self.toggle_command,
            'motor_protection'   : self.toggle_command,
            'battery_protection' : self.toggle_command,
            'buzz_prevention'    : self.toggle_command,
            'lifelike_behaviour' : self.toggle_command,
            'clear_calibration'  : self.fixed_command,
            'save_calibration'   : self.fixed_command,
            'ros_command'        : self.command,
            'chatter'            : self.chatter,
            'set_param'          : self.command,
            'firmware_version'   : self.fixed_command,
            'mute_serial'        : self.fixed_command,
            'i2c_write'          : self.command,
            'gpio_write'         : self.fixed_command,
            'gpio_mode'          : self.fixed_command,
        })

        # for opcode, _ in self.COMMANDS_LUT.items():
        #     if opcode not in self.CMD_OPCODES.keys():
        #         print('Missing {}'.format(opcode))


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


    @staticmethod
    def discover(timeout=10, *args, **kwargs):
        '''
        Search for Marties on the network using a UDB multicast to port 4000
        '''
        socket_addr = "224.0.0.1"
        socket_port = 4000
        magic_command = b"AA"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        sock.settimeout(timeout)
        sock.sendto(magic_command, (socket_addr, socket_port))

        found = []
        start = time.time()
        try:
            while (time.time() - start) < timeout:
                data, addr = sock.recvfrom(1000)
                found.append({addr: data})
        except socket.timeout:
            return found


    # Encodes Command Type flag, LSB size, MSB size, Data
    CMD_OPCODES = {
        'battery'            : ['\x01', '\x01', '\x00'],         # OK
        'distance'           : ['\x01', '\x08', '\x00'],         #
        'accel'              : ['\x01', '\x02'],                 # OK
        'motorcurrent'       : ['\x01', '\x03'],                 # OK
        'gpio'               : ['\x01', '\x04'],                 #
        'chatter'            : ['\x01', '\x05', '\x00',],        # Variable Length
        'hello'              : ['\x02', '\x01', '\x00', '\x00'], # OK
        'lean'               : ['\x02', '\x05', '\x00', '\x02'], #
        'walk'               : ['\x02', '\x07', '\x00', '\x03'], # OK
        'kick'               : ['\x02', '\x05', '\x00', '\x05'], # OK
        'celebrate'          : ['\x02', '\x03', '\x00', '\x08'], # OK
        'arms'               : ['\x02', '\x05', '\x00', '\x0B'], #
        'sidestep'           : ['\x02', '\x06', '\x00', '\x0E'], #
        'play_sound'         : ['\x02', '\x07', '\x00', '\x10'], #
        'stop'               : ['\x02', '\x02', '\x00', '\x11'], # OK
        'move_joint'         : ['\x02', '\x05', '\x00', '\x12'], #
        'enable_motors'      : ['\x02', '\x01', '\x00', '\x13'], # Has optional args now
        'disable_motors'     : ['\x02', '\x01', '\x00', '\x14'], # Has optional args now
        'circle_dance'       : ['\x02', '\x04', '\x00', '\x1C'], #
        'enable_safeties'    : ['\x02', '\x01', '\x00', '\x1E'], #
        'fall_protection'    : ['\x02', '\x02', '\x00', '\x15'], #
        'motor_protection'   : ['\x02', '\x02', '\x00', '\x16'], #
        'battery_protection' : ['\x02', '\x02', '\x00', '\x17'], #
        'buzz_prevention'    : ['\x02', '\x02', '\x00', '\x18'], #
        'lifelike_behaviour' : ['\x02', '\x02', '\x00', '\x1D'], #
        'clear_calibration'  : ['\x02', '\x01', '\x00', '\xFE'], #
        'save_calibration'   : ['\x02', '\x01', '\x00', '\xFF'], #
        'ros_command'        : ['\x03'],                         # Variable Length
        'set_param'          : ['\x02', '\x1F'], #
        'firmware_version'   : ['\x02', '\x01', '\x00', '\x20'], #
        'mute_serial'        : ['\x02', '\x01', '\x00', '\x21'], # OK
        'i2c_write'          : ['\x02'],                         #
        'gpio_write'         : ['\x02', '\x06', '\x00', '\x1A'], #
        'gpio_mode'          : ['\x02', '\x03', '\x00', '\x19'], #
    }


    def pack(self, characters):
        '''
        Pack characters list into a byte string
        Expects pre-packed chars, use chr or struct.pack to do this
        '''
        if self.debug:
            print(list(map(lambda x: '{}:{}'.format(x, type(x)), characters)))
        try:
            return six.b("".join(characters))
        except UnicodeEncodeError:
            raise ArgumentOutOfRangeException('Argument(s) overflowed int')



    def fixed_command(self, *args, **kwargs):
        '''
        Send a command with a fixed (preknown) number of arguments
        that does not expect a response.
        NB!: Assumes data (args[2:]) is broken into 8-bit bytes
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd]
        datalen = ord(opcode[1]) + (ord(opcode[2]) << 8) - 1
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
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd][0]
        data = list(args[2:])
        datalen_lsb, datalen_msb = struct.pack('<H', len(data))
        payload = [opcode,
                   chr(six.byte2int([datalen_lsb])),
                   chr(six.byte2int([datalen_msb]))] + data
        self.sock.send(self.pack(payload))
        return True



    def toggle_command(self, *args, **kwargs):
        '''
        Takes a python Boolean and toggles a switch on the board
        '''
        cmd = args[1]
        toggle = '\x01' if args[2] == True else '\x00'
        opcode = self.CMD_OPCODES[cmd]
        self.sock.send(self.pack(opcode + [toggle]))
        return args[2]


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
        index = args[2]
        self.sock.send(self.pack(self.CMD_OPCODES[cmd] + [index]))
        data = self.sock.recv(4)
        return struct.unpack('f', data)[0]



    def chatter(self, *args, **kwargs):
        '''
        Return chatter topic data (variable length)
        '''
        cmd = args[1]
        self.sock.send(self.pack(self.CMD_OPCODES[cmd]))
        data_length = six.byte2int(self.sock.recv(1))
        data = self.sock.recv(data_length)
        return data
