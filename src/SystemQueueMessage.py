import os
import threading
from src.Logger import Logger
from .exceptions import *
from .message import Message
from .queue import Queue

SQM_QUEUEKEY_PREFIX = "QUEUE"
SQM_DEBUGKEY = "dbg"
def isEmpty(d:list or dict) -> bool: return len(d) == 0

timeOutTime = 1
class SystemQueueMessage:
    def __init__(self, log:Logger,autoConfigure:bool=True, timeOutWaitingSeconds:float=5.0):
        self.log = log
        self._queue = {}
        self._events = {}

        global timeOutTime
        timeOutTime = timeOutWaitingSeconds

        if autoConfigure:
            self._getQueuesKeyFromEnviroment()

    def _methodeWithDebug(func):
        def wrapper(*args, **kwargs):
            log = None
            for i in args:
                if isinstance(i, Logger):
                    log = i
                elif isinstance(i, SystemQueueMessage):
                    log = i.log
            if os.environ.get(SQM_DEBUGKEY)=="True" and log is not None:
                log.print("(SQM) {} has been called by {}, args={}".format(func.__name__, inspect.getouterframes(inspect.currentframe(), 2)[1].function, args),4)
            try:
                return func(*args, **kwargs)
            except KeyError:
                return None
            except IndexError:
                return None

        return wrapper

    def _getQueuesKeyFromEnviroment(self)->int:
        for i in os.environ:
            if i.find(SQM_QUEUEKEY_PREFIX) != -1:
                self.addQueue(os.environ[i])
        self.log.print("(SQMS) {}".format(f"found {len(self._queue)} queues key from enviroment." if not isEmpty(self._queue) else "Queues not found in enviroment."),0 if not isEmpty(self._queue) else 1,False)
        return len(self._queue)

    @_methodeWithDebug
    def geEventByKey(self, key:str) -> threading.Event: return self._events[key][0]

    def addThreadListenerToEvents(self, key:str, thread:threading.Thread) -> bool:
        if thread in self._events[key][1]: raise SystemQueueMessageException("(SQM) Listener event thread {} already exists.".format(thread.name))
        self._events[key][1].append(thread)
        return True

    @_methodeWithDebug
    def SQMSubscribe(func)  -> list[threading.Thread]:
        def wrapper(*args, **kwargs):
            sqm,key,log = None,None,None
            for i in args:
                if  isinstance(i, SystemQueueMessage): sqm = i
                elif isinstance(i, str): key = i
                elif isinstance(i, Logger): log = i

            if sqm is None:
                raise SQMSubscribeException("(SQMS) Not found SystemQueueMessage class in request.",log=log)
            if key is None:
                raise SQMSubscribeException("(SQMS) Not found queue key in reqiest.", log=log)
            if log is None: log = sqm.log

            if os.environ.get(SQM_DEBUGKEY) == "True":
                sqm.log.print("(SQMS) Succsefuly get SQM,KEY{} from function {}".format(",LOGGER" if log is None else "",func.__name__),4)

            def threadFunc(*args, **kwargs):
                log = None
                for i in args:
                    if isinstance(i,Logger): log = i
                    elif isinstance(i,SystemQueueMessage): log = i.log
                    global timeOutTime
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
                sqm.addThreadListenerToEvents(key, thread)
                if log is not None:
                    log.print("(SQMS) Thread {} has been succseful created and started.".format(thread.name),0)
            except:
                if log is not None:
                    log.print("(SQMS) Failed create thread.",1)
                pass

            return thread
        return wrapper

    @_methodeWithDebug
    def addQueue(self,key:str, requirementTypes:list[str]=None) -> bool:
        if key in self._queue: raise SystemQueueMessageException("(SQM) key alredy in queue.",log=self.log)
        self._queue[key] = Queue(key,requirementTypes)
        self._events[key] = (threading.Event(),[])
        return True
    @_methodeWithDebug
    def removeQueue(self,key:str) -> bool:
        nQueue = {}
        nEvents = {}
        for i in self._queue:
            if i != key:
                nQueue[key] = self._queue[i]
                nEvents[i] = self._events[i]
        self._queue[key] = nQueue
        self._events[key] = nEvents
        return True

    def builderMSG(self, author:str, content, receiver):
        return Message(author, receiver, content)

    @_methodeWithDebug
    def pushMessage(self,key:str, msg:Message) -> bool:
        try:
            if not self._queue[key].checkType(msg.content):
                raise SQMPushMessageExeption("(SQM) Messege content type {} not required types queue.".format(type(msg.content)), log=self.log)
        except KeyError:
            raise SQMPushMessageExeption("(SQM) Invalid queue key {}.".format(key),log=self.log)
        self._queue[key].append(msg)
        self._events[key][0].set()

        return True

    @_methodeWithDebug
    def popMSGFirst(self,key:str) -> Message:
        return self._queue[key].pop(0)
    @_methodeWithDebug
    def popMSGLast(self,key:str) -> Message:
        return self._queue[key].pop(-1)

    def getQueueListeners(self,key:str) -> list[threading.Thread]: return self._events[key][1]