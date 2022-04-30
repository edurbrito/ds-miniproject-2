from collections import Counter
from logging import debug
from multiprocessing import Process
import random

import rpyc
from rpyc.utils.server import ThreadedServer

from env import PORT, NF, F
from rpc import RPCService


class Node(Process):
    """
    Represents a general. It runs as an isolated process,
    child of the main process, and exposes a multithreaded 
    RPC service for handling concurrent connections
    """

    def __init__(self, port, neighbours, primary) -> None:
        super().__init__()
        self.id = port - PORT
        self.port = port
        self.neighbours = neighbours
        if self.port in self.neighbours:
            self.neighbours.remove(self.port)

        self.state = NF
        self.primary = primary
        self.primary_order = ""

        self.rpc_service = RPCService(self)

    def __str__(self) -> str:
        role = "primary" if self.id == self.primary else "secondary"
        return f"G{self.id}, {role}, state={self.state}"

    def set_neighbours(self, neighbours):
        """
        Sets the node neighbours for communicating
        during the quorum activity. If the primary,
        it sets its neighbours first, then sends the
        order for the secondaries to do the same
        """

        self.neighbours = set(neighbours)
        if self.port in self.neighbours:
            self.neighbours.remove(self.port)

        if self.primary == self.id:
            for neighbour in self.neighbours:
                conn = rpyc.connect("localhost", neighbour)
                conn.root.set_neighbours(self.neighbours)
                conn.close()

    def get_free_neighbours_ids(self, n):
        """
        If the primary, it searches for available ids
        for the <n> new nodes to take when joining the quorum
        """

        if self.id == self.primary:
            _neighbours = [neighbour-PORT for neighbour in self.neighbours]
            _neighbours.append(self.id)
            neighbours = sorted(_neighbours)
            new_neighbours = []
            i = 1
            while n > 0:
                if i not in neighbours:
                    new_neighbours.append(i)
                    n -= 1
                i += 1
            return new_neighbours
        return []

    def add_neighbours(self, neighbours):
        """
        If the primary, it adds the newly joined neighbours
        and advertises them to the secondaries
        """

        if self.id == self.primary:
            for neighbour in neighbours:
                if neighbour + PORT not in self.neighbours:
                    self.neighbours.add(neighbour + PORT)
            self.set_neighbours(self.neighbours)
            return self.get_state()
        return f"Could not add {len(neighbours)} new generals..."

    def remove_neighbour(self, node_id):
        """
        If the primary, it removes the killed neighbour
        and advertises it to the secondaries
        """

        if self.id == self.primary and len(self.neighbours) > 1 and node_id + PORT in self.neighbours:
            self.neighbours.remove(node_id + PORT)
            self.set_neighbours(self.neighbours)
            return self.get_state()
        return f"Could not kill general {node_id}..."

    def set_state(self, node_id, state):
        """
        Sets the state of the node with the given id. 
        If the called node is the primary, it will 
        forward the operation to the targeted node
        """

        if state != NF and state != F:
            return f"Could not set state {state} for general {node_id}..."
        if node_id == self.id:
            self.state = state
            return self.get_state() if self.id == self.primary else True
        elif self.id == self.primary and node_id + PORT in self.neighbours:
            conn = rpyc.connect("localhost", node_id + PORT)
            conn.root.set_state(node_id, state)
            conn.close()
            return self.get_state()
        return f"Could not set state {state} for general {node_id}..."

    def get_state(self):
        """
        Gets the node state. If the called node is the primary, 
        it will query the state of all the nodes
        """

        result = [str(self)]
        if self.id == self.primary:
            for neighbour in sorted(self.neighbours):
                conn = rpyc.connect("localhost", neighbour)
                result.append(str(conn.root.get_state()))
                conn.close()
        return "\n".join(result)

    def set_primary(self, primary):
        """
        Sets the primary node. If the called node is 
        the current primary, it will forward the operation
        to all the nodes in the quorum
        """

        self.primary = primary
        if self.id == primary:
            for neighbour in self.neighbours:
                conn = rpyc.connect("localhost", neighbour)
                conn.root.set_primary(primary)
                conn.close()
            self.set_neighbours(self.neighbours)
            return self.get_state()
        return True

    def execute_order(self, order):
        """
        If the primary, it will execute the algorithm
        by communicating with and querying the quorum,
        returning the final output
        """

        if self.id == self.primary:

            self.primary_order = order

            for neighbour in self.neighbours:
                if self.state == F:
                    order = "attack" if random.randint(0, 1) else "retreat"
                conn = rpyc.connect("localhost", neighbour)
                conn.root.set_primary_order(order)
                conn.close()

            result = ""
            faulty_nodes = int(self.state == F)
            decisions = Counter()

            for neighbour in sorted(self.neighbours):
                conn = rpyc.connect("localhost", neighbour)
                state, majority = conn.root.query_neighbours()
                conn.close()
                faulty_nodes += int(state == F)
                decisions[majority] += 1
                result += f"G{neighbour-PORT}, secondary, majority={majority}, state={state}\n"

            if len(self.neighbours) == 0:
                majority = order
                non_faulty = self.state == NF
            else:
                majority = decisions.most_common(1)[0][0]
                non_faulty = decisions.most_common(1)[0][1]

            result = f"G{self.id}, primary, majority={self.primary_order}, state={self.state}\n" + result

            _plural = "s" * int(faulty_nodes != 1)
            _total_nodes = len(self.neighbours) + 1

            if _total_nodes < 3*faulty_nodes + 1 or _total_nodes == 1:
                result += f"\nExecute order: cannot be determined - not enough generals in the system! {faulty_nodes} faulty node{_plural} in the system - {_total_nodes-1} out of {_total_nodes} quorum not consistent"
            else:
                result += f"\nExecute order: {majority}! {faulty_nodes} faulty node{_plural} in the system - {max(non_faulty-faulty_nodes,0)} out of {_total_nodes} quorum suggest {majority}"

            return result
        return ""

    def set_primary_order(self, order):
        """
        If not the primary, it will set the
        received primary order, based on the state,
        to then be forwarded to the rest of the quorum
        """

        if self.id != self.primary:
            if self.state == F:
                order = "attack" if random.randint(0, 1) else "retreat"
            self.primary_order = order
            return True
        return False

    def query_neighbours(self):
        """
        If not the primary, it will exchange
        messages with the quorum neighbours to
        calculate the majority
        """

        if self.id != self.primary:
            decisions = Counter()
            decisions[self.primary_order] += 1

            for neighbour in self.neighbours:
                conn = rpyc.connect("localhost", neighbour)
                decisions[conn.root.get_order()] += 1
                conn.close()

            majority = decisions.most_common(1)[0][0]
            if decisions["attack"] == decisions["retreat"]:
                majority = "undefined"

            return self.state, majority
        return "", ""

    def get_order(self):
        return self.primary_order

    def run(self):
        ThreadedServer(self.rpc_service, port=self.port).start()
