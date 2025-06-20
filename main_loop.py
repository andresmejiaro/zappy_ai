import socket

from World import World


class Orchester():

    def __init__(self, world: World):
        self.partial_msg = b''
        self.world = world
    
    def process_input(self, input):
        self.partial_msg += input
        s = self.partial_msg.find(b'\n')
        while s != -1:
            temp = self.partial_msg.split(b'\n',1)
            if len(temp) == 0:
                self.partial_msg = b''
                break
            self.world.command(temp[0].decode("utf-8"))
            if len(temp) == 1:
                self.partial_msg = b''
                break
            else:
                self.partial_msg = temp[1]
            s = self.partial_msg.find(b'\n')


    def main_loop(self, args):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((args.h, args.p))
                while True:
                    if not args.random:
                        input = client.recv(16)
                        if not input:
                            break
                    else:
                        input = ""
                    self.process_input(input);
                    self.world.sanity_check()
                    message = self.world.generate_message(args);
                    if len(message) > 0:
                        client.sendall((message + '\n').encode())
        except ConnectionRefusedError:
            print("Server is down. Unable to connect.")
        except Exception as e:
            print("An error occurred:", e)








