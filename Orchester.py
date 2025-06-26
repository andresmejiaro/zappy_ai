import socket

from Agent import Agent
from ActionTree import Action, Status

class Orchester():

    def __init__(self, agent: Agent, plan: Action):
        self.partial_msg = b''
        self.agent = agent
        self.plan = plan
    
    def process_input(self, input):
        self.partial_msg += input
        s = self.partial_msg.find(b'\n')
        while s != -1:
            temp = self.partial_msg.split(b'\n',1)
            if len(temp) == 0:
                self.partial_msg = b''
                break
            self.agent.command(temp[0].decode("utf-8"))
            if len(temp) == 1:
                self.partial_msg = b''
                break
            else:
                self.partial_msg = temp[1]
            s = self.partial_msg.find(b'\n')


    def main_loop(self, args):
        #try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((args.h, args.p))
                while True:
                    if not args.random:
                        input = client.recv(16)
                        if not input:
                            break
                    else:
                        input = ""
                    self.process_input(input)
                    self.agent.food_update()
                    if self.agent.inventory["norriture"] <= 0:
                        print("Dude u ded")
                        break
                    if self.plan.status(self.agent) != Status.S and self.agent.starting >= 3:
                        self.plan.run(self.agent)
                    # elif self.agent.starting >= 3:
                    #     print("Lo Logre!")
                    #     break
                    message = self.agent.generate_message(args)
                    client.sendall((message + '\n').encode())
        #except ConnectionRefusedError:
        #    print("Server is down. Unable to connect.")
        #except Exception as e:
        #    print("An error occurred:", e)








