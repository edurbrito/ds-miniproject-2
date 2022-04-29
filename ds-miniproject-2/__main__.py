import readline  # for key up support
import signal
import sys
from logging import CRITICAL, DEBUG, ERROR, INFO, basicConfig, debug, info

import rpyc

from env import PORT
from node import Node
from args import ArgsParser


basicConfig(filename="./log.out", filemode="w", level=DEBUG)


if len(sys.argv) != 2 or not sys.argv[1].isnumeric() or int(sys.argv[1]) < 1:
    print(
        "Usage: general-byzantine-problem.sh [N]\n\tN\tnumber of processes (N > 0)"
    )
    info(f"wrong args: {sys.argv}")
    exit(1)


"""
Creates and start N processes/nodes, each with 
an RPC service exposed by a socket connection
"""

N = int(sys.argv[1])

nodes = {}
primary = None

for n in range(1, N+1):
    if primary is None:
        primary = n
    nodes[n] = Node(PORT + n, set(), primary)

for n in nodes:
    nodes[n].start()

"""
Sends a command to the primary to set the 
quorum neighbour nodes for them to 
communicate between eachother
"""

conn = rpyc.connect("localhost", nodes[primary].port)
conn.root.set_neighbours(set(range(PORT+1, PORT + N + 1)))
conn.close()

info(f"{len(nodes)} nodes started - primary node with id {primary}")


args_parser = ArgsParser(primary, nodes)

print(args_parser.get_usage())


def signal_handler(sig, frame):
    info("ctrl+c")
    args_parser.execute("exit")

signal.signal(signal.SIGINT, signal_handler)


while True:

    command = input("\nCommand: ")

    if not args_parser.is_valid_command(command):
        print(args_parser.get_usage("\nInvalid Command..."))
        info(f"invalid command: {command}")
        continue

    info(f"command executed: {command}")

    args_parser.execute(command)
