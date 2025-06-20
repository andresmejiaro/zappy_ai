
from abc import ABC, abstractmethod
from enum import Enum

class Status(Enum):
    S = 1
    F = -1
    O = 0

class Action(ABC):

    @abstractmethod
    def status(self)->Status:
        pass

    @abstractmethod
    def run(self):
        pass
    
    def __and__(self,A2):
        return AND(self,A2)

    def __or__(self,A2):
        return OR(self,A2)
    
    def __invert__(self):
        return NOT(self)

    def and_(self,action):
        return AND(self, action)
    
    def or_(self, action):
        return OR(self, action)
    
    def not_(self):
        return NOT(self)


class AND(Action):
    def __init__(self, A1:Action, A2: Action):
        self.A1 = A1
        self.A2 = A2
    
    def status(self)-> Status:
        if self.A1.status() == Status.S:
            return self.A2.status()
        return self.A1.status()
    
    def run(self):
        if self.A1.status() == Status.O:
            self.A1.run()
        if self.A1.status() == Status.S:
            self.A2.run()


class OR(Action):
    def __init__(self, A1:Action, A2: Action):
        self.A1 = A1
        self.A2 = A2
    
    def status(self)-> Status:
        if self.A1.status() == Status.S or self.A2.status() == Status.S:
            return Status.S
        if self.A1.status() == Status.O or self.A2.status() == Status.O:
            return Status.O
        return Status.F
    
    def run(self):
        if self.A1.status() == Status.O:
            self.A1.run()
        if self.A1.status() == Status.F:
            self.A2.run()        


class NOT(Action):
    def __init__(self, A1:Action):
        self.A1 = A1
    
    def status(self)-> Status:
        if self.A1.status() == Status.S:
            return Status.F
        if self.A1.status() == Status.F:
            return Status.S
        return Status.O
    
    def run(self):
        self.A1.run()        

