from .genericclient import GenericClient

class ROSClient(GenericClient):

    def __init__(self, *args, **kwargs):
        GenericClient.__init__(self)
        raise NotImplementedError()

