#!/usr/bin/env python3

import argparse
import gurobipy as g
import numpy as np

def read_data(file_path):
    with open(file_path, 'r') as f:
        line = f.readline().split()
        if not line:
            exit()
        n, w, h = map(int, line)
        data = np.fromfile(f, sep=" ", dtype=int)
    stripes = data.reshape((n, h, w, 3))
    return n, w, h, stripes

def compute_dist(s1, s2):
    first_mat = s1[:, -1, :]
    second_mat = s2[:, 0, :]
    return np.sum(np.abs(first_mat - second_mat))

def compute_dist_matrix(stripes):
    D = np.zeros((n+1, n+1))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            D[i+1, j+1] = compute_dist(stripes[i], stripes[j])
    return D

def find_subtours(solution, n):
    nodes_dict = {i: j for (i, j) in solution.keys() if solution[(i, j)] > 0.5}
    unvisited_nodes = [i for i in range(n + 1)]
    
    min_cycle = None
    while unvisited_nodes:
        cycle = []
        start_node = unvisited_nodes[0]
        cycle.append(start_node)
        unvisited_nodes.remove(start_node)
        current_node = nodes_dict[start_node]
        while current_node != start_node:
            cycle.append(current_node)
            unvisited_nodes.remove(current_node)
            current_node = nodes_dict[current_node]
        
        if min_cycle == None or len(cycle) < len(min_cycle):
            min_cycle = cycle
    return min_cycle        

def solveTsp(distances):
    # Define gurobi model
    # Model ---------------------------
    m = g.Model()
    # Enable lazy constraints
    m.Params.lazyConstraints = 1

    # - variables
    x = m.addVars([(i, j) for i in range(n + 1) for j in range(n + 1) if i != j], vtype=g.GRB.BINARY)

    # - constraints
    for i in range(n+1):
        m.addConstr(g.quicksum(x[i, j] for j in range(n+1) if j != i) == 1)

    for j in range(n+1):
        m.addConstr(g.quicksum(x[i, j] for i in range(n+1) if j != i) == 1)

    # - objective
    m.setObjective(
        g.quicksum(
            x[i, j] * D[i, j]
            for j in range(n+1)
            for i in range(n+1)
            if i != j
        ), 
        g.GRB.MINIMIZE)

    def my_callback(model, where):
        # Callback is called when some event occur. The type of event is
        # distinguished using argument ’’where’’.
        # In this case, we want to perform something when an integer
        # solution is found, which corresponds to ’’GRB.Callback.MIPSOL’’.
        if where == g.GRB.Callback.MIPSOL:
            # Get the value of variable x[i, j] from the solution.
            # You may also pass a list of variables to the method.
            values = model.cbGetSolution(x)
            min_cycle = find_subtours(values, n)
            # Add lazy constraint to model.
            if len(min_cycle) < n + 1:
                constr_sum = g.quicksum(x[i, j] for i in min_cycle for j in min_cycle if i != j)
                model.cbLazy(constr_sum <= len(min_cycle) - 1)
    
    m.optimize(my_callback)

    solution = []
    if m.status == g.GRB.OPTIMAL:
        print("Found optimal solution")
        nodes_dict = {i: j for (i, j) in x.keys() if x[i, j].X > 0.5}
        start_node = 0
        current_node = nodes_dict[0]
        while current_node != start_node:
            solution.append(current_node)
            current_node = nodes_dict[current_node]
    else:
        print("No optimal solution found. Status code:", m.status)

    return solution

def write_data(file_path, solution):
    with open(file_path, 'w') as f:
        output_string = " ".join(str(int(x)) for x in solution)
        f.write(output_string)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # n --> number of stripes
    # w --> with of strip
    # h --> height of strip
    n, w, h, stripes = read_data(input_path)
    
    D = compute_dist_matrix(stripes)
    solution = solveTsp(D)

    # print(solution)

    write_data(output_path, solution)