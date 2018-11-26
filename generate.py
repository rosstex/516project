import networkx as nx
from z3 import *

class FOLSolver:
    def __init__(self):
        self.G = nx.DiGraph()
        self.G.add_node(1)
        self.G.add_node(2)

        self.G.add_edge(1, 2)

        self.solver = Solver()


    def r(self, x1, x2):
        return self.G.has_edge(x1, x2)

    def run(self):
        nodes = self.G.nodes
        for node1 in nodes:
            for node2 in nodes:
                self.solver.add(Bool("{}_{}".format(node1, node2)) == self.r(node1, node2))
        print(self.solver)


FOLSolver().run()