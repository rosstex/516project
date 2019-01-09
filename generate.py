import networkx as nx
import random
from python.z3 import Int, Or, And
from collections import OrderedDict

SAT = True

class Formula:
    # Part 1+2a: State
    quantifiers = []
    var_order = {}
    z3_symbols = []
    clauses = []
    n = 0

    # Part 1+2a: Creation
    def __init__(self, quantifiers, var_order):
        self.quantifiers = quantifiers
        self.var_order = var_order
        self.n = len(var_order)

        for i in range(len(self.var_order)):
            self.z3_symbols.append(Int("var_{}".format(i)))

    def add_clause(self, var1, var2, neg):
        self.clauses.append((var_order[var1], var_order[var2], neg))

    # Part 2b: Evaluation
    def add_z3_int_int(self, x, y, val, graph):
        return [graph[x][y] == val]

    def add_z3_var_int(self, x, y, val, graph):
        x_values = []
        G = len(graph)
        for i in range(G):
            if (graph[i][y] != val):
                x_values.append(x != i)
        return x_values

    def add_z3_int_var(self, x, y, val, graph):
        y_values = []
        G = len(graph)
        for i in range(G):
            if (graph[x][i] != val):
                y_values.append(y != i)
        return y_values

    def add_z3_var_var(self, x, y, val, graph):
        xy_values = []
        G = len(graph)
        for i in range(G):
            for j in range(G):
                if (graph[i][j] != val):
                    xy_values.append(Or(x != i, y!= j))
        return xy_values        
    
    def generate_z3_formula(self, choices, graph, neg):
        z3_clauses = []
        for clause in clauses:
            the_clauses = []
            
            x = clause[0]
            y = clause[1]
            val = clause[2]

            if type(choices[x]) is int:
                valx = choices[x]
                if type(choices[y]) is int:
                    valy = choices[y]
                    the_clauses = add_z3_int_int(valx, valy, val, graph)
                else:
                    vary = choices[y]
                    the_clauses = add_z3_int_var(valx, vary, val, graph)
            else:
                varx = choices[x]
                if type(choices[y]) is int:
                    valy = choices[y]
                    the_clauses = add_z3_var_int(varx, valy, val, graph)
                else:
                    vary = choices[y]
                    the_clauses = add_z3_var_var(varx, vary, val, graph)

            z3_clauses.append(the_clauses)
                 
        if neg:
            formula = Or(z3_clauses)
        else:
            formula = And(z3_clauses)

        return formula

    
# Part 2a: Parse input
if __name__ == "__main__":
    # str = input()
    str = "Fx.Ey.Fz -xy,yz"

    vars_raw, clauses_raw = str.split(" ")

    # generate var order
    var_list = vars_raw.split(".")
    n = len(var_list)

    var_order = OrderedDict()
    quantifiers = []
    i = 0
    for var in var_list:
        quant, v = var
        quantifiers.append(quant)
        var_order[v] = i
        i += 1

    formula = Formula(quantifiers, var_order)

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



# Fx.Ey.Fz -xy,yz




# class FOLSolver:
#     def __init__(self):
#         self.solver = Solver()
#         self.const_dict = {}
#         self.SAT_GRAPH = nx.DiGraph()
#         self.UNSAT_GRAPH = nx.DiGraph()
#         self.matrix = []
#
#         self.formula_constraints =
#
#     def get_var(self, i, j):
#         if not self.const_dict:
#             self.const_dict["%s%s" % (i, j)] = Int("x_%s_%s") % (i, j)
#         return self.const_dict["%s%s" % (i, j)]
#
#     def get_graph(self, n):
#         for i in range(n):
#             for j in range(n):
#                 self.solver.add(self.get_var(i, j) == random.randint(0, 2))
#
#     def run(self):
#         n = 1
#         while True:
#             try:
#                 self.matrix = [[self.get_var(i, j) for i in range(n)]for j in range(n)]
#
#                 while self.solver.check() != unsat:
#
#
#
#
#
#
#
#
#
#
#                     turn = not turn
#
#             except KeyboardInterrupt:
#                 break
#         print(self.solver)
#
# FOLSolver().run()
