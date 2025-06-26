import random
import numpy as np
import time

random.seed(42)

#Rotating to the left
DIRECTIONS = list(map(np.array,[[1,0],[0,-1],[-1,0],[0,1]]))

DENSITY = {"norriture": 0.05, "linemate": 0.3, "deraumere": 0.15, "sibur": 0.1, "mendiane":0.1, "phiras": 0.08, "thystame": 0.05}

class Game():

    def __init__(self):
        self.tick = 0
        self.t = 6
        self.starting = 0
        self.x = 10
        self.y = 10
        self.pos = np.array([5,5])
        self.message_queue = ["BIENVENUE", "5", f"{self.x} {self.y}"]
        self.facing = 0
        self.objects = [[[] for y in range(self.y)] for x in range(self.x)]
        self.initial_fill()
        self.level = 1
        self.inventory ={"nourriture": 10, "linemate": 0, "deraumere": 0, "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0}
        self.team = None

    def initial_fill(self):
        for x in range(self.x):
            for y in range(self.y):
                for item in DENSITY.keys():
                    if random.random() < DENSITY[item]:
                        self.objects[x][y].append(item)
        print(self.objects)


    def starting_command(self, command: str):
        if self.starting == 0:
            self.starting += 1
            return "5"
        
        if self.starting == 1:
            self.starting =     3
            return f"{self.x} {self.y}"
        
    
    def soir(self):
        objects = []
        left_dir = DIRECTIONS[(self.facing + 1) % 4]
        front_dir = DIRECTIONS[(self.facing) % 4]
        for x in range(self.level + 1):
            for y in range(2*x + 1):
                coord = self.pos + x*front_dir +(y - x) * (-left_dir) 
                coord = coord.tolist()
                objects.append(self.objects[coord[0] % self.x][coord[1] %self.y])
        toout =list(map(lambda x: " ".join(x), objects))
        toout = "{" + ",".join(toout) + "}"
        print(toout)
        return(toout)

    def avance(self):
        print(f"Old position: {self.pos}")
        self.pos += DIRECTIONS[self.facing]
        self.pos[0] = (self.pos[0] + self.x) % self.x
        self.pos[1] = (self.pos[1] + self.y) % self.y
        print(f"New position: {self.pos}")
        return "ok"

    def droite(self):
        print(f"Old facing: {DIRECTIONS[self.facing]}")
        self.facing = (self.facing + 3) % 4
        print(f"New facing: {DIRECTIONS[self.facing]}")
        return "ok"
        
    def gauche(self):
        print(f"Old facing: {DIRECTIONS[self.facing]}")
        self.facing = (self.facing + 1) % 4
        print(f"New facing: {DIRECTIONS[self.facing]}")
        return "ok"
    
    
    def prend(self,command):
        things = command.split()
        if things[1] in self.objects[self.pos[0]][self.pos[1]]:
            print(f"Picking up {things[1]}")
            self.inventory[things[1]] += 1
            self.objects[self.pos[0]][self.pos[1]].remove(things[1])
            return "ok"
        else:
            return "ko"
        
    def pose(self,command):
        things = command.split()
        if self.inventory[things[1]] > 0:
            print(f"Dropping {things[1]}")
            self.inventory[things[1]] -= 1
            self.objects[self.pos[0]][self.pos[1]].append(things[1])
            return "ok"
        else:
            return "ko"

    def respond(self,message):
        self.message_queue.append(message)

    def command(self, command):
        if len(command) == 0:
            return
        if command == "soir":
            self.respond(self.soir())
        elif command == "avance":
            self.respond(self.avance())
        elif command == "droite":
            self.respond(self.droite())
        elif command == "gauche":
            self.respond(self.gauche())
        elif command.split()[0] == "prend":
            self.respond(self.prend(command))
        elif command.split()[0] == "pose":
            self.respond(self.pose(command))
        elif self.team is None:
            self.team = command
        else:
            self.respond("ko")
        
    
    def generate_message(self)->str:
        if len(self.message_queue) > 0:
            return self.message_queue.pop(0)
        else: 
            return ""
