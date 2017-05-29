import socket
from .exceptions import MartyConnectException

class SocketClient(object):
    '''
    Lower level interface class between `Marty` abstracted control class, and the socket interface
    '''
    
    def __init__(self, loc):
        '''
        Initialise connection to remote Marty over a IPv4 socket by name 'loc' over port 24

        Raises:
            MartyConnectException if the socket failed to make the connection to the host
        '''
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            loc_ip = socket.gethostbyname(loc)
            self.sock.connect((loc_ip, 24))
        except Exception as e:
            raise MartyConnectException(e)

