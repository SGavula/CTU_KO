#!/usr/bin/env python3

import argparse
import gurobipy as g

from collections import defaultdict

def read_data(file_path):
    with open(file_path, 'r') as f:
        data = f.read().split()
        
    if not data:
        return None

    # Pointer to track our position in the flat list of values
    it = iter(data)
    
    # 1. Load basic parameters
    # N: customers, K: max vans, Q: capacity, Gamma: fixed van cost
    N = int(next(it))
    K = int(next(it))
    Q = int(next(it))
    gamma = float(next(it))
    
    # 2. Load customer data
    # Each customer has: size (s_i), early time (T_i_low), late time (T_i_high)
    customers = []
    for i in range(N):
        s_i = int(next(it))
        t_low = int(next(it))
        t_high = int(next(it))
        customers.append({
            'id': i + 1,
            'size': s_i,
            'window': (t_low, t_high)
        })
        
    # 3. Load Travel Time Matrix T (size N+1 x N+1)
    # Index 0 is the Depot 
    travel_time = []
    for r in range(N + 1):
        row = [float(next(it)) for _ in range(N + 1)]
        travel_time.append(row)
        
    # 4. Load Travel Cost Matrix C (size N+1 x N+1)
    travel_cost = []
    for r in range(N + 1):
        row = [float(next(it)) for _ in range(N + 1)]
        travel_cost.append(row)
        
    return N, K, Q, gamma, customers, travel_time, travel_cost

def write_data(file_path, all_routes, obj):
    with open(file_path, 'w') as f:
        # 1. Write the first line: objective and number of vans
        f.write(f"{obj} {len(all_routes)}\n")

        # 2. Write routes to file
        for route in all_routes:
            output_string = [str(len(route))]
            for customer, time in route:
                output_string.append(str(customer))
                # Using :g to format time --> 10.0 -> 10 automatically
                output_string.append(f"{time:g}")
            f.write(" ".join(output_string) + "\n")

def write_invalid_data(file_path):
    with open(file_path, 'w') as f:
        f.write("-1")
        
def solve(N, K, Q, gamma, customers, travel_time, travel_cost):
    # Model ---------------------------
    m = g.Model()

    # - variables
    x = m.addVars(N + 1, N + 1, K, vtype=g.GRB.BINARY)
    y = m.addVars(K, vtype=g.GRB.BINARY)
    t = m.addVars(N+1, K, vtype=g.GRB.CONTINUOUS)

    # - constraints
    # 1.
    for u in range(1, N+1):
        m.addConstr(
            g.quicksum(
                x[u, v, d] for d in range(K) for v in range(N + 1) if v != u
            ) == 1
        )

    # 2.
    for v in range(1, N+1):
        m.addConstr(
            g.quicksum(
                x[u, v, d] for d in range(K) for u in range(N + 1) if u != v
            ) == 1
        )

    # 3.
    m.addConstr(
        g.quicksum(
            x[0, v, d] for d in range(K) for v in range(1, N + 1)
        ) <= K
    )

    # 4.
    m.addConstr(
        g.quicksum(
            x[u, 0, d] for d in range(K) for u in range(1, N + 1)
        ) <= K
    )

    # 5.
    for i in range(1, N + 1):
        for d in range(K):
            m.addConstr(
                g.quicksum(x[u, i, d] for u in range(N+1) if u != i) ==
                g.quicksum(x[i, v, d] for v in range(N+1) if v != i)
            )
    
    # 6.
    for d in range(K):
        m.addConstr(
            g.quicksum(customers[v-1]["size"] * x[u, v, d] for v in range(1, N+1) for u in range(N+1) if u != v) <= Q
        )

    # 7.
    for d in range(K):
        m.addConstr(
            g.quicksum(x[0, v, d] for v in range(1, N+1)) == y[d]
        )
        m.addConstr(
            g.quicksum(x[u, 0, d] for u in range(1, N+1)) == y[d]
        )

    ### TIME
    # 8.
    M = 1000000
    for u in range(N + 1):
        for v in range(1, N + 1):
            if u != v:
                for d in range(K):
                    m.addConstr(
                        t[u, d] + travel_time[u][v] <= t[v, d] + M * (1 - x[u, v, d])
                    )

    # 9. + 10.
    for i in range(1, N + 1):
        for d in range(K):
            m.addConstr(
                t[i, d] <= customers[i-1]["window"][1]
            )
            m.addConstr(
                t[i, d] >= customers[i-1]["window"][0]
            )

    # 11.
    for v in range(1, N+1):
        for d in range(K):
            m.addConstr(
                travel_time[0][v] * x[0, v, d] <= t[v, d]
            )

    total_demand = sum(c['size'] for c in customers)
    min_vans = (total_demand + Q - 1) // Q
    m.addConstr(g.quicksum(x[0, v, d] for v in range(1, N + 1) for d in range(K)) >= min_vans)

    # - objective
    m.setObjective(
        g.quicksum(
            travel_cost[u][v] * x[u, v, d] for u in range(N+1) for v in range(N+1) for d in range(K) if u != v
        ) + gamma * g.quicksum(y[d] for d in range(K))
        ,
        g.GRB.MINIMIZE)

    m.optimize()

    if m.status == g.GRB.OPTIMAL:
        print("Found optimal solution")
        obj_val = m.ObjVal
        x_sol = m.getAttr('x', x)
        y_sol = m.getAttr('x', y)
        t_sol = m.getAttr('x', t)

        return {
            "obj": obj_val,
            "x": x_sol,
            "y": y_sol,
            "t": t_sol,
        }
    elif m.status == g.GRB.INFEASIBLE:
        print("The model is infeasible.")
        return -1
    else:
        print(f"Optimization was stopped with status {m.status}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # N --> number of customers
    # K --> maximum number of vans 
    # Q --> capacity of the van
    # gamma --> cost of using a van
    # customers --> [{'id': id, 'size': size, 'window': (window1, window2)}, ...]

    N, K, Q, gamma, customers, travel_time, travel_cost = read_data(input_path)

    output = solve(N, K, Q, gamma, customers, travel_time, travel_cost)

    if output == -1:
        write_invalid_data(output_path)
    else:
        used_vans = [d for d in range(K) if output["y"][d] > 0.5]

        valid_solutions = defaultdict(float)
        for d in range(K):
            route = []
            for state in output["x"]:
                if(output["x"][state] > 0.5):
                    valid_solutions[state] = output["t"][(state[1], state[2])]

        all_routes = []

        for d in used_vans:
            route = []
            # Start at depot
            curr = 0

            while True:
                next_node = None
                # Find next node where current node is at the second position
                for key in valid_solutions.keys():
                    if key[0] == curr and key[2] == d:
                        next_node = key[1]
                        break
                
                # If we return to depot (0) or get stuck, the tour is done
                if next_node == 0 or next_node is None:
                    break

                # Get the arrival time
                arrival_time = valid_solutions[(curr, next_node, d)]
                
                route.append((next_node, arrival_time))
                # Move to the next customer
                curr = next_node
                
            if route:
                all_routes.append(route)

        write_data(output_path, all_routes, output["obj"])