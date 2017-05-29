from .genericclient import GenericClient

class SerialClient(GenericClient):

    def __init__(self, *args, **kwargs):
        GenericClient.__init__(self)
        raise NotImplementedError()
