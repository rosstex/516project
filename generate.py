import networkx as nx
import random
from python.z3 import *
from collections import OrderedDict, defaultdict
import sys

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
    def add_z3_int_int(self, x, y, val, matrix):
        return matrix[x][y] == val

    def add_z3_var_int(self, x, y, val, matrix):
        x_values = []
        G = len(matrix)
        for i in range(G):
            if matrix[i][y] == val:
                x_values.append(x == i)
        return Or(x_values)

    def add_z3_int_var(self, x, y, val, matrix):
        y_values = []
        G = len(matrix)
        for i in range(G):
            if matrix[x][i] == val:
                y_values.append(y == i)
        return Or(y_values)

    def add_z3_var_var(self, x, y, val, matrix):
        xy_values = []
        G = len(matrix)
        for i in range(G):
            for j in range(G):
                if matrix[i][j] == val:
                    xy_values.append(And(x == i, y == j))
        return Or(xy_values)
    
    def generate_z3_formula(self, choices, matrix, neg):
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
                    the_clauses = self.add_z3_int_int(valx, valy, val, matrix)
                else:
                    vary = choices[y]
                    the_clauses = self.add_z3_int_var(valx, vary, val, matrix)
            else:
                varx = choices[x]
                if type(choices[y]) is int:
                    valy = choices[y]
                    the_clauses = self.add_z3_var_int(varx, valy, val, matrix)
                else:
                    vary = choices[y]
                    the_clauses = self.add_z3_var_var(varx, vary, val, matrix)

            z3_clauses.append(the_clauses)

        if neg:
            formula = Or(z3_clauses)
        else:
            formula = And(z3_clauses)

        return formula

    def generate_entire_z3_formula(self, choices, matrix, neg):
        all_clauses = []
        for choice in choices:
            z3_clauses = self.generate_z3_formula(choice, matrix, neg)
            all_clauses.append(z3_clauses)

        return And(all_clauses)

# Fx.Ey.Fz -xy,yz

