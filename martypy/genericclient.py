from .utils import dict_merge
from .exceptions import (UnavailableCommandException,
                         MartyCommandException)


class GenericClient(object):
    '''
    Provides useful common members to child classes
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initialise the client class.
        COMMANDS_LUT is initialised as empty
        '''

    COMMANDS_LUT = dict()


    def execute(self, *args, **kwargs):
        '''
        Execute the command prescribed by the commands lookup table
        '''
        try:
            return self.COMMANDS_LUT[args[0]](self, *args, **kwargs)
        except KeyError:
            raise UnavailableCommandException("The command '{}' is not available "
                                              "from the {} client type"
                                              "".format(args[0], str(self.__class__.__name__)))
        except Exception as e:
            raise MartyCommandException(e)


    def register_commands(self, handlers):
        '''
        Take {str:func} command names & handlers in handlersa dict
        and register them with the COMMANDS_LUT
        '''
        self.COMMANDS_LUT = dict_merge(self.COMMANDS_LUT, handlers)
