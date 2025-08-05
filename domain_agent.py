import time
import random
import numpy as np
import json

random.seed(42)


#Rotating to the left
DIRECTIONS = list(map(np.array,[[1,0],[0,-1],[-1,0],[0,1]]))



class Agent():
    
    def __init__(self, args):
        self.running_routine = [] ## Messages Sent not answered
        self.unsent_commands = [] ## Messages to be sent
        self.resolved_queue = [] ## Messages Resolved includes status
        self.starting = 0 # just started the client for handshage
        self.team = args.n # team
        self.size = np.array([10,10]) #size of the map
        self.pos = np.array([0,0]) #actual position wrt spawning point
        self.facing = 0 #direction facing wrt spawning point
        self.turn = 0 # internal control of time
        self.inventory ={"nourriture": 10, "linemate": 0, "deraumere": 0, "sibur": 0, "mendiane": 0, "phiras": 0, "thystame": 0} # starting inventory updates whenever inventory is seen
        self.level = 1 #level
        self.objects_countdown = None #timeouts of seen parts of the map, forgets
        self.last_turn = 0 #for control of timeouts last seen turn
        self.new_totem = np.array([0,0]) # for found totems
        self.new_totem_size = 0 # for found totems
        self.totem_pos = np.array([0,0]) # for starting totem
        self.totem_size = 0 # starting totem
        self.name = id(self) #give yourself a name
        self.reset_party() #reset info about teams


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
                self.objects_countdown = np.zeros(self.size)
                self.starting += 1

    
    def food_update(self):
        #update 
        time_diff = self.turn - self.last_turn
        self.inventory["nourriture"] -= time_diff/126
        if time_diff > 0:
            print(f"food: {self.inventory["nourriture"]}")
        self.last_turn = self.turn
        if self.objects_countdown is not None:
            breaks = -(self.objects_countdown - self.turn) > 100
            for x in range(self.size[0]):
                for y in range(self.size[1]):
                    if breaks[x,y]:
                        self.objects[x][y] = []
                    if self.objects[x][y].count("linemate") >= self.totem_size:
                        self.new_totem = np.array([x,y])
                        self.new_totem_size = self.objects[x][y].count("linemate")
                    if np.array_equal(self.totem_pos,np.array([x,y])):
                        if len(self.objects[x][y]) != 0:
                            self.totem_size = self.objects[x][y].count("linemate")

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
            if things[1] in self.objects[self.pos[0]][self.pos[1]]:
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
                    okaiable_commands[j](command, x[0],"ko")
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
        self.resolve_from_running_routine("incantation")

    def message_processer(self,command):
        #str.split
        split_command1 = command.split(",",maxsplit = 1)
        direction = int(split_command1[0].split()[1])
        message = split_command1[1]
        self.team_message_processer(message, direction)


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

    def party_message_processer(self, message, direction):
        processers = {
            "lfg": self.bc_lfg_processer,#generated
            "join": self.bc_join_processer, #generated
            "inventory": self.bc_inventory_processer,
            "complete": self.bc_complete_processer,
            "closed": self.bc_closed_party, #generated
            "disband": self.bc_disband #generated
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
        print("Recived random broadcast")
        

    def bc_lfg_processer(self, message_dict, direction):
        """
        Recieves messages of poosible lfg.

        Tested
        generator written
        """
        lvl = int(message_dict.get("lvl",-1))
        if lvl != self.level + 1:
            return
        remote_name =message_dict.get("party_name")
        if self.party_name is not None:
            if remote_name < self.party_name:
                return
            else:
                self.reset_party()  
        self.party_name = remote_name
        self.party_role = 1
        
        

    def bc_join_processer(self,message_dict, direction):
        """
        generator written
        """
        if message_dict.get("party_name") != self.party_name and self.party_role != 3:
            return 
        self.party_members.append(message_dict.get("name"))       

    def bc_inventory_processer(self, message_dict,direction):
        member = message_dict.get("name")
        if member not in self.party_members:
            return
        inventory = message_dict.get("inventory")
        self.party_inventories[member] = inventory

    def bc_complete_processer(self,message_dict, direction):
        if message_dict.get("party_name") != self.party_name:
            return
        self.colection_complete = True

    def bc_closed_party(self, message_dict,direction):
        """
        Message to send when the party is full
        tested
        """       
        if message_dict.get("party_name") != self.party_name and self.party_role != 1:
            return
        if self.name not in message_dict.get("members"):
            self.reset_party()
        self.party_role = 2
        self.party_members = message_dict.get("members")

    def bc_disband(self, message_dict,direction):
        """
        disbands if the leader says so

        tested
        """
        if message_dict.get("party_name") != self.party_name:
            return
        self.reset_party()

    def reset_party(self):
        """
        Resets variables related to the partys
        """
        self.party_name = None # for partying up
        self.party_role = 0 # 0 = none ,1 = applicant, 2=member, 3 = master
        self.party_members = [] #who is in our party
        self.party_inventories = {} #inventories of our party members
        self.lfg = False # Am I Leader of a not full group
        self.colection_complete = False # is what we are doing done?
        self.party_size = 2 # party size limit 
        self.party_closed = False # did I send closing message