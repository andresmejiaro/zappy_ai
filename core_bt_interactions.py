from core_behavior_tree import BTNode, Status
import random

class Interaction(BTNode):
    def __init__(self, command, resource = '', replica = 1):
        self.status_ = Status.O
        self.signaure = []
        if resource == '':
            self.command = command
        else:
            self.command = command + ' ' + resource
        self.started = False
        self.replica = replica

    def run(self,object):
        if not self.started:
            self.status_ = Status.O
            for i in range(self.replica):
                object.unsent_commands.append(self.command)
                signaure = hash(random.random())
                self.signaure.append(signaure)
                object.running_routine.append([self.command, signaure])
            self.started = True
            return self.status_
        else:
            return self.check_status(object)

    
    def check_status(self, object):
        if self.started == False:
            return Status.O
        for x in object.running_routine:
            if x[0] == self.command and x[1] in self.signaure:
                return Status.O
        for x in object.resolved_queue:
            if x[0] == self.command and x[1] in self.signaure:
                if x[2] == "ko":
                    return Status.F
                elif x[2] == "ok":
                    self.signaure.remove(x[1])
        if len(self.signaure) == 0:
            return Status.S
        return Status.F
   
   

