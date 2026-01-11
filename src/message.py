class Message:
    def __init__(self, author: str, receiver, content):
        self.author = author
        self.content = content
        self.receiver = receiver

    def contentType(self) -> type: return type(self.content)

    def __str__(self): return self.author