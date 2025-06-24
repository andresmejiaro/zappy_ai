import argparse
from Orchester import Orchester
from BasicAction import Basic
from Agent import Agent
from MovementPlans import move_to
import numpy as np

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
    #plan = Basic("soir") & Basic("avance") & Basic("soir") & Basic("droite") & Basic("avance") & Basic("gauche") & Basic("avance") & Basic("soir")
    #plan = Basic("soir") & Basic("prend","linemate") & Basic("soir") & Basic("pose","linemate") & Basic("soir")
    plan = move_to(np.array([4,6]),agent)
    orc = Orchester(agent,plan)
    orc.main_loop(args)

if __name__ == "__main__":
    main()
