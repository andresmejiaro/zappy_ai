import time
from objects import commands_single, commands_object, commands_text, objects
import random
import numpy as np
from ActionTree import Status

#Rotating to the left
DIRECTIONS = list(map(np.array,[[1,0],[0,-1],[-1,0],[0,1]]))

def generate_random_message():
    if not hasattr(generate_random_message, "weights"):
        generate_random_message.weights = [len(commands_single), len(commands_object), len(commands_text)]
        generate_random_message.tot_weight = sum(generate_random_message.weights)
    random_n = random.randint(0,generate_random_message.tot_weight - 1)
    if random_n < generate_random_message.weights[0]:
        return commands_single[random_n]
    random_n -= generate_random_message.weights[0]
    if random_n < generate_random_message.weights[1]:
        random_n2 = random.randint(0, len(objects) - 1)
        return commands_object[random_n] + ' ' + objects[random_n2]
    random_n -= generate_random_message.weights[1]
    if random_n < generate_random_message.weights[2]:
        random_n2 = random.randint(0, 9999)
        return commands_text[random_n] + ' ' + str(hash(random_n2))


class Agent():
    
    def __init__(self, args):
        self.running_routine = [] ## Messages Sent not answered
        self.unsent_commands = [] ## Messages to be sent
        self.resolved_queue = [] ## Messages Resolved includes status
        self.starting = 0
        self.team = args.n
        self.nb_client = 0
        self.size = np.array([10,10])
        self.pos = np.array([0,0])
        self.facing = 0
        self.objects = None
        self.turn = 0
        self.inventory ={"nourriture": 10, "linemate": 0, "deraumere": 0, "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0}
        

    def starting_command(self, command: str):
        if self.starting == 0:
            if command == "BIENVENUE":
                self.starting += 1
                self.unsent_commands.append(f"{self.team}")
                return
            else:
                print(f"No se recibio el mensaje de bienvenida al iniciar {command}")
                self.starting = 4
        if self.starting == 1:
            if command.isdigit():
                self.nb_client = int(command)
                self.starting += 1
                self.starting_time = time.time()
                return
            else:
                self.starting = 4
                print(f"No se identifico el numero de clientes de manera correcta {command}")
        if self.starting == 2:
            coords = command.split(' ')
            if len(coords) != 2:
                self.starting = 4
                print(f"No son dos coordenadas!{coords}")
            for x in coords:
                if not x.isdigit():
                    self.starting = 4
                    print(f"esto deberian ser numeros {x}")
            if self.starting != 4:
                self.size = np.array(list(map(int,coords)))
                self.objects = [[[] for y in range(self.size[1])] for x in range(self.size[0])]
                self.starting += 1

    def status_check(self):
        pass
        
    def avance_processer(self, command, x= None):
        print(f"Old position: {self.pos}")
        self.pos += DIRECTIONS[self.facing]
        self.pos[0] = (self.pos[0] + self.size[0]) % self.size[0]
        self.pos[1] = (self.pos[1] + self.size[1]) % self.size[1]
        print(f"New position: {self.pos}")
        self.turn += 7
        self.resolve_from_running_routine("avance")
    
    def droite_processer(self,command,x = None):
        print(f"Old facing: {DIRECTIONS[self.facing]}")
        self.facing = (self.facing + 3) % 4
        print(f"New facing: {DIRECTIONS[self.facing]}")
        self.turn += 7
        self.resolve_from_running_routine("droite")
        
    
    def gauche_processer(self,command,x = None):
        print(f"Old facing: {DIRECTIONS[self.facing]}")
        self.facing = (self.facing + 1) % 4
        print(f"New facing: {DIRECTIONS[self.facing]}")
        self.turn += 7
        self.resolve_from_running_routine("gauche")
    
    def prend_processer(self,command,x,status = "ok"):
        if status == "ok":
            things = x.split(" ")
            print(f"Picking up {things[1]}")
            self.inventory[things[1]] += 1
        self.turn += 7
        self.resolve_from_running_routine(x, status)

    def pose_processer(self,command,x, status = "ok"):
        if status == "ok":
            things = x.split()
            print(f"Dropping {things[1]}")
            self.inventory[things[1]] -= 1
        self.turn += 7  
        self.resolve_from_running_routine(x, status)

    
    def expulse_processer(self,command):
        pass
    
    def broadcast_processer(self,command):
        pass
    
    def fork_processer(self,command):
        pass

    def ok_processer(self, command):
        okaiable_commands = {"avance": self.avance_processer,
                             "droite": self.droite_processer,
                             "gauche": self.gauche_processer,
                              "prend": self.prend_processer,
                              "pose": self.pose_processer,
                              "expulse": self.expulse_processer,
                              "broadcast": self.broadcast_processer,
                               "fork": self.fork_processer}    
        for i in range(len(self.running_routine)):
            for j in okaiable_commands.keys():
                if self.running_routine[i][0].startswith(j):
                    x = self.running_routine[i]
                    okaiable_commands[j](command, x[0])
                    return
            
    def ko_processer(self, command):
        okaiable_commands = {"prend": self.prend_processer,
                              "pose": self.pose_processer,
                              "expulse": self.expulse_processer}    
        for i in range(len(self.running_routine)):
            for j in okaiable_commands.keys():
                if self.running_routine[i][0].startswith(j):
                    x = self.running_routine[i]
                    okaiable_commands[j](command, x[0])
                    return
        print(f"ko for unknown command most likely {self.running_routine[0][0]}")
        self.resolve_from_running_routine(self.running_routine[0][0], "ko")


    def elevation_en_cours_processer(self,command):
        pass

    def mort_processer(self,command):
        pass
    
    def resolve_from_running_routine(self, command, status = "ok"):
       for i in range(len(self.running_routine)):
           if self.running_routine[i][0] == command:
               y = self.running_routine.pop(i)
               y.append(status)
               self.resolved_queue.append(y)
               break 
    
    def soir_processer(self, command:str):
        left_dir = DIRECTIONS[(self.facing + 1) % 4]
        front_dir = DIRECTIONS[(self.facing) % 4]
        contents = command.removeprefix("{").removesuffix("}").split(",")
        w = 0
        for x in range(9999):
            if w >= len(contents):
                break
            for y in range(2*x + 1):
                coord = self.pos + x*front_dir +(y - x) * (-left_dir) 
                coord = coord.tolist()
                self.objects[coord[0]][coord[1]].append(contents[w].split())
                w += 1
        print(f"soir {command}")
        self.resolve_from_running_routine("soir")
        self.turn += 7

    def inventaire_processer(self, command):
        pass

    def bracket_processer(self,command):
        for i in range(len(self.running_routine)):
            if self.running_routine[i][0] in ["soir", "inventaire"]:
                break
        x = self.running_routine[i  ]
        if x[0] == "soir":
            self.soir_processer(command)
        if x[0] == "inventaire":
            self.inventaire_processer(command)


    def niveau_actuel_processer(self,command):
        pass

    def message_processer(self,command):
        if self.tick is None:
            self.tick = time.time() - self.starting_time
        pass

    def processer_select(self,command: str):
        static_responses = {"ok":self.ok_processer,
                            "ko": self.ko_processer,
                            "elevation en cours":self.elevation_en_cours_processer,
                            "mort":self.mort_processer}
        if command in static_responses:
            return static_responses[command] 
        if command[0] == '{':
            return self.bracket_processer
        if command.isnumeric():
            return self.numeric_processer
        if command.startswith("niveau actuel"):
            return self.niveau_actuel_processer
        if command.startswith("message"):
            return self.message_processer
        print(f"Unknown command type {command} returning empty hander. Command will be ignored")
        return lambda x: None
    
    ### process command from server
    def command(self, command):
        if len(command) == 0:
            return
        if self.starting < 3:
            self.starting_command(command)
            return
        processer = self.processer_select(command)
        processer(command)


    def generate_message(self, args)->str:
        if args.random:
            time.sleep(1)
            return generate_random_message()
        if len(self.unsent_commands) > 0 and len(self.running_routine) < 10:
            y = self.unsent_commands.pop(0)
            return y
        else:
            return ""


    # def update_Agent(self,msg: str):
    #     func = msg.split(maxsplit=2)
    #     if func[0] in self.updater.keys():
    #         self.updater[func[0]](func[1])
    #     else:
    #         print(f"Command {func[0]} in {msg} not found skipping")

    # updater = {}
    #updater = {"avance", "droite", "gauche", "voir", "inventaire", "expulse", "incantation", "fork", "connect_nbr","prend", "pose","broadcast"}