import six
import time
import struct
import ctypes
from .genericclient import GenericClient
from .exceptions import UnavailableClientTypeException, ArgumentOutOfRangeException

try:
    import rospy
    from marty_msgs.msg import ByteArray, Accelerometer, MotorCurrents, GPIOs
    from std_msgs.msg import Float32, String
    have_ros = True
except ImportError:
    have_ros = False


class ROSClient(GenericClient):

    def __init__(self, debug=False,*args, **kwargs):
        GenericClient.__init__(self)

        if not have_ros:
            raise UnavailableClientTypeException('Unable to import rospy')

        self.sensor_value = Float32()
        self.acceleration = Accelerometer()
        self.currents = MotorCurrents()
        self.gpios = GPIOs()
        self.chatter_data = ''

        self.pub = rospy.Publisher('/marty/socket_cmd', ByteArray, queue_size=10)
        rospy.Subscriber('/marty/battery', Float32, self.simple_sensor_value)
        rospy.Subscriber('/marty/accel', Accelerometer, self.get_accel)
        rospy.Subscriber('/marty/motor_currents', MotorCurrents, self.get_currents)
        rospy.Subscriber('/marty/gpios', GPIOs, self.get_gpios)
        rospy.Subscriber('/marty/chatter', String, self.get_chatter)

        rospy.init_node('martypy_client', anonymous=True)

        self.debug = debug

        self.register_commands({
            # 'discover'           : self.discover,
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
            # 'fall_protection'    : self.toggle_command,   #Configure file on Pi
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


    # def __repr__(self):
    #     return '{}.{}{}'.format(self.__module__,
    #                          self.__class__.__name__,
    #                          self.sock.getsockname())


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


    def pack_signed_int(self, data):
        '''
        Packs unsigned int data to bytes
        '''
        packed_list = []
        for item in data:
            packed_list.append(ctypes.c_byte(ord(item)).value)
        return packed_list


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
                            ''.format(datalen, len(data)))
        self.pub.publish(self.pack_signed_int(opcode[3:] + data))
        return True



    def command(self, *args, **kwargs):
        '''
        Pipes args down the socket whilst calculating the payload length
        Args:
            *args of length at least 3
        '''
        cmd = args[1]
        opcode = self.CMD_OPCODES[cmd][0]
        data = list(*args[2:])
        datalen_lsb, datalen_msb = struct.pack('<H', len(data))
        payload = [opcode,
                   chr(six.byte2int([datalen_lsb])),
                   chr(six.byte2int([datalen_msb]))] + data
        self.pub.publish(self.pack_signed_int(payload))
        return True



    def toggle_command(self, *args, **kwargs):
        '''
        Takes a python Boolean and toggles a switch on the board
        '''
        cmd = args[1]
        toggle = '\x01' if args[2] == True else '\x00'
        opcode = self.CMD_OPCODES[cmd]
        # self.sock.send(self.pack(opcode + [toggle]))
        self.pub.publish(list(map(ord, opcode[3:])) + [ord(toggle)])
        return args[2]


    def simple_sensor_value(self, data):
        '''
        Called by ROS subscriber to update variable with requested sensor value
        '''
        self.sensor_value = data


    def simple_sensor(self, *args, **kwargs):
        '''
        Read a simple sensor and give its value
        Args:
            cmd
        '''
        cmd = args[1]
        while(self.sensor_value.data == 0.0):
            continue
        data = self.sensor_value.data
        return data


    def get_accel(self, data):
        '''
        Assign acceleration data to variable
        '''
        self.acceleration = data


    def get_currents(self, data):
        '''
        Assign motor currents data to variable
        '''
        self.currents = data


    def get_gpios(self, data):
        '''
        Assign gpio data to variable
        '''
        self.gpios = data


    def select_sensor(self, *args, **kwargs):
        '''
        Read a sensor that takes an argument and give i)ts value
        Args:(
            cmd, index
        '''
        cmd = args[1]
        index = args[2]
        if(cmd == 'accel'):
            if(index == '\x00'):
                return self.acceleration.x
            elif(index == '\x01'):
                return self.acceleration.y
            elif(index == '\x02'):
                return self.acceleration.z
        elif(cmd == 'motorcurrent'):
            return self.currents.current[int(index)]
        elif(cmd == 'gpio'):
            return  self.gpios.gpio[ord(index)]


    def get_chatter(self, data):
        '''
        Assign chatter data to variable
        '''
        self.chatter_data = data


    def chatter(self, *args, **kwargs):
        '''
        Return chatter topic data (variable length)
        '''
        cmd = args[1]
        while(self.chatter_data == ''):
            continue
        return self.chatter_data
