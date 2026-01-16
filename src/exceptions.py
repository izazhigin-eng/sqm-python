from src.Logger import Logger
import inspect

class SQMExpBody(Exception):
    def __init__(self, message, log:Logger=None):
        self.caller = inspect.getouterframes(inspect.currentframe(),2)[1].function
        self.message = message
        if not log is None: log.print(self.__str__(),1)

    def __str__(self): return "SQMSubscribeException.{}: {}".format(
        self.caller,
        self.message
    )
class SystemQueueMessageException(SQMExpBody):
    pass

class SQMSubscribeException(SQMExpBody):
    pass

class SQMPushMessageExeption(SQMExpBody):
    pass