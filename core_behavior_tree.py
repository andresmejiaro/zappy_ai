
from abc import ABC, abstractmethod
from enum import Enum

class Status(Enum):
    S = 1
    F = -1
    O = 0
    

class BTNode(ABC):

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


class AND(BTNode):
    def __init__(self, A1:BTNode, A2: BTNode):
        self.A1 = A1
        self.A2 = A2
    
    
    def run(self,object):
        w = self.A1.run(object)
        if w == Status.S:
            return self.A2.run(object)
        else:
            return w

class OR(BTNode):
    def __init__(self, A1:BTNode, A2: BTNode):
        self.A1 = A1
        self.A2 = A2
    
    def run(self,object):
        w = self.A1.run(object)
        if w == Status.F:
            return self.A2.run(object)        
        return w

class NOT(BTNode):
    def __init__(self, A1:BTNode):
        self.A1 = A1

    def run(self, object):
        w =self.A1.run(object)
        if w == Status.F:
            return Status.S
        if w == Status.S:
            return Status.F
        return w 

class LOGIC(BTNode):
    def __init__(self, fun):
        self.fun = fun
 
    def run(self, object):
        if self.fun(object):
            return Status.S
        return Status.F
        
class GEN(BTNode):
    def __init__(self, generator, sticky = False):
        self.generator = generator
        self.plan = None
        self.sticky = sticky
        self.sticky_result = None
    def run(self, object):
        if self.plan is None:
            self.plan = self.generator(object)
        if self.sticky and self.sticky_result is not None:
            return self.sticky_result      
        w = self.plan.run(object)
        if w in [Status.S, Status.F]:
            if not self.sticky:
                self.plan = None
            else:
                self.sticky_result = w
        return w        

class MSG(BTNode):
    def __init__(self, message, nxt = "and"):
        self.message = message
        self.nxt = nxt

    def run(self, object):
        print(self.message)
        if self.nxt == "and":
            return Status.S
        if self.nxt == "or":
            return Status.F
 
class GATE(BTNode):
    """
    Boolean guard

    * It takes open and close conditions in the constructor
    * If the door is closed checks open condition to open it and allow flow via &
    * If the door is open checks closed condition to close the door if necessary

    If the door is open it returns Status.S else Status.F
    """
    def __init__(self, open_cond, close_cond):
        self._open = False
        self.open_cond = open_cond
        self.close_cond = close_cond

    def run(self, object):
        if not self._open and self.open_cond(object):
            self._open = True
            return Status.S
        if not self._open and not self.open_cond(object):
            return Status.F
        if self._open and self.close_cond(object):
            self._open = False
            return Status.F
        return Status.S
        
