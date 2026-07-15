#!/usr/bin/env python3

import argparse
import gurobipy as g
import numpy as np

def read_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    # print(lines)
    n, m, c = [int(x) for x in lines[0].split()]
    # print("n: ", n)
    # print("m: ", m)
    # print("c: ", c)
    colors = []
    volumes = []
    edges = []
    for c_i in range(c):
        colors.append(int(lines[c_i+1].split()[0]))
        volumes.append(int(lines[c_i+1].split()[1]))
    
    for m_i in range(m):
        edge1 = int(lines[m_i+c+1].split()[0])
        edge2 = int(lines[m_i+c+1].split()[1])
        edges.append((edge1, edge2))

    return n, m, c, colors, volumes, edges

def write_data(file_path, output):
    with open(file_path, 'w') as f:
        if output == []:
            f.write("-1")
        else:
            for x in output:
                f.write(str(int(x)) + "\n")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # n --> number of houses (nodes)
    # m --> number of edges
    # c --> number of colors
    n, m, c, cost, volumes, edges = read_data(input_path)

    # print("Colors: ", cost)
    # print("Volumes: ", volumes)
    # print("Edges: ", edges)

    # Model ---------------------------
    m = g.Model()

    # - variables
    x = m.addVars(n, c, vtype=g.GRB.BINARY)

    # - constraints
    for (i, j) in edges:
        # print(i)
        # print(j)
        for c_i in range(c):
            m.addConstr((x[i-1, c_i] + x[j-1, c_i]) <= 1)

    for i in range(n):
        m.addConstr(g.quicksum(x[i, c_i] for c_i in range(c)) == 1)
    
    for c_i in range(c):
        m.addConstr(g.quicksum(x[i, c_i] for i in range(n)) <= volumes[c_i])

    # - objective
    m.setObjective(
        g.quicksum(
            x[i, c_i] * cost[c_i]
            for c_i in range(c)
            for i in range(n)
        ), 
        g.GRB.MINIMIZE)
    
    m.optimize()

    valid_sol = []

    if m.status == g.GRB.OPTIMAL:
        print("Found optimal solution")
        solution = m.getAttr('x', x)
        # print(solution)
        for sol in solution:
            # print(f"{sol}: {solution[sol]}")
            if(solution[sol] == 1.0):
                # print(sol[1]+1)
                valid_sol.append(sol[1]+1)
    else:
        print("No optimal solution found. Status code:", m.status)

    print(valid_sol)

    write_data(output_path, valid_sol)