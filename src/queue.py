class Queue:
    def __init__(self, key: str, requiredTypes: list[str]):
        self.key = key
        self._queue = []
        self._requiredTypes = requiredTypes

    def append(self, msg):self._queue.append(msg)
    def pop(self, index: int): return self._queue.pop(index)

    def getQueue(self): return self._queue.copy()
    def setQueue(self, queue: list): self._queue = queue

    def checkType(self, T:object)->bool:
        if not self._requiredTypes: return True
        return type(T) in self._requiredTypes

    def messegeCount(self) -> int: return len(self._queue)

    def __str__(self): return self.key