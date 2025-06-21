import random

random.seed(42)

DIRECTIONS = [[1,0],[0,-1],[-1,0],[0,1]]

DENSITY = {"norriture": 0.05, "linemate": 0.3, "deraumere": 0.15, "sibur": 0.1, "mendiane":0.1, "phiras": 0.08, "thystame": 0.05}

class Game():

    def __init__(self):
        self.tick = 0
        self.t = 6
        self.starting = 0
        self.x = 10
        self.y = 10
        self.pos = [5,5]
        self.message_queue = ["BIENVENUE", "5", f"{self.x} {self.y}"]
        self.view = 0
        self.objects = [[[] for y in range(self.y)] for x in range(self.x)]
        self.initial_fill()


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
            return f"{self.x} {self.y}"
    
    def soir():
        pass


    def command(self, command):
        if len(command) == 0:
            return
        if command == "soir":
            return self.soir()
    
    def generate_message(self)->str:
        if len(self.message_queue) > 0:
            return self.message_queue.pop(0)
        else:
            return ""
