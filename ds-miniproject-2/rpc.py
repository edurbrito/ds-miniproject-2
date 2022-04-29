import rpyc


class RPCService(rpyc.Service):

    def __init__(self, node) -> None:
        self.node = node
        super().__init__()

    def exposed_get_state(self):
        return self.node.get_state()

    def exposed_set_state(self, node_id, state):
        return self.node.set_state(node_id, state)

    def exposed_set_neighbours(self, ports):
        return self.node.set_neighbours(ports)

    def exposed_get_free_neighbours_ids(self, n):
        return self.node.get_free_neighbours_ids(n)

    def exposed_add_neighbours(self, neighbours):
        return self.node.add_neighbours(neighbours)

    def exposed_remove_neighbour(self, node_id):
        return self.node.remove_neighbour(node_id)

    def exposed_set_primary(self, node_id):
        return self.node.set_primary(node_id)

    def exposed_execute_order(self, order):
        return self.node.execute_order(order)

    def exposed_set_primary_order(self, order):
        return self.node.set_primary_order(order)

    def exposed_query_neighbours(self):
        return self.node.query_neighbours()

    def exposed_get_order(self):
        return self.node.get_order()