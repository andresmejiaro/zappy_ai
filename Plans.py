from ActionTree import Action, Status
import random

class Basic(Action):
    def __init__(self, command):
        self.status_ = Status.O
        self.signaure = None
        self.command = command
        self.started = False

    def run(self,object):
        if not self.started:
            self.status_ = Status.O
            object.unsent_commands.append(self.command)
            self.signaure = hash(random.random())
            object.running_routine.append([self.command, self.signaure])
            self.started = True

    
    def check_status(self, object):
        if self.started == False:
            return Status.O
        for x in object.running_routine:
            if x == [self.command,self.signaure]:
                return Status.O
        for x in object.resolved_queue[::-1]:
            if x[0] == self.command and x[1] == self.signaure:
                if x[2] == "ok":
                    return Status.S
                return Status.F
        print("Se perdio el soir de alguna manera")
        return Status.F
   
    def status(self, object):
        if self.status_ == Status.O:
            self.status_ = self.check_status(object)
        return self.status_
    

