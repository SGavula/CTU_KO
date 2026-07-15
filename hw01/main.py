#!/usr/bin/env python3

import argparse
import gurobipy as g

def read_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    d = [int(x) for x in lines[0].split()]
    e = [int(x) for x in lines[1].split()]
    
    # Saving the third line as a single value (D)
    D_val = int(lines[2].strip())
    
    return d, e, D_val

def write_data(file_path, obj_val, x_values):
    with open(file_path, 'w') as f:
        f.write(f"{int(obj_val)}\n")
        output_string = " ".join(str(int(x)) for x in x_values)
        f.write(output_string)

def solve_weekly_schedule(d, e, D):
    # Define full demand for the whole week
    full_demand = d * 5 + e * 2

    n = len(full_demand)

    # Model ---------------------------
    m = g.Model()

    # - variables
    x = [0]*n
    z = [0]*n
    for i in range(n):
        x[i] = m.addVar(vtype=g.GRB.INTEGER)
        z[i] = m.addVar(vtype=g.GRB.CONTINUOUS)

    # - constraints
    for i in range(n):
        coverage = g.quicksum(x[(i-k) % 168] for k in range(8))
        d = full_demand[i]
        m.addConstr(d - coverage <= z[i])
        m.addConstr(coverage - d <= z[i])
        m.addConstr(d - coverage <= D)

    # - objective
    m.setObjective(g.quicksum(z[i] for i in range(n)), g.GRB.MINIMIZE)

    m.optimize()

    if m.status == g.GRB.OPTIMAL:
        print("Found optimal solution")
        x_values = [v.X for v in x]
    else:
        print("No optimal solution found. Status code:", m.status)
    
    return m.ObjVal, x_values

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    d, e, D = read_data(input_path)

    obj_val, x_values = solve_weekly_schedule(d, e, D)

    write_data(output_path, obj_val, x_values)