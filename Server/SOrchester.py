import socket

from Game import Game


class   SOrchester():

    def __init__(self, game: Game):
        self.partial_msg = b''
        self.game = game
        
    def process_input(self, input):
        self.partial_msg += input
        s = self.partial_msg.find(b'\n')
        while s != -1:
            temp = self.partial_msg.split(b'\n',1)
            if len(temp) == 0:
                self.partial_msg = b''
                break
            print(f"Client: {temp[0].decode("utf-8")}")
            self.game.command(temp[0].decode("utf-8"))
            if len(temp) == 1:
                self.partial_msg = b''
                break
            else:
                self.partial_msg = temp[1]
            s = self.partial_msg.find(b'\n')


    def main_loop(self):
        #try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.bind(("localhost", 5555))
                server.listen(1)
                conn, addr = server.accept()
                print(f"Listening on {"localhost"}:{5555} ...")
                input = b''
                with conn:
                    while True:
                        self.process_input(input)
                        message = self.game.generate_message()
                        print(f"Server: {message}")
                        conn.sendall((message + '\n').encode())
                        input = conn.recv(16)
                        if not input:
                            break
        #except ConnectionRefusedError:
        #    print("Server is down. Unable to connect.")
        #except Exception as e:
        #    print("An error occurred:", e)

    






