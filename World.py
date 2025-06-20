import time
from objects import commands_single, commands_object, commands_text, objects
import random

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


class World():
    
    def __init__(self, args):
        self.world = {"identity":"drone","position" :None, "facing":["N","S","E","W"] }
        self.action_queue = []
        self.partial_msg = b''
        self.starting = 0
        self.message_queue = []
        self.team = args.n
        self.nb_client = 0
        self.movement_history = []
        

    def starting_command(self, command):
        if self.starting == 0:
            if command == "BIENVENUE":
                self.starting += 1
                self.message_queue.append(f"{self.team}")
                return
            else:
                print(f"No se recibio el mensaje de bienvenida al iniciar {command}")
                self.starting = 4
        if self.starting == 1:
            if command.isdigit():
                self.nb_client = int(command)
                self.starting += 1
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
                self.coords = map(int,coords)
                self.starting += 1

    def sanity_check(self):
        pass

    def ok_processer(self, command):
        pass
    
    def ko_processer(self, command):
        pass

    def elevation_en_cours_processer(self,command):
        pass

    def mort_processer(self,command):
        pass

    def bracket_processer(self,command):
        pass

    def niveau_actuel_processer(self,command):
        pass

    def message_processer(self,command):
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
        if len(self.message_queue) > 0 and len(self.action_queue) < 10:
            return self.message_queue.pop(0)
        else:
            return ""


    def update_world(self,msg: str):
        func = msg.split(maxsplit=2)
        if func[0] in self.updater.keys():
            self.updater[func[0]](func[1])
        else:
            print(f"Command {func[0]} in {msg} not found skipping")

    updater = {}
    #updater = {"avance", "droite", "gauche", "voir", "inventaire", "expulse", "incantation", "fork", "connect_nbr","prend", "pose","broadcast"}