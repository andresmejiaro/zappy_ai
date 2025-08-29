
from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import Callable, Any
import time
import json


class Status(Enum):
    S = 1
    F = -1
    O = 0


class BTNode(ABC):
    def __init__(self, name: str | None = None):
        if name is None:
            self.name = f"node{id(self)}"
        else:
            self.name = name

    def __repr__(self):
        cls = self.__class__.__name__
        return f"{cls}(name = {self.name!r})"

    @abstractmethod
    def run(self, object, log_seq):
        pass


class AND(BTNode):
    """
    Sequential memoryless
    """

    def __init__(self, actions: list[BTNode], name: str | None = None):
        super().__init__(name)
        self.actions = actions
        self._last_return = None
        self._key_node = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        for action in self.actions:
            self._key_node = action
            w = action.run(object, log_seq)
            if w != Status.S:
                self._last_return = w
                return w
        self._last_return = Status.S
        return Status.S


class AND_P(BTNode):
    """
    Sequential with memory
    """

    def __init__(self, actions: list[BTNode], name: str | None = None):
        super().__init__(name)
        self.actions = actions
        self.action_n = 0
        self._last_return = None
        self._key_node = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        if self.action_n >= len(self.actions):
            self._key_node = "done"
            self._last_return = Status.S
            return Status.S
        w = self.actions[self.action_n].run(object, log_seq)
        self._key_node = self.actions[self.action_n]
        if w != Status.S:
            self._last_return = w
            return w
        else:
            self.action_n += 1
        self._last_return = Status.O
        return Status.O


class OR(BTNode):
    def __init__(self, actions: list[BTNode], name: str | None = None):
        super().__init__(name)
        self.actions = actions
        self._last_return = None
        self._key_node = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        for action in self.actions:
            w = action.run(object, log_seq)
            if w in [Status.S, Status.O]:
                self._key_node = action
                self._last_return = w
                return w
        self._key_node = None
        self._last_return = Status.F
        return Status.F


class NOT(BTNode):
    def __init__(self, A1: BTNode, name: str | None = None):
        super().__init__(name)
        self.A1 = A1
        self._last_return = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        w = self.A1.run(object)
        if w == Status.F:
            self._last_return = Status.S
            return Status.S
        if w == Status.S:
            self._last_return = Status.F
            return Status.F
        self._last_return = w
        return w


class ALWAYS_F(BTNode):
    def __init__(self, A1: BTNode, name: str | None = None):
        super().__init__(name)
        self.A1 = A1
        self._last_return = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        w = self.A1.run(object, log_seq)
        self._last_return = Status.F
        if w == Status.F:
            return Status.F
        if w == Status.S:
            return Status.F
        self._last_return = w
        return w


class O_ON_F(BTNode):
    def __init__(self, A1: BTNode, name: str | None = None):
        super().__init__(name)
        self.A1 = A1
        self._last_return = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        w = self.A1.run(object, log_seq)
        self._last_return = Status.O
        if w == Status.F:
            return Status.O
        if w == Status.O:
            return Status.O
        self._last_return = w
        return w


class ALWAYS_S(BTNode):
    def __init__(self, A1: BTNode, name: str | None = None):
        super().__init__(name)
        self.A1 = A1
        self._last_return = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        w = self.A1.run(object, log_seq)
        self._last_return = Status.S
        if w == Status.F:
            return Status.S
        if w == Status.S:
            return Status.S
        self._last_return = w
        return w


class LOGIC(BTNode):
    def __init__(self, fun: Callable[[Any], bool], name: str | None = None):
        super().__init__(name)
        self.fun = fun
        self._last_return = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        if self.fun(object):
            self._last_return = Status.S
            return Status.S
        self._last_return = Status.F
        return Status.F


class GEN(BTNode):
    """
    Creates a dinamic plan.
    Uses a generator function a generator function takes an agent
    and returns a BTNode object

    """

    def __init__(self,
                 generator: Callable[[Any],
                                     BTNode],
                 name: str | None = None,
                 reset_on_failure=True,
                 reset_on_success=True,
                 timeout=1000000,
                 timeout_callback=None):
        super().__init__(name)
        self.generator = generator
        self.plan = None
        self.reset_on_success = reset_on_success
        self.reset_on_failure = reset_on_failure
        self._last_return = None
        self.timeout = timeout
        self.last_timeout = 0
        self.last_log = ""
        self.init_count = 0
        self.timeout_callback = timeout_callback

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name + f"inv:{object.inventory}"]
        if self.plan is None:
            self.plan = self.generator(object)
            self.init_count += 1
        w = self.plan.run(object, log_seq)
        reset_S = (w == Status.S and self.reset_on_success)
        reset_F = (w == Status.F and self.reset_on_failure)
        if reset_S or reset_F:
            self.plan = None
            if self.timeout_callback is not None:
                self.timeout_callback(object)
        if self.timeout > 0:
            if object.turn - self.last_timeout > self.timeout:
                self.plan = None
                self.last_timeout = object.turn
        self._last_return = w
        return w


class GATE(BTNode):
    """
    Boolean guard

    * It takes open and close conditions in the constructor
    * If the door is closed checks open condition to open it and allow flow
    * If the door is open checks closed condition to close the door

    If the door is open it returns Status.S else Status.F
    """

    def __init__(self, open_cond: Callable[[Any], bool], close_cond: Callable[[
                 Any], bool], name: str | None = None):
        super().__init__(name)
        self._open = False
        self.open_cond = open_cond
        self.close_cond = close_cond
        self._last_return = None

    def run(self, object, log_seq=[]):
        log_seq = log_seq.copy() + [self.name]
        if not self._open and self.open_cond(object):
            self._open = True
            self._last_return = Status.S
            return Status.S
        if not self._open and not self.open_cond(object):
            self._last_return = Status.F
            return Status.F
        if self._open and self.close_cond(object):
            self._open = False
            self._last_return = Status.F
            return Status.F
        self._last_return = Status.S
        return Status.S


class Interaction(BTNode):
    def __init__(self, command, resource='', name: str | None = None):
        if name is None:
            if len(resource) > 0:
                name = command + ' ' + resource
            else:
                name = command
        super().__init__(name)
        self.status_ = Status.O
        self.signature = []
        if resource == '':
            self.command = command
        else:
            self.command = command + ' ' + resource
        self.started = False
        self._last_return = None

    def run(self, object, log_seq):
        log_seq = log_seq.copy() + [self.name]
        if object.marco_polo_target is None:
            mpt = None
        else:
            mpt = object.marco_polo_target.tolist()
        if not self.started:
            object.unsent_commands.append(self.command)
            signature = hash(random.random())
            self.signature = signature
            object.running_routine.append([self.command, signature])
            self.started = True
            self._last_return = Status.O
            # with open(f"logs/highlight_{object.name}.jsonl", "a") as f:
            #     f.write(json.dumps({"turn": object.turn,
            #                         "unix_time": time.time(),
            #                         "name": object.name,
            #                         "lvl": object.level,
            #                         "path": log_seq,
            #                         "s": "O",
            #                         "inventory": object.inventory,
            #                         "pos": object.pos.tolist(),
            #                         "totem": mpt,
            #                         "action": self.command}) + "\n")
            #     f.flush()
            return Status.O
        else:
            self._last_return = self.check_status(object)
            # with open(f"logs/highlight_{object.name}.jsonl", "a") as f:
            #     f.write(json.dumps({"turn": object.turn,
            #                         "unix_time": time.time(),
            #                         "name": object.name,
            #                         "lvl": object.level,
            #                         "path": log_seq,
            #                         "s": self._last_return.name,
            #                         "inventory": object.inventory,
            #                         "pos": object.pos.tolist(),
            #                         "totem": mpt,
            #                         "action": self.command}) + "\n")
            #     f.flush()
            return self._last_return

    def check_status(self, object):
        if not self.started:
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