class Strategies:
    def __init__(self, formula):
        self.formula = formula
        self.SAT_GRAPH = nx.DiGraph()
        self.UNSAT_GRAPH = nx.DiGraph()
        self.level_map = defaultdict(int)  # var index -> # of choices (x_1, x_2, ...)

        self.SAT_GRAPH.add_node("START", value=None)
        self.UNSAT_GRAPH.add_node("START", value=None)

        self.unique_num = 1

    # TODO
    def get_fresh_variable(self, level):
        num_level = self.level_map[level]
        self.level_map[level] += 1
        return Int(str(level) + "_" + str(num_level))

    def add_info(self, choices, to_SAT):
        if len(choices) == 0 or len(choices[0]) == 0:
            return

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

                if len(fill_levels) == 0:
                    current_level = 0
                    break
                if len(list(graph.neighbors("START"))) == 0:
                    current_level = 0
                    break
                while current_level < next_level - 1:
                    previous_node = current_node
                    current_node = (list(graph.neighbors(current_node)))[0]
                    # if none, add vars to get there
                    current_level += 1
                previous_node = current_node
                nodes = graph.neighbors(current_node)
                found = 0
                for node in nodes:
                    if graph.node[node]['value'] == next_choice:
                        found = 1
                        current_node = node
                if found != 1:
                    break
                current_level += 1
                index += 1
            
            # Add path starting at previous node down graph
            level = current_level - 1
            # next_level = current_level
            node = previous_node

            if level < -1:
                level = -1
                next_level = 0

            # Remember next_choice and index
            while level < self.formula.n - 1:
                next_node_num = self.unique_num
                if level == next_level - 1:
                    graph.add_node(next_node_num, value=choice[index])
                    if level == -1:
                        graph.add_edge("START", next_node_num)
                    else:
                        graph.add_edge(node, next_node_num)
                    index += 1
                    if index < len(choice):
                        next_level = fill_levels[index]
                        node = next_node_num
                        level += 1
                    else:
                        next_level = -2
                        node = next_node_num
                        level += 1
                else:
                    fresh_variable = self.get_fresh_variable(level + 1)
                    graph.add_node(next_node_num, value=fresh_variable)
                    if level == -1:
                        graph.add_edge("START", next_node_num)
                    else:
                        graph.add_edge(node, next_node_num)
                    level += 1
                    node = next_node_num
                self.unique_num += 1
                   

    #TODO: generate choices list from graph
    def get_choices(self, from_graph):
        choices = []
        for node in from_graph:
            if node != "START":
                if from_graph.out_degree(node) == 0:
                    leaf_path = list(nx.all_simple_paths(from_graph, "START", node))[0]
                    leaf_path = [from_graph.node[node]["value"] for node in leaf_path][1:]
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
        self.matrix_size = 0
        self.formula = None
        self.strategies = None

        self.parse_input()
        print(self.play_a_game())


    def play_a_game(self):
        """
        0. Provide a graph.
        1. Add all variables into z3. Solve for all variables once. (generate_z3_formula)
        2. Setup two graphs. Fill based on initial solution.
        3. Alternate between SAT and UNSAT turn.
            SAT turn:
                Get choices from graph.
                Solve for variables.
                Fill in new choices on UNSAT's graph.
            UNSAT:
                same
        4. Terminate when one turn is UNSAT.

        """
        initial_vars = []
        for num in range(self.formula.n):
            initial_vars.append(Int(str(num)))

        solver = Solver()

        z3_formula = self.formula.generate_entire_z3_formula([initial_vars], self.matrix, False)
        solver.add(z3_formula)

        if solver.check() == unsat:
            return "UNSAT wins"
        else:
            SAT_choices = []
            UNSAT_choices = []
            model = solver.model()
            for i in range(self.formula.n):
                if i in self.formula.SAT_vars:
                    SAT_choices.append(model[Int(str(i))].as_long())
                else:
                    UNSAT_choices.append(model[Int(str(i))].as_long())

            self.strategies.add_info([SAT_choices], False)
            self.strategies.add_info([UNSAT_choices], True)

            turn = 0

            while True:
                if turn == 0: # SAT
                    choices = self.strategies.get_choices(self.strategies.SAT_GRAPH)
                    z3_formula = self.formula.generate_entire_z3_formula(choices, self.matrix, False)
                    solver = Solver()
                    solver.add(z3_formula)
                    if solver.check() == unsat:
                        return "UNSAT wins"
                    else:
                        new_choices_vals = []
                        model = solver.model()
                        choices_vars = [[x for x in choice if type(x) != int] for choice in choices]
                        for choice in choices_vars:
                            new_choice_vals = []
                            for var in choice:
                                new_choice_vals.append(model[var].as_long())
                            new_choices_vals.append(new_choice_vals)

                        self.strategies.add_info(new_choices_vals, False)

                else: # UNSAT
                    choices = self.strategies.get_choices(self.strategies.UNSAT_GRAPH)
                    z3_formula = self.formula.generate_entire_z3_formula(choices, self.matrix, True)
                    solver = Solver()
                    solver.add(z3_formula)
                    if solver.check() == unsat:
                        return "SAT wins"
                    else:
                        new_choices_vals = []
                        model = solver.model()
                        choices_vars = [[x for x in choice if type(x) != int] for choice in choices]
                        for choice in choices_vars:
                            new_choice_vals = []
                            for var in choice:
                                new_choice_vals.append(model[var].as_long())
                            new_choices_vals.append(new_choice_vals)

                        self.strategies.add_info(new_choices_vals, True)

                turn = 1 - turn
                print(turn)


    def parse_input(self):
        # str = input()
        str = "Ex.Fy.Ez -xy,yz"

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

        self.formula = Formula(SAT_vars, UNSAT_vars, var_order)
        self.strategies = Strategies(self.formula)

        clauses_list = clauses_raw.split(",")
        for clause in clauses_list:
            if clause[0] == "-":
                neg = 1
            else:
                neg = 0
            var1 = clause[0 + neg]
            var2 = clause[1 + neg]
            self.formula.add_clause(var1, var2, 1 - neg)

        self.matrix = [[0, 1, 0], [1, 1, 1], [1, 0, 0]]
        self.matrix_size = 3

FOLSolver()
