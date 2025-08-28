import argparse
from zappy_ai.infra_orchestrator import Orchester
from zappy_ai.domain_agent import Agent
from zappy_ai.master_plan import master_plan


def parse_args():
    parser = argparse.ArgumentParser(
        description="Zappy Client!!!", add_help=False)
    parser.add_argument("-p", type=int,
                        help="port", required=True)
    parser.add_argument("-n", type=str,
                        help="Team name", required=True)
    parser.add_argument("-h", type=str,
                        default="localhost", help="host")
    return parser.parse_args()


def main():
    args = parse_args()
    agent = Agent(args)
    plan = master_plan
    orc = Orchester(agent, plan)
    orc.main_loop(args)


if __name__ == "__main__":
    main()
