import argparse
from Orchester import Orchester
from Plans import Basic
from Agent import Agent

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
    agent = Agent(args)
    soir = Basic("soir") & Basic("avance") & Basic("soir")
    orc = Orchester(agent,soir)
    orc.main_loop(args)

if __name__ == "__main__":
    main()
