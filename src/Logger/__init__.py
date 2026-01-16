import os, datetime,inspect
class Logger:
    def __init__(self):
        self.statusCodes = {0:"SUC",1:"FAIL",2:"NEU",4:"DEBUG"}
        self._fileName = "log.txt"
        self.lastCaller = None

        f = open(self._fileName,"w")
        f.write(f"{datetime.datetime.now()}, Start Application\n\n")

    def print(self, text, code=2, printMSG:bool=True):
        newCaller = inspect.getouterframes(inspect.currentframe())[0].function
        _text = "{}{}\n".format("["+self.statusCodes[code]+"]| " if code!=2 else "", text)
        print( _text,end="" )
        with open(self._fileName, "a") as f:
            f.write( _text )
            if newCaller != self.lastCaller:
                f.write("\n")
                print()
                self.lastCaller = newCaller
    def __str__(self): return __name__