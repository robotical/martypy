from .genericclient import GenericClient


class TestClient(GenericClient):
    '''
    Debugging and testing interface to spoof a connection to Marty
    '''

    def __init__(self, proto, loc, *args, **kwargs):
        GenericClient.__init__(self)
        print("Connected to '{}'".format(loc))


    def execute(self, *args, **kwargs):
        '''
        Print all commands received
        '''
        print('args {}  kwargs {}'.format(args, kwargs))

