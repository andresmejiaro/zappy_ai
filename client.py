import argparse
from infra_orchestrator import Orchester
from core_bt_interactions import Interaction
from domain_agent import Agent
import numpy as np
from core_behavior_tree import  GEN
from gen_movement import roam
from gen_levelup import level_up
from plan_master import master_plan

def parse_args():
    parser = argparse.ArgumentParser(description="Zappy Client!!!", add_help=False)
    parser.add_argument("-p", type=int,
                        help="port", required = True)
    parser.add_argument("-n", type=str,
                        help="Team name", required = True)
    parser.add_argument("-h", type=str,
                        default="localhost", help="host")
    return parser.parse_args()


def main():
    args = parse_args()
    agent = Agent(args)
    plan = master_plan
    orc = Orchester(agent,plan)
    orc.main_loop(args)

if __name__ == "__main__":
    main()
