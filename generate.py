import networkx as nx
import random
from python.z3 import Int, Or, And, Solver
from collections import OrderedDict

SAT = True

class Formula:
    # Part 1+2a: State
    quantifiers = []
    var_order = {} # var -> index
    clauses = []
    n = 0

    # Part 1+2a: Creation
    def __init__(self, SAT_vars, UNSAT_vars, var_order):
        self.SAT_vars = SAT_vars
        self.UNSAT_vars = UNSAT_vars
        self.var_order = var_order
        self.n = len(var_order)

    def add_clause(self, var1, var2, neg):
        self.clauses.append((self.var_order[var1], self.var_order[var2], neg))

    # Part 2b: Evaluation
    def add_z3_int_int(self, x, y, val, graph):
        return graph[x][y] == val

    def add_z3_var_int(self, x, y, val, graph):
        x_values = []
        G = len(graph)
        for i in range(G):
            if (graph[i][y] == val):
                x_values.append(x == i)
        return Or(x_values)

    def add_z3_int_var(self, x, y, val, graph):
        y_values = []
        G = len(graph)
        for i in range(G):
            if (graph[x][i] == val):
                y_values.append(y == i)
        return Or(y_values)

    def add_z3_var_var(self, x, y, val, graph):
        xy_values = []
        G = len(graph)
        for i in range(G):
            for j in range(G):
                if (graph[i][j] == val):
                    xy_values.append(And(x == i, y == j))
        return Or(xy_values)
    
    def generate_z3_formula(self, choices, graph, neg):
        z3_clauses = []
        for clause in self.clauses:
            
            x = clause[0]
            y = clause[1]
            val = clause[2]

            if neg:
                val = 1 - val

            if type(choices[x]) is int:
                valx = choices[x]
                if type(choices[y]) is int:
                    valy = choices[y]
                    the_clauses = self.add_z3_int_int(valx, valy, val, graph)
                else:
                    vary = choices[y]
                    the_clauses = self.add_z3_int_var(valx, vary, val, graph)
            else:
                varx = choices[x]
                if type(choices[y]) is int:
                    valy = choices[y]
                    the_clauses = self.add_z3_var_int(varx, valy, val, graph)
                else:
                    vary = choices[y]
                    the_clauses = self.add_z3_var_var(varx, vary, val, graph)

            z3_clauses.append(the_clauses)

        if neg:
            formula = Or(z3_clauses)
        else:
            formula = And(z3_clauses)

        return formula



# Fx.Ey.Fz -xy,yz

class Strategies:
    def __init__(self, formula):
        self.formula = formula
        self.SAT_GRAPH = nx.DiGraph()
        self.UNSAT_GRAPH = nx.DiGraph()
        self.level_map = {}  # var index -> # of choices (x_1, x_2, ...)

        self.SAT_GRAPH.add_node("START")
        self.UNSAT_GRAPH.add_node("START")

    # TODO
    def get_fresh_variable(self, level):
        num_level = self.level_map[level]
        return Int(str(level) + "_" + str(num_level))

    def add_info(self, choices, to_SAT):
        if to_SAT:
            graph = self.SAT_GRAPH
            fill_levels = self.formula.UNSAT_vars
        else:
            graph = self.UNSAT_GRAPH
            fill_levels = self.formula.SAT_vars

        #TODO: add path
        len_choices = len(choices)
        for choice in choices:
            index = 0
            current_node = "START"
            previous_node = "START"

            current_level = -1
            next_level = 0

            while index < len(choice):
                next_level = fill_levels[index]
                next_choice = choice[index]
                while current_level < next_level - 1:
                    previous_node = current_node
                    current_node = (graph.neighbors(current_node))[0]
                    current_level += 1
                previous_node = current_node
                nodes = graph.neighbors(current_node)
                found = 0
                for node in nodes:
                    if node == next_choice:
                        found = 1
                        current_node = node
                if found != 1:
                    break
                current_level += 1
                index += 1
            
                # Add path starting at previous node down graph
                level = current_level - 1
                next_level = current_level
                node = previous_node

                # Remember next_choice and index
                while level < self.formula.n:
                    if level == next_level - 1:
                        graph.add_node(choices[index])
                        graph.add_edge(node, choices[index])
                        index += 1
                        if index < len_choices:
                            next_level = choices[index]
                            node = choices[index]
                            level += 1
                        else:
                            next_level = -1
                            node = choices[index]
                            level += 1
                    else:
                        fresh_variable = self.get_fresh_variable(level + 1)
                        graph.add_node(fresh_variable)
                        graph.add_edge(node, fresh_variable)
                        level += 1
                   

    #TODO: generate choices list from graph
    def get_choices(self, from_graph):
        choices = []
        for node in from_graph:
            if from_graph.out_degree(node) == 0:
                leaf_path = nx.all_simple_paths(from_graph, "START", node)[0]
                leaf_path = [node for node in leaf_path if type(node["value"]) is int]
                choices.append(leaf_path)
        return choices

g = nx.DiGraph()
g.add_node("START")
g.add_node("NEXT")
g.add_edge("START", "NEXT")
for n in g.neighbors("START"):
    print(n)

class FOLSolver:
    def __init__(self):
        self.solver = Solver()
        self.const_dict = {}
        self.matrix = []

    def get_var(self, i, j):
        if not self.const_dict:
            self.const_dict["%s%s" % (i, j)] = Int("x_%s_%s") % (i, j)
        return self.const_dict["%s%s" % (i, j)]

    def get_graph(self, n):
        for i in range(n):
            for j in range(n):
                self.solver.add(self.get_var(i, j) == random.randint(0, 2))

    def parse_input(self):
        # str = input()
        str = "Fx.Ey.Fz -xy,yz"

        vars_raw, clauses_raw = str.split(" ")

        # generate var order
        var_list = vars_raw.split(".")
        n = len(var_list)

        var_order = OrderedDict()
        SAT_vars = []
        UNSAT_vars = []
        i = 0
        for var in var_list:
            quant, v = var
            if quant == "E":
                SAT_vars.append(i)
            else:
                UNSAT_vars.append(i)
            var_order[v] = i
            i += 1

        formula = Formula(SAT_vars, UNSAT_vars, var_order)

        clauses_list = clauses_raw.split(",")
        for clause in clauses_list:
            if clause[0] == "-":
                neg = 1
            else:
                neg = 0
            var1 = clause[0 + neg]
            var2 = clause[1 + neg]
            formula.add_clause(var1, var2, neg)

        pass

FOLSolver().parse_input()
