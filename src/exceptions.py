from src.Logger import Logger
import inspect

class SystemQueueMessageException(Exception):
    def __init__(self, message, log:Logger=None):
        self.caller = inspect.getouterframes(inspect.currentframe(),2)[1].function
        self.message = message
        if not log is None: log.print(self.__str__(),1)

    def __str__(self): return "SQMSubscribeException.{}: {}".format(
        self.caller(),
        self.message
    )

class SQMSubscribeException(SystemQueueMessageException):
    def __init__(self, message, log: Logger = None):
        super().__init__(message, log)

class SQMPushMessageExeption(SystemQueueMessageException):
    def __init__(self, message, log: Logger = None):
        super().__init__(message, log)