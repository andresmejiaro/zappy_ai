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


    def command(self, command):
        if len(command) == 0:
            return
        if self.starting < 3:
            self.starting_command(command)
            return


    def generate_message(self, args)->str:
        if args.random:
            time.sleep(1)
            return generate_random_message()
        if len(self.message_queue) > 0:
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