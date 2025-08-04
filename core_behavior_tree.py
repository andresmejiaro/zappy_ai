
from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import Callable, Any

class Status(Enum):
    S = 1
    F = -1
    O = 0
    

class BTNode(ABC):
    def __init__(self,name: str |None = None):
        if name is None:
            self.name = f"node{id(self)}"
        else:
            self.name = name

    def __repr__(self):
        cls = self.__class__.__name__
        return f"{cls}(name = {self.name!r})"
 
    @abstractmethod
    def run(self, object):
        pass
    


class AND(BTNode):
    """
    Sequential memoryless
    """
    def __init__(self, actions: list[BTNode], name: str|None = None):
        super().__init__(name)
        self.actions = actions
    
    
    def run(self,object):
        for action in self.actions:
            w = action.run(object)
            if w != Status.S:
                return w
        return Status.S


class AND_P(BTNode):
    """
    Sequential with memory
    """
    def __init__(self, actions: list[BTNode], name: str|None = None):
        super().__init__(name)
        self.actions = actions
        self.action_n = 0
    
    
    def run(self,object):
        if self.action_n >= len(self.actions):
            return Status.S
        w = self.actions[self.action_n].run(object)
        if w != Status.S:
              return w
        else:
            self.action_n += 1
        return Status.O



class OR(BTNode):
    def __init__(self, actions: list[BTNode], name: str|None = None):
        super().__init__(name)
        self.actions = actions
    
    def run(self,object):
        for action in self.actions:
            w = action.run(object)
            if w in [Status.S, Status.O]:
                return w        
        return Status.F

class NOT(BTNode):
    def __init__(self, A1:BTNode, name: str|None = None):
        super().__init__(name)
        self.A1 = A1

    def run(self, object):
        w =self.A1.run(object)
        if w == Status.F:
            return Status.S
        if w == Status.S:
            return Status.F
        return w 

class LOGIC(BTNode):
    def __init__(self, fun: Callable[[Any], bool], name: str|None = None):
        super().__init__(name)
        self.fun = fun
 
    def run(self, object):
        if self.fun(object):
            return Status.S
        return Status.F
        
class GEN(BTNode):
    """
    Creates a dinamic plan. Refreshes upon Success or Failure.
    Uses a generator function a generator function takes an agent 
    and returns a BTNode object
    
    the return option makes this node return always the same value.
    The idea is to create loops

    LOGIC | GEN (ret = Status.F) is a while loop until condition is
    complete for example

    timeout forces to drop the plan to regenerate note timeout here 
    takes the agent internal time not machine time

    """
    def __init__(self, generator:Callable[[Any], BTNode], name: str|None = None, ret: Status|None = None, timeout:int = 400):
        super().__init__(name)
        self.generator = generator
        self.plan = None
        self.ret = ret
        self.timeout = timeout
        self.gen_stamp = None
    
    def run(self, object):
        if self.gen_stamp is not None and (object.turn - self.gen_stamp) > self.timeout:
            self.plan = None
        if self.plan is None:
            #try:
                self.plan = self.generator(object)
                self.gen_stamp = object.turn
            #except Exception as e:
            #    print(f"Generator Failed due to {e}")
            #    return Status.F     
        w = self.plan.run(object)
        if w in [Status.S, Status.F]:
            self.plan = None
        if self.ret is not None and w != Status.O:
            w = self.ret 
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
    def __init__(self, open_cond: Callable[[Any],bool], close_cond: Callable[[Any],bool], name: str|None = None):
        super().__init__(name)
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
        
##### Core interaction goes here does not justifies a file

class Interaction(BTNode):
    def __init__(self, command, resource = '', name: str|None = None):
        super().__init__(name)
        self.status_ = Status.O
        self.signature = []
        if resource == '':
            self.command = command
        else:
            self.command = command + ' ' + resource
        self.started = False


    def run(self,object):
        if not self.started:
            object.unsent_commands.append(self.command)
            signature = hash(random.random())
            self.signature = signature
            object.running_routine.append([self.command, signature])
            self.started = True
            return Status.O
        else:
            return self.check_status(object)

    
    def check_status(self, object):
        if self.started == False:
            return Status.O
        for x in object.running_routine:
            if x[0] == self.command and x[1] == self.signature:
                return Status.O
        for x in object.resolved_queue:
            if x[0] == self.command and x[1] == self.signature:
                if x[2] == "ko":
                    return Status.F
                elif x[2] == "ok":
                    return Status.S
        return Status.F