
from SOrchester import SOrchester
from Game import Game

if __name__ == "__main__":
    game = Game()
    orq = SOrchester(game)
    orq.main_loop()