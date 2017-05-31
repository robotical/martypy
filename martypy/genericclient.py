from .utils import dict_merge
from .exceptions import (UnavailableCommandException,
                         MartyCommandException)


class GenericClient(object):
    '''
    Provides useful common members to child classes
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initialise the client class
        '''

    COMMANDS_LUT = {
        'battery'            : None,
        'accel'              : None,
        'motorcurrent'       : None,
        'gpio'               : None,
        'hello'              : None,
        'lean'               : None,
        'walk'               : None,
        'eyes'               : None,
        'kick'               : None,
        'lift_leg'           : None,
        'lower_leg'          : None,
        'celebrate'          : None,
        'arms'               : None,
        'sidestep'           : None,
        'stand_straight'     : None,
        'play_sound'         : None,
        'stop'               : None,
        'move_joint'         : None,
        'enable_motors'      : None,
        'disable_motors'     : None,
        'fall_protection'    : None,
        'motor_protection'   : None,
        'battery_protection' : None,
        'buzz_prevention'    : None,
        'save_calibration'   : None,
        'ros_command'        : None,
    }


    def execute(self, *args, **kwargs):
        '''
        Execute the command prescribed by the commands lookup table
        '''
        try:
            return self.COMMANDS_LUT[args[0]](self, *args, **kwargs)
        except TypeError:
            raise UnavailableCommandException("The command '{}' is not available "
                                              "from the {} client type"
                                              "".format(args[0], str(self.__class__.__name__)))
        except Exception as e:
            raise MartyCommandException(e)


    def register_commands(self, handlers):
        '''
        Take {str:func} command names & handlers in a dict
        and register them with the COMMANDS_LUT 
        '''
        self.COMMANDS_LUT = dict_merge(self.COMMANDS_LUT, handlers)

