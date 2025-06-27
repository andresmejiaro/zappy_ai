
from abc import ABC, abstractmethod
from enum import Enum

class Status(Enum):
    S = 1
    F = -1
    O = 0
    

class Action(ABC):

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
    
    
    def run(self,object):
        w = self.A1.run(object)
        if w == Status.S:
            return self.A2.run(object)
        else:
            return w


class OR(Action):
    def __init__(self, A1:Action, A2: Action):
        self.A1 = A1
        self.A2 = A2
    
    def run(self,object):
        w = self.A1.run(object)
        if w == Status.F:
            return self.A2.run(object)        
        return w


class NOT(Action):
    def __init__(self, A1:Action):
        self.A1 = A1

    def run(self, object):
        w =self.A1.run(object)
        if w == Status.F:
            return Status.S
        if w == Status.S:
            return Status.F
        return w 


class LOGIC(Action):
    def __init__(self, fun):
        self.fun = fun
 
    def run(self, object):
        if self.fun(object):
            return Status.S
        return Status.F
        

class GEN(Action):
    def __init__(self, generator):
        self.generator = generator
        self.plan = None

    def run(self, object):
        if self.plan is None:
            self.plan = self.generator(object)
        w = self.plan.run(object)
        if w in [Status.S, Status.F]:
            self.plan = None
        return w        


# class GEN(Action):
#     def __init__(self, generator):
#         self.generator = generator
#         self.plan = None

#     def status(self, object):
#         if self.plan is None:
#             return Status.O
#         w = self.plan.status(object)
#         if w in [Status.F, Status.S]:
#             self.plan = None
#         return w

#     def run(self, object):
#         if self.plan is None:
#             self.plan = self.generator(object)
#         self.plan.run(object)        
