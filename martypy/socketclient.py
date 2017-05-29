import six
import socket
import struct
from .genericclient import GenericClient
from .exceptions import MartyConnectException


class SocketClient(GenericClient):
    '''
    Lower level interface class between the `Marty` abstracted
    control class and the Rick socket interface
    '''

    SOCKET_PORT = 24
    
    def __init__(self, loc, port=None):
        '''
        Initialise connection to remote Marty over a IPv4 socket by name 'loc' over port 24

        Args:
            loc, type str, must either resolve to an IP or be an IP address

        Raises:
            MartyConnectException if the socket failed to make the connection to the host
        '''
        GenericClient.__init__(self)
        if port is None:
            port = self.SOCKET_PORT
 
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            loc_ip = socket.gethostbyname(loc)
            self.sock.connect((loc_ip, port))
        except Exception as e:
            raise MartyConnectException(e)

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
            'enable_motors'      : None,
            'disable_motors'     : None,
            'fall_protection'    : None,
            'motor_protection'   : None,
            'battery_protection' : None,
            'save_calibration'   : None,
            'ros_command'        : self.command,
        })


    # Encodes Command Type flag, LSB size, MSB size, Data
    CMD_OPCODES = {
        'battery'            : [0x01, 0x01, 0x00],
        'accel'              : [0x01, 0x02],
        'motorcurrent'       : [0x01, 0x03],
        'gpio'               : [0x01, 0x04],
        'hello'              : [0x02, 0x01, 0x00, 0x00], #
        'lean'               : [0x02, 0x05, 0x00, 0x02], #
        'walk'               : [0x02, 0x06, 0x00, 0x03], #
        'eyes'               : [0x02, 0x02, 0x00, 0x04], #
        'kick'               : [0x02, 0x05, 0x00, 0x05], #
        'lift_leg'           : [0x02, 0x06, 0x00, 0x06], # NotImplemented on board
        'lower_leg'          : [0x02, 0x06, 0x00, 0x07], # NotImplemented on board
        'celebrate'          : [0x02, 0x03, 0x00, 0x08], #
        'arms'               : [0x02, 0x05, 0x00, 0x0B], #
        'sidestep'           : [0x02, 0x06, 0x00, 0x0E], #
        'stand_straight'     : [0x02, 0x03, 0x00, 0x0F], # NotImplemented on board
        'play_sound'         : [0x02, 0x07, 0x00, 0x10], # OK
        'stop'               : [0x02, 0x02, 0x00, 0x11], #
        'move_joint'         : [0x02, 0x05, 0x00, 0x12], #
        'enable_motors'      : [0x02, 0x01, 0x00, 0x13], # Subject to change
        'disable_motors'     : [0x02, 0x01, 0x00, 0x14], # Subject to change
        'fall_protection'    : [0x02, 0x02, 0x00, 0x15], #
        'motor_protection'   : [0x02, 0x02, 0x00, 0x16], #
        'battery_protection' : [0x02, 0x02, 0x00, 0x17], #
        'save_calibration'   : [0x02, 0x01, 0x00, 0xFF], #
        'ros_command'        : [0x03],                   # Variable Length
    }



    def pack(self, characters):
        '''
        Pack characters list into a byte string
        '''
        return six.b("".join(map(chr, characters)))


    def little_endian(self, integer):
        '''
        Return the little endian 'short' (2 byte) encoding of the int
        '''
        return struct.pack('<h', integer)


    def fixed_command(self, *args, **kwargs):
        '''
        Send a command with a fixed (preknown) number of arguments
        that does not expect a response
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd]
        datalen = opcode[1] + (opcode[2] << 8) - 1
        data = list(args[2:])
        if len(data) != datalen:
            raise TypeError('{} takes {} arguments but {} were given'
                            ''.format(cmd, datalen, len(data)))
        self.sock.send(self.pack(opcode + data))


    def command(self, *args, **kwargs):
        '''
        Pipes args down the socket whilst calculating the payload length
        Args:
            *args of length at least 3
        TODO: test for large payloads
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd][0]
        data = list(args[2:])
        datalen = struct.pack('<i', len(data))
        payload = six.int2byte(opcode) + datalen + self.pack(data)
        self.sock.send(payload)


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

