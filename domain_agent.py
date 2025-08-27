import time
import random
import numpy as np
import json
import math
from functools import reduce
import os



random.seed(42)


#Rotating to the left
DIRECTIONS = list(map(np.array,[[1,0],[0,-1],[-1,0],[0,1]]))
SOUND_DIRECTIONS = list(map(np.array,[[1,0],[1,-1],[0,-1],[-1,1],[-1,0],[-1,1],[0,1],[1,1]]))


class Agent():
    
    def __init__(self, args):
        self.running_routine = [] ## Messages Sent not answered
        self.unsent_commands = [] ## Messages to be sent
        self.resolved_queue = [] ## Messages Resolved includes status
        self.starting = 0 # just started the client for handshake
        self.team = args.n # team
        self.size = np.array([10,10]) #size of the map
        self.pos = np.array([0,0]) #actual position wrt spawning point
        self.facing = 0 #direction facing wrt spawning point
        self.turn = 0 # internal control of time
        self.inventory ={"nourriture": 10, "linemate": 0, "deraumere": 0, "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0} # starting inventory updates whenever inventory is seen
        self.level = 1 #level
        self.objects_countdown = None #timeouts of seen parts of the map, forgets
        self.last_turn = -1 #for control of timeouts last seen turn
        self.name = os.getpid() #give yourself a name
        self.ppl_timeouts = {} #store<function level_up_fail_conditions.<locals>.<lambda> at 0x79a8eb670720> when last ppl
        self.ppl_lv = {} #agents 
        self.ppl_inventories = {}
        self.last_called = []
        self.free_egg = True
        self.queen_reset()


    def queen_reset(self):
        self.sound_direction = None
        self.marco_polo_target = None
        self.marco_polo_confirm = 0
        self.needs = {}
        self.level_up = False
        self.level_up_count = 0
        self.last_fork = self.turn
        self.fork = False   
        self.queen = None
        self.level_up_cooldown = None
        self.queen_food = 10

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
                if self.nb_client > 0:
                    self.hold = True
                self.starting += 1
                self.starting_time = time.time()
                return
            else:
                self.starting = 4
                print(f"No se identifico el numero de clientes de manera correcta {command}")
        if self.starting == 2:
            coords = command.split(' ')
            if len(command) == 1:
                return
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
                self.objects_countdown = np.zeros(self.size) 
                self.starting += 1

    def objects_cooldown(self): 
        if self.objects_countdown is not None:
            needs = {
                "nourriture": 120,      # 1 per 120 ticks
                "linemate": 17143,      # 60000 / 3.5
                "deraumere": 31304,     # 60000 / 1.9167
                "sibur": 23226,         # 60000 / 2.5833
                "phiras": 34286,        # 60000 / 1.75
                "mendiane": 55385,      # 60000 / 1.0833
                "thystame": 360000      # 60000 / 0.1667
            } ## Based on subject 120 and evaluation sheet get to level 8 in 10 minutes al speed 100
            substances_chances = {"nourriture": 0.5, "linemate": 0.3, "deraumere": 0.15, "sibur": 0.1, "mendiane": 0.1, "phiras": 0.08, "thystame": 0.05}
            for key, value in substances_chances.items():
                nplayers = max(1, len(self.ppl_timeouts))
                nobj = value*self.size[0]*self.size[1]
                if nplayers < nobj:
                    breaks = -(self.objects_countdown - self.turn) > 0.25*needs[key]*np.log(0.5)/np.log(1-nplayers/nobj) ## assuming independance of picking up for each player random 0.25 for moving this from the edge case to the ez case
                else:
                    breaks = -(self.objects_countdown - self.turn) > 300000 # big value
                for x in range(self.size[0]):
                    for y in range(self.size[1]):
                        if breaks[x,y]:
                            self.objects[x][y] = [w for w in self.objects[x][y] if w != key]

    def ppl_cooldown(self):
        diff = {key:value  - self.turn for key, value in self.ppl_timeouts.items() if self.turn - value  > 600}
        if len(diff) > 0:
            for key in diff.keys():
                self.ppl_timeouts.pop(key, None)
                self.ppl_lv.pop(key,None)
        


    def update_level_inventory(self):
        self.level_inventory = {}
        for thing in self.inventory.keys():
            self.level_inventory[thing] = 0
            for person, level in self.ppl_lv.items():
                if level != self.level:
                    continue
                if person in self.ppl_inventories:
                    self.level_inventory[thing] += self.ppl_inventories[person].get(thing,0) 

    
    def food_update(self):
        #update 
        time_diff = self.turn - self.last_turn
        self.inventory["nourriture"] -= 1.2*time_diff/(126)
        if time_diff > 0:
            print(f"food: {self.inventory["nourriture"]}")
            self.update_tree = True
        self.last_turn = self.turn
        if self.level_up_cooldown is not None and self.turn - self.level_up_cooldown > 600:
            self.level_up_cooldown = None
        self.objects_cooldown()
        self.ppl_cooldown()


    def avance_processer(self, command, x= None):
        print(f"Old position: {self.pos}")
        self.pos += DIRECTIONS[self.facing]
        self.pos[0] = (self.pos[0] + self.size[0]) % self.size[0]
        self.pos[1] = (self.pos[1] + self.size[1]) % self.size[1]
        print(f"New position: {self.pos}")
        self.turn += 7
        self.resolve_from_running_routine("avance")
    
    def droite_processer(self,command,x = None):
        #print(f"Old facing: {DIRECTIONS[self.facing]}")
        self.facing = (self.facing + 3) % 4
        #print(f"New facing: {DIRECTIONS[self.facing]}")
        self.turn += 7
        self.resolve_from_running_routine("droite")
        
    
    def gauche_processer(self,command,x = None):
        #print(f"Old facing: {DIRECTIONS[self.facing]}")
        self.facing = (self.facing + 1) % 4
        #print(f"New facing: {DIRECTIONS[self.facing]}")
        self.turn += 7
        self.resolve_from_running_routine("gauche")
    
    def prend_processer(self,command,x,status = "ok"):
        things = x.split(" ")
        if status == "ok":
            print(f"Picking up {things[1]}")
            self.inventory[things[1]] += 1
            if things[1] in self.objects[self.pos[0]][self.pos[1]]:
                self.objects[self.pos[0]][self.pos[1]].remove(things[1])
        elif status == "ko":
            while things[1] in self.objects[self.pos[0]][self.pos[1]]:
                self.objects[self.pos[0]][self.pos[1]].remove(things[1])
        self.turn += 7
        self.resolve_from_running_routine(x, status)

    def pose_processer(self,command,x, status = "ok"):
        if status == "ok":
            things = x.split()
            print(f"Dropping {things[1]}")
            self.inventory[things[1]] -= 1
        self.turn += 7  
        self.resolve_from_running_routine(x, status)

    
    def expulse_processer(self,command, x = None):
        pass
    
    def broadcast_processer(self,command, x = None):
        self.turn += 7
        self.resolve_from_running_routine(x)
  
    def fork_processer(self,command,x):
        self.fork = False
        self.free_egg = False
        self.turn += 42
        self.resolve_from_running_routine(x)

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
                              "expulse": self.expulse_processer,
                              "incantation": self.incantation_ko}    
        for i in range(len(self.running_routine)):
            for j in okaiable_commands.keys():
                if self.running_routine[i][0].startswith(j):
                    x = self.running_routine[i]
                    okaiable_commands[j](command, x[0],"ko")
                    return
        print(f"ko for unknown command most likely {self.running_routine[0][0]}")
        self.resolve_from_running_routine(self.running_routine[0][0], "ko")

    def incantation_ko(self, command,x,status = "ko"):
        self.turn += 300
        if self.level_up_count < 5:
            self.level_up_count += 1
        else:
            self.level_up_count = 0
            self.level_up = False
            self.level_up_cooldown =  self.turn
        self.resolve_from_running_routine("incantation","ko")
        
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
    
    def voir_processer(self, command:str):
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
                self.objects[coord[0] % self.size[0]][coord[1] % self.size[1]]= contents[w].split()
                self.objects_countdown[coord[0] % self.size[0],coord[1] % self.size[1]] = self.turn
                w += 1
        print(f"voir {command}")
        self.resolve_from_running_routine("voir")
        self.turn += 7

    def inventaire_processer(self, command):
        contents = command.removeprefix("{").removesuffix("}").split(",")
        self.inventory = {}
        for content in contents:
            #str.split()
            a = content.split()
            self.inventory[a[0]] = int(a[1])
        self.turn += 1
        self.resolve_from_running_routine("inventaire")
        return

    def bracket_processer(self,command):
        for i in range(len(self.running_routine)):
            if self.running_routine[i][0] in ["voir", "inventaire"]:
                break
        x = self.running_routine[i  ]
        if x[0] == "voir":
            self.voir_processer(command)
        if x[0] == "inventaire":
            self.inventaire_processer(command)



    def niveau_actuel_processer(self,command):
        levels = command.split(":")
        self.level = int(levels[1])
        self.queen_reset()
        self.turn += 300
        self.resolve_from_running_routine("incantation")

    def message_processer(self,command):
        #str.split
        split_command1 = command.split(",",maxsplit = 1)
        direction = int(split_command1[0].split()[1])
        message = split_command1[1]
        self.party_message_processer(message, direction)
        self.alive_processer(message) #new


    def alive_processer(self,message):
        try:
            message_dict = json.loads(message)
        except Exception as e:
            print(f"Could not decript message {e}")
            return
        who = message_dict.get("name", None)
        lvl = message_dict.get("lvl", -1) 
        if who is None:
            return
        self.ppl_timeouts[who] = self.turn
        if lvl != -1:
            if who in self.ppl_lv:
                oldlv = self.ppl_lv[who]
            else:
                oldlv = lvl
            self.ppl_lv[who] = lvl

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
        print(f"Unknown command type {command} returning empty handler. Command will be ignored")
        return lambda x: None
    
    ### process command from server
    def command(self, command):
        print(f"Recieved command: {command}")
        if len(command) == 0:
            return
        if self.starting < 3:
            self.starting_command(command)
            return
        processer = self.processer_select(command)
        processer(command)


    def generate_message(self, args)->str:
        if len(self.unsent_commands) > 0 and len(self.running_routine) < 10:
            y = self.unsent_commands.pop(0)
            return y
        else:
            return ""
        
    def sound_directionf(self,direction: int):
        if direction != 0:
            newdir = (2*self.facing + direction -1) % 8
            return SOUND_DIRECTIONS[newdir]
        else:
            return np.array([0,0])


    def uncertanty_mask(self)-> np.array:
        mask = np.zeros(shape=self.size)
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                for z in range(-(self.level + 1),self.level + 1):
                    for w in range(-(self.level + 1),self.level + 1):
                        x1 = (x + z) % self.size[0]
                        y1 = (y + w) % self.size[1]
                        mask[x,y] += (1/(1 + np.abs(z) + np.abs(w)))*(1- np.exp(-0.015*(self.turn - self.objects_countdown[x1,y1])))
        return mask
    
    def distance_matrix(self) -> np.ndarray:
        W, H = self.size
        px, py = self   .pos
        X, Y = np.indices((W, H))
        dx = np.abs(X - px); dy = np.abs(Y - py)
        dx = np.minimum(dx, W - dx)
        dy = np.minimum(dy, H - dy)
        return (dx + dy).astype(int)
    
    def party_message_processer(self, message, direction):
        processers = {
            "inventory": self.bc_inventory_processer, #generated
            "ready": self.bc_incantation_ready, #generated
         }
        try:
            message_dict = json.loads(message)
        except Exception as e:
            print(f"Could not decript message {e}")
            return
        kind = message_dict.get("kind")
        if kind is not None and kind in processers.keys():
            processers[kind](message_dict, direction)
            return
        print("Recieved random broadcast")


    def bc_incantation_ready(self, message_dict, direction):
        """
        """
        #level = message_dict.get("lvl")
        #name = message_dict.get("name")
        if self.queen is None:
            self.queen = message_dict["name"]
        if self.queen > message_dict["name"]:
            return
        self.queen = message_dict["name"]      
        self.sound_direction = direction
        self.pos_at_sound = self.pos.copy()
        self.needs = message_dict.get("needs",{})
        self.fork = message_dict.get("fork",False)
        self.queen_food = message_dict.get("food", 0)
        if direction == 0:
            self.marco_polo_target = self.pos.copy()
            self.marco_polo_confirm += 1
        elif np.array_equal(self.marco_polo_target, self.pos):
            self.marco_polo_target = None
        if self.name in message_dict.get("level_up",[]):
            self.level_up = True

    def bc_inventory_processer(self, message_dict,direction):
        """
        tested
        generator written
        """
        member = message_dict.get("name")
        inventory = message_dict.get("inventory")
        self.ppl_inventories[member] = inventory.copy()

    def queen_needs_generator(self):
        needs = self.drone_needs()
        xpos = self.pos[0]
        ypos = self.pos[1]
        for stone in self.inventory.keys():
            if stone == "nourriture":
                continue
            needs[stone] = max(0, needs.get(stone,0) - self.objects[xpos][ypos].count(stone))
        return needs 

    def drone_buckets(self):
        import gen_gathering as ggat
        ppl_lv2 = {k:v for k,v in self.ppl_lv.items() if k != self.name and k not in self.last_called}        
        ppl_lv = [list(ppl_lv2.values()).count(x+1) for x in range(8)]
        buckets = [math.ceil(x/ggat.level_up_party_size(n+1)) for n,x in enumerate(ppl_lv)]
        return buckets

    def drone_needs(self):
        import gen_gathering as ggat
        collect_needs = {}
        buckets = self.drone_buckets()
        reqs = list(map(lambda w: [ggat.level_up_reqs(w[0]+1)] * w[1]  ,enumerate(buckets)))
        reqs = reduce(lambda x,y: x +y, reqs)
        for stone in self.inventory.keys():
            for entry in reqs:
                collect_needs[stone] = collect_needs.get(stone,0) + entry.get(stone,0)
        return collect_needs
    
    def item_ground_count(self,floor: list,reqs:dict)->bool:
        for key, value in reqs.items():
            if floor.count(key) < value:
                return False
        return True


    def call_to_level_up(self):
        import gen_gathering as ggat
        buckets = self.drone_buckets()
        floor_contents = self.objects[self.pos[0]][self.pos[1]].copy()
        known_players = self.ppl_lv.copy()
        if self.name in known_players:
           del known_players[self.name]
        called_players = [] 
        for lvl, nbuckets in enumerate(buckets):
            for j in range(nbuckets):
                if self.item_ground_count(floor_contents, ggat.level_up_reqs(lvl+1)) and list(known_players.values()).count(lvl + 1) >= ggat.level_up_party_size(lvl +1): 
                    lvl_players = [player for player, level in known_players.items() if level == lvl+1 and player not in self.last_called]
                    if len(lvl_players) < ggat.level_up_party_size(lvl +1):
                        continue
                    for h in range(ggat.level_up_party_size(lvl +1)):
                        who = lvl_players.pop()
                        called_players.append(who)
                        del known_players[who]
                    for k,v in ggat.level_up_reqs(lvl+1).items():
                        for u in range(v):
                            if k in floor_contents:
                                floor_contents.remove(k)
        self.last_called = called_players
        return called_players

    def fork_generator(self):
        if self.turn - self.last_fork > 600 and len(self.ppl_lv) < 11:
            self.last_fork = self.turn
            return True
        return False