import rpyc
from env import NF, F, PORT
from node import Node


class Command():
    def __init__(self, name, params=[], description=""):
        self.name = name
        self.params = params
        self.description = description

        params_description = ""
        if len(self.params):
            for param, type in self.params:
                params_description += f"<{param}> "
            params_description += "\t"

        self.usage = f"{self.name} {params_description}\t{self.description}"

    def __str__(self) -> str:
        return self.usage

    def __hash__(self) -> int:
        return hash(self.name + str(len(self.params)))

    def is_valid(self, params):
        return True

    def execute(self, params, primary):
        return True


class ActualOrderCommand(Command):
    """
    Proposes an order to the primary which will
    query the quorum and return the final decision
    """

    def __init__(self):
        super().__init__(
            "actual-order",
            params=[("order", str)],
            description="proposes an order to the primary (\"attack\" or \"retreat\")"
        )

    def is_valid(self, params):
        if len(params) != 1:
            return False
        if type(params[0]) is not str:
            return False
        if params[0] != "attack" and params[0] != "retreat":
            return False
        return True

    def execute(self, params, primary):
        order = params[0]
        conn = rpyc.connect("localhost", primary + PORT)
        print(conn.root.execute_order(order))
        conn.close()


class GStateIdCommand(Command):
    """
    Sets the state (faulty or non-faulty) of a given general
    """

    def __init__(self):
        super().__init__(
            "g-state",
            params=[("id", int), ("state", str)],
            description="sets the state of the general with id (\"faulty\" or \"non-faulty\")"
        )

    def is_valid(self, params):
        if len(params) != 2:
            return False
        if not params[0].isnumeric():
            return False
        if params[1] != "faulty" and params[1] != "non-faulty":
            return False
        return True

    def execute(self, params, primary):
        if not self.is_valid(params):
            return

        state = NF if params[1] == "non-faulty" else F

        conn = rpyc.connect("localhost", primary + PORT)
        print(conn.root.set_state(int(params[0]), state))
        conn.close()


class GStateCommand(Command):
    """
    Returns the information about the entire system,
    meaning, the generals, their roles and state
    """

    def __init__(self):
        super().__init__(
            "g-state",
            description="\t\treturns the system state"
        )

    def is_valid(self, params):
        if len(params) != 0:
            return False
        return True

    def execute(self, params, primary):
        conn = rpyc.connect("localhost", primary + PORT)
        print(str(conn.root.get_state()))
        conn.close()


class GKillCommand(Command):
    """
    Kills a given general. If killing the primary, it assigns
    a new primary to lead the quorum. Also removes the killed 
    general from the list of neighbours of all the nodes
    """

    def __init__(self, nodes):
        super().__init__(
            "g-kill",
            params=[("id", int)],
            description="\tkills the general with id"
        )
        self.nodes = nodes

    def is_valid(self, params):
        if len(params) != 1:
            return False
        if not params[0].isnumeric():
            return False
        return True

    def execute(self, params, primary):
        if not self.is_valid(params):
            return

        n = int(params[0])

        if n == primary and len(self.nodes) < 2:
            print(f"Could not kill primary with id {n}...")
            return

        set_new_primary = False
        if n == primary:
            for node in sorted(self.nodes):
                if node != primary:
                    primary = node
                    set_new_primary = True
                    break
            if not set_new_primary:
                print(f"Could not kill primary with id {n}...")
                return

        conn = rpyc.connect("localhost", primary + PORT)
        if set_new_primary:
            print(conn.root.set_primary(primary))
        else:
            print(conn.root.remove_neighbour(n))
        conn.close()

        if n in self.nodes:
            self.nodes.pop(n).terminate()

        return primary if set_new_primary else None


class GAddCommand(Command):
    """
    Adds a new set of generals to the quorum, with new 
    unique ids. Also adds them as neighbours to all the nodes
    """

    def __init__(self, nodes):
        super().__init__(
            "g-add",
            params=[("k", int)],
            description="\tadds k new generals with non-faulty default state"
        )
        self.nodes = nodes

    def is_valid(self, params):
        if len(params) != 1:
            return False
        if not params[0].isnumeric() or int(params[0]) < 1:
            return False
        return True

    def execute(self, params, primary):
        if not self.is_valid(params):
            return

        N = int(params[0])
        conn = rpyc.connect("localhost", primary + PORT)
        neighbours_ids = conn.root.get_free_neighbours_ids(N)

        for n in neighbours_ids:
            node = Node(PORT + n, set(), primary)
            self.nodes[n] = node
            node.start()

        print(conn.root.add_neighbours(neighbours_ids))
        conn.close()


class ExitCommand(Command):
    """
    Exits the program, terminating all processes
    """

    def __init__(self, nodes):
        super().__init__(
            "exit",
            params=[],
            description="\t\t\tterminates the program execution"
        )
        self.nodes = nodes

    def execute(self, params, primary):
        print("Exiting...")
        for n in self.nodes:
            self.nodes[n].terminate()
        exit(0)
