import os
import threading
from .exceptions import *
from .message import Message
from .queue import Queue
from .sqmKey import SQMKey

SQM_QUEUEKEY_PREFIX = "QUEUE"
SQM_DEBUGKEY = "dbg"
def isEmpty(d:list or dict) -> bool: return len(d) == 0

timeOutTime : int = 1
sqm = None
log : Logger = None
class SystemQueueMessage:
    @staticmethod
    def keyToHash(key):
        if isinstance(key,str):
            return SQMKey(key).__hash__()
        elif isinstance(key,SQMKey) and isinstance(key.key,str):
            return key.__hash__()
        elif isinstance(key,int):
            return key
        elif isinstance(key,SQMKey) and isinstance(key.key,int):
            return key.key

    def __init__(self, logger:Logger, timeOutWaitingSeconds:float=5.0):
        self.log = logger
        self._queue = {}
        self._events = {}

        global timeOutTime
        timeOutTime = timeOutWaitingSeconds

        global sqm
        sqm = self
        global log
        log = logger

    def _methodeWithDebug(func):
        def wrapper(*args, **kwargs):
            global log
            if os.environ.get(SQM_DEBUGKEY)=="True" and log is not None:
                log.print("(SQM) {} has been called by {}, args={}".format(func.__name__, inspect.getouterframes(inspect.currentframe(), 2)[1].function, args),4)
            try:
                return func(*args, **kwargs)
            except KeyError:
                return None
            except IndexError:
                return None

        return wrapper

    def _getQueuesKeyFromEnviroment(self)->list[int]:
        list = []
        for i in os.environ:
            if i.find(SQM_QUEUEKEY_PREFIX) != -1:
                list.append(self.createQueue(os.environ[i]))
        self.log.print("(SQMS) {}".format(f"found {len(self._queue)} queues key from enviroment." if not isEmpty(self._queue) else "Queues not found in enviroment."),0 if not isEmpty(self._queue) else 1,False)
        return list

    @_methodeWithDebug
    def geEventByKey(self, key:str) -> threading.Event:
        key = self.keyToHash(key)
        return self._events[key][0]

    def addThreadListenerToEvents(self, key:str, thread:threading.Thread) -> bool:
        key = self.keyToHash(key)
        if thread in self._events[key][1]: raise SystemQueueMessageException("(SQM) Listener event thread {} already exists.".format(thread.name))
        self._events[key][1].append(thread)
        return True

    @_methodeWithDebug
    def SQMSubscribe(func)  -> threading.Thread:
        """
        Create a new thread for waiting new messages on "queue". On youre function u always adding to params SQMKEY.
        :return: Thread
        """
        def wrapper(*args, **kwargs):
            key = None
            global sqm,log

            for i in args:
                if isinstance(i, SQMKey): key = sqm.keyToHash(i)
            if key is None:
                raise SQMSubscribeException("(SQMS) Not found queue key in reqiest.", log=log)

            if os.environ.get(SQM_DEBUGKEY) == "True":
                log.print("(SQMS) Succsefuly get SQM,KEY{} from function {}".format(",LOGGER" if log is None else "",func.__name__),4)

            def threadFunc(*args, **kwargs):
                global timeOutTime,log

                while(True):
                    event = sqm.geEventByKey(key)
                    if event is None:
                        if not log is None: log.print("Listening queue has been removed, exit from thread '{}'.".format(func.__name__),1)
                        return
                    if not event.wait(timeOutTime if timeOutTime == None or timeOutTime>0 else None): continue
                    func(*args, **kwargs)
                    event.clear()
                return
            try:
                thread = threading.Thread(target=threadFunc, args=(*args,), name=f"SQMS.{func.__name__}")
                thread.start()
                print(sqm.getQueueKeys(),key)
                sqm.addThreadListenerToEvents(key, thread)
                if log is not None:
                    log.print("(SQMS) Thread {} has been succseful created and started.".format(thread.name),0)
            except:
                if log is not None:
                    log.print("(SQMS) Failed create thread.",1)
                pass
            return thread
        return wrapper
    def getQueueKeys(self): return self._queue.keys()
    @_methodeWithDebug
    def createQueue(self,key:str, requirementTypes:list[str]=None) -> int:
        """
        :param key: Get String, in func change to hash
        :return: hash queue
        """
        key = SQMKey(key).__hash__()
        if key in self._queue: raise SystemQueueMessageException("(SQM) key alredy in queue.",log=self.log)
        self._queue[key] = Queue(key, requirementTypes)
        self._events[key] = (threading.Event(),[])
        return key

    def builderMessages(self, author:str, content, receiver):
        return Message(author, receiver, content)

    @_methodeWithDebug
    def pushMessage(self,key:str, msg:Message) -> bool:
        key = self.keyToHash(key)
        try:
            if not self._queue[key].checkType(msg.content):
                raise SQMPushMessageExeption("(SQM) Messege content type {} not required types queue.".format(type(msg.content)), log=self.log)
        except KeyError:
            raise SQMPushMessageExeption("(SQM) Invalid queue key {}.".format(key),log=log)
        self._queue[key].append(msg)
        self._events[key][0].set()

        return True

    @_methodeWithDebug
    def popMSGFirst(self,key:str) -> Message:
        return self._queue[self.keyToHash(key)].pop(0)
    @_methodeWithDebug
    def popMSGLast(self,key:str) -> Message:
        return self._queue[self.keyToHash(key)].pop(-1)

    def getQueueListeners(self,key:str) -> list[threading.Thread]: return self._events[self.keyToHash(key)][1]