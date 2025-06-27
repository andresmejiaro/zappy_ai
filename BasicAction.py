from ActionTree import Action, Status
import random

class Basic(Action):
    def __init__(self, command, resource = ''):
        self.status_ = Status.O
        self.signaure = None
        if resource == '':
            self.command = command
        else:
            self.command = command + ' ' + resource
        self.started = False

    def run(self,object):
        if not self.started:
            self.status_ = Status.O
            object.unsent_commands.append(self.command)
            self.signaure = hash(random.random())
            object.running_routine.append([self.command, self.signaure])
            self.started = True
            return self.status_
        else:
            return self.check_status(object)

    
    def check_status(self, object):
        if self.started == False:
            return Status.O
        for x in object.running_routine:
            if x == [self.command,self.signaure]:
                return Status.O
        for x in object.resolved_queue:
            if x[0] == self.command and x[1] == self.signaure:
                if x[2] == "ok":
                    return Status.S
                return Status.F
        return Status.F
   
    # def status(self, object):
    #     if self.status_ == Status.O:
    #         self.status_ = self.check_status(object)
    #     return self.status_
   

