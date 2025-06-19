import socket
from objects import commands_single, commands_object, commands_text, objects
import random
import time


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


def generate_message(args, in_message):
    if args.random:
        time.sleep(1)
        return generate_random_message()
    


def main_loop(args):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((args.h, args.p))
            while True:
                if not args.random:
                    in_message = client.recv(1024)
                else:
                    in_message = ""
                message = generate_message(args, in_message);
                if len(message) > 0:
                    client.sendall((message + '\n').encode())
    except ConnectionRefusedError:
        print("Server is down. Unable to connect.")
    except Exception as e:
        print("An error occurred:", e)