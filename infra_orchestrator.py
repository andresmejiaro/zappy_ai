import socket
import select

from domain_agent import Agent
from core_behavior_tree import BTNode, Status
from datetime import datetime
import json
import random


class Orchester():

    def __init__(self, agent: Agent, plan: BTNode):
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
                client.setblocking(False)
                old_log = ""
                while True:
                    readable, _, _ = select.select([client],[],[],0)
                    if readable:
                        input = client.recv(1024)
                        if not input:
                            break
                    else:
                        input = b""
                    self.process_input(input)
                    self.agent.food_update()
                    if  self.agent.starting >= 3:
                        if len(self.agent.running_routine) == 0:
                            w = self.plan.run(self.agent)
                                # log = json.dumps(self.plan.log())
                                # log_path = f"logs/log_{self.agent.name}.jsonl"
                                # with open(log_path, "a") as f:
                                #     f.write(log + "\n")
                                
                                                #if w != Status.O:
                        #    print("termine")
                    message = self.agent.generate_message(args)
                    if len(message) > 0:
                        print(f"sending message: {message}")
                        import numpy as np
                        if message.startswith("prend") and np.array_equal(self.agent.pos, self.agent.marco_polo_target) and max(self.agent.ppl_inventories.keys()) != self.agent.name:
                            raise Exception("WTF")
                        client.sendall((message + '\n').encode())
        #except ConnectionRefusedError:
        #    print("Server is down. Unable to connect.")
        #except Exception as e:
        #    print("An error occurred:", e)




    



