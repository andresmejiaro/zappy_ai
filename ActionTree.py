
from abc import ABC, abstractmethod
from enum import Enum

class Status(Enum):
    S = 1
    F = -1
    O = 0
    

class Action(ABC):

    @abstractmethod
    def status(self, object)->Status:
        pass

    @abstractmethod
    def run(self, object):
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
    
    def status(self,object)-> Status:
        if self.A1.status(object) == Status.S:
            return self.A2.status(object)
        return self.A1.status(object)
    
    def run(self,object):
        if self.A1.status(object) == Status.O:
            self.A1.run(object)
        if self.A1.status(object) == Status.S:
            self.A2.run(object)


class OR(Action):
    def __init__(self, A1:Action, A2: Action):
        self.A1 = A1
        self.A2 = A2
    
    def status(self)-> Status:
        if self.A1.status(object) == Status.S or self.A2.status() == Status.S:
            return Status.S
        if self.A1.status(object) == Status.O or self.A2.status() == Status.O:
            return Status.O
        return Status.F
    
    def run(self):
        if self.A1.status(object) == Status.O:
            self.A1.run(object)
        if self.A1.status(object) == Status.F:
            self.A2.run(object)        


class NOT(Action):
    def __init__(self, A1:Action):
        self.A1 = A1
    
    def status(self)-> Status:
        if self.A1.status(object) == Status.S:
            return Status.F
        if self.A1.status(object) == Status.F:
            return Status.S
        return Status.O
    
    def run(self):
        self.A1.run(object)        

