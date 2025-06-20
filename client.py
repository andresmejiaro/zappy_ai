import argparse
from main_loop import Orchester
from World import World

def parse_args():
    parser = argparse.ArgumentParser(description="Zappy Client!!!", add_help=False)
    parser.add_argument("-p", type=int,
                        help="port", required = True)
    parser.add_argument("-n", type=str,
                        help="Team name", required = True)
    parser.add_argument("-h", type=str,
                        default="localhost", help="host")
    parser.add_argument("-random", action="store_true",
                        help="Sends random commands to the server for testing purposes")
    return parser.parse_args()


def main():
    args = parse_args()
    world = World(args)
    orc = Orchester(world)
    orc.main_loop(args)
   


if __name__ == "__main__":
    main()
