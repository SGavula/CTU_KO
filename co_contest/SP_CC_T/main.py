#!/usr/bin/env python3

import argparse
import copy
import random
import time

from collections import defaultdict

# Input:
# N: customers, K: max vans, Q: capacity, Gamma: fixed van cost
# Each customer has: size (s_i), early time (T_i_low), late time (T_i_high)
# Travel Time Matrix T (size N+1 x N+1), T[i][j] represents travel time from node i to node j
# Travel Cost Matrix C (size N+1 x N+1), C[i][j] represents cost of travelling from node i to node j

# Output:
# Obj: value of objective function, K: number of vans unsed
# v_i: number of parcels van i transports, (C_i_1, t_i_1), (C_i_2, t_i_2), ... C_i_v_i: Customer ID, t_i_1: time when van arrives 

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
            "id": i + 1,
            "size": s_i,
            "window": (t_low, t_high)
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

# Verify if the solution is feasible
# solution --> (n1, n2, n3, ...)
def verify_route(route_list, customers, travel_time, travel_cost):
    # 1. Define variable for current load
    current_load = 0
    # 2. Define variable for total time
    total_time = 0
    arrival_times = []
    total_cost = 0

    # Track previous customer
    prev_customer = 0

    for customer_id in route_list:
        customer_id_in_customers = customer_id - 1
        # 1. Check size condition
        current_load += customers[customer_id_in_customers]["size"]
        if current_load > Q:
            return False, None, None

        # 2. Check time condition
        total_time += travel_time[prev_customer][customer_id]
        if total_time > customers[customer_id_in_customers]["window"][1]:
            # Time traveling to customer is higher than top limit
            # Solution infeasible
            return False, None, None
        elif total_time < customers[customer_id_in_customers]["window"][0]:
            # Time traveling to customer is lower than bottom limit
            # Van must wait at customer but route is feasible
            total_time += (customers[customer_id_in_customers]["window"][0] - total_time)

        arrival_times.append(total_time)
        # 3. Add travel cost to total_cost
        total_cost += travel_cost[prev_customer][customer_id]
        # 4. Append arrival time
        # 5. Sum total cost
        prev_customer = customer_id
    
    # Add time to total time between last customer and depot
    total_time += travel_time[prev_customer][0]
    arrival_times.append(total_time)
    # Add cost to total cost between last customer and depot
    total_cost += travel_cost[prev_customer][0]

    return True, total_cost, arrival_times

def find_first_feasible_sol(customers, travel_time, travel_cost, N, K, sort_by_time):
    all_routes = []

    time_sorted_customers = customers

    if sort_by_time:
        time_sorted_customers = sorted(range(1, N+1), key=lambda i: customers[i-1]["window"][0])

    # Get initial valid solution
    # For each customer put them at best possible position in the routes we found so far (we do not generate all routes just one that is good enough) 
    for customer_id in time_sorted_customers:
        best_route_cost = float("inf")
        best_route_idx = -1
        best_position = -1

        # Go through every route, we generated so far and insert customer id according to minimal cost 
        for i, route in enumerate(all_routes):
            # Try every possible position: [New, C1, C2], [C1, New, C2], [C1, C2, New]
            for pos in range(len(route)+1):
                generated_route = route[:pos] + [customer_id] + route[pos:]
                is_feasible, total_cost, _ = verify_route(generated_route, customers, travel_time, travel_cost)
                if is_feasible and total_cost < best_route_cost:
                    best_route_cost = total_cost
                    best_position = pos
                    best_route_idx = i

        if best_route_idx != -1:
            all_routes[best_route_idx].insert(best_position, customer_id)
        elif len(all_routes) <= K:
            all_routes.append([customer_id])
        else:
            return None

    return all_routes

def get_total_objective(all_routes, customers, travel_time, travel_cost, gamma):
    total_gas = 0
    for route in all_routes:
        _, gas_cost, _ = verify_route(route, customers, travel_time, travel_cost)
        total_gas += gas_cost
    
    # Total = Sum of Gas + (Number of active vans * Gamma)
    return total_gas + (len(all_routes) * gamma)

def try_relocate(all_routes, gamma, customers, travel_time, travel_cost):
    for i in range(len(all_routes)):
        for j in range(len(all_routes)):
            if i == j:
                continue
    
            for idx, customer_id in enumerate(all_routes[i]):
                for pos in range(len(all_routes[j]) + 1):
                    updated_r_i = all_routes[i][:idx] + all_routes[i][idx+1:]
                    updated_r_j = all_routes[j][:pos] + [customer_id] + all_routes[j][pos:]

                    is_feasible_i, total_cost_i, _ = verify_route(updated_r_i, customers, travel_time, travel_cost)
                    is_feasible_j, total_cost_j, _ = verify_route(updated_r_j, customers, travel_time, travel_cost)
                    
                    if is_feasible_i and is_feasible_j:
                        _, old_cost_i, _ = verify_route(all_routes[i], customers, travel_time, travel_cost)
                        _, old_cost_j, _ = verify_route(all_routes[j], customers, travel_time, travel_cost)

                        total_old_cost = old_cost_i + old_cost_j + (2 * gamma)

                        new_gamma_count = (1 if not updated_r_i else 2)
                        total_new_cost = total_cost_i + total_cost_j + (new_gamma_count * gamma)

                        if total_new_cost < total_old_cost:
                            # SUCCESS: Apply the changes
                            all_routes[j] = updated_r_j
                            if not updated_r_i:
                                all_routes.pop(i) # Delete the empty van
                            else:
                                all_routes[i] = updated_r_i
                            return True

    return False

def try_swap_systematic(all_routes, customers, travel_time, travel_cost):
    # Try swapping every customer in Route A with every customer in Route B
    # Take route 1 (start from the beginning)
    for r_i in range(len(all_routes)):
        # Take route 2 (start from the route 1 index)
        for r_j in range(r_i + 1, len(all_routes)): # Compare pairs of routes
            for i in range(len(all_routes[r_i])):
                for j in range(len(all_routes[r_j])):
                    
                    # Create actual copies
                    new_r_i = all_routes[r_i].copy()
                    new_r_j = all_routes[r_j].copy()
                    
                    # Perform swap
                    new_r_i[i], new_r_j[j] = new_r_j[j], new_r_i[i]
                    
                    # Verify
                    valid1, cost_i, _ = verify_route(new_r_i, customers, travel_time, travel_cost)
                    valid2, cost_j, _ = verify_route(new_r_j, customers, travel_time, travel_cost)
                    
                    if valid1 and valid2:
                        _, old_cost_i, _ = verify_route(all_routes[r_i], customers, travel_time, travel_cost)
                        _, old_cost_j, _ = verify_route(all_routes[r_j], customers, travel_time, travel_cost)
                        total_old_cost = old_cost_i + old_cost_j
                        total_new_cost = cost_i + cost_j
                        
                        if total_new_cost < total_old_cost:
                            all_routes[r_i] = new_r_i
                            all_routes[r_j] = new_r_j
                            return True
    return False

def local_search(all_routes, gamma, customers, travel_time, travel_cost, start_time, total_time_limit, safety_margin):
    curr_all_routes = copy.deepcopy(all_routes)
    improved = True
    
    while improved:
        improved = False
        
        if time.time() - start_time > (total_time_limit - safety_margin):
            break

        # 1. Try Relocate (Highest priority: can eliminate vans)
        if try_relocate(curr_all_routes, gamma, customers, travel_time, travel_cost):
            improved = True
            continue
            
        # 2. Try Swap (Lower priority: optimizes gas)
        if try_swap_systematic(curr_all_routes, customers, travel_time, travel_cost):
            improved = True
            continue
    
    return curr_all_routes

def shake(all_routes, k, customers, travel_time, travel_cost, K):
    # With 20% try to add new van with customer, if it is possible
    copy_all_routes = copy.deepcopy(all_routes)

    for _ in range(k):
        # Choose random van 1
        r1_idx = random.randrange(len(copy_all_routes))
        if not copy_all_routes[r1_idx]: continue

        # Pick a random customer from that route (van)
        customer_idx = random.randrange(len(copy_all_routes[r1_idx]))
        customer_id = copy_all_routes[r1_idx].pop(customer_idx)

        found_spot = False
        for _ in range(20):
            # With 20% change we add customer to a new van
            # If we want to add customer to new van we must also check if number of van is smaller than available limit
            if random.random() < 0.2 and len(copy_all_routes) < K:
                new_route = [customer_id]
                is_valid, _, _ = verify_route(new_route, customers, travel_time, travel_cost)
                if is_valid:
                    copy_all_routes.append(new_route)
                    found_spot = True
                    break
            else:
                # Pick random route (van) -- idx
                r2_idx = random.randrange(len(copy_all_routes))
                # Pick random position in the given van
                pos = random.randint(0, len(copy_all_routes[r2_idx]))
                # Add customer to that position
                new_route = copy_all_routes[r2_idx][:pos] + [customer_id] + copy_all_routes[r2_idx][pos:]
                is_valid, _, _ = verify_route(new_route, customers, travel_time, travel_cost)
                if is_valid:
                    copy_all_routes[r2_idx] = new_route
                    found_spot = True
                    break

        # If we couldn't find a random valid spot, put the customer back where they were
        if not found_spot:
            copy_all_routes[r1_idx].insert(customer_idx, customer_id)

        # Clean up empty routes
        copy_all_routes = [r for r in copy_all_routes if r]

    return copy_all_routes

# Implementing variable neighbour search algorithm
def vns_search(customers, travel_time, travel_cost, N, K, gamma):
    k_max = min(10, N)

    # 1. Start
    all_routes = find_first_feasible_sol(customers, travel_time, travel_cost, N, K, True)

    attempts = 0
    while all_routes is None and attempts < 100:
        # Shuffle customers and try greedy again
        random.shuffle(customers) 
        all_routes = find_first_feasible_sol(customers, travel_time, travel_cost, N, K, False)
        attempts += 1

    # Check if route is still None
    if all_routes is None:
        return None, None
    else:
        best_sol = all_routes
        best_obj = get_total_objective(all_routes, customers, travel_time, travel_cost, gamma)

        # Main loop of algorithm 
        safety_margin = 1.5
        k = 1
        while time.time() - start_time < (total_time_limit - safety_margin):
            # 2. Shake routes
            shaken_sol = shake(all_routes, k, customers, travel_time, travel_cost, K)

            # 3. Run local search
            sol = local_search(shaken_sol, gamma, customers, travel_time, travel_cost, start_time, total_time_limit, safety_margin)
            obj = get_total_objective(sol, customers, travel_time, travel_cost, gamma)

            if obj < best_obj:
                best_obj = obj
                best_sol = sol
                all_routes = sol
                k = 1
            else:
                k = (k % k_max) + 1
    
    return best_obj, best_sol

def compute_time_of_routes(best_sol, customers, travel_time, travel_cost):
    all_times = []
    for s in best_sol:
        _, _, times = verify_route(s, customers, travel_time, travel_cost)
        all_times.append(times)
    return all_times

def write_data(file_path, all_routes, all_times, obj):
    with open(file_path, 'w') as f:
        # 1. Write the first line: objective and number of vans
        f.write(f"{obj} {len(all_routes)}\n")

        # 2. Write routes to file
        for route_idx, route in enumerate(all_routes):
            # Number of parcel the current van transport
            output_string = [str(len(route))]

            for idx, customer in enumerate(route):
                output_string.append(str(customer))
                # Using :g to format time --> 10.0 -> 10 automatically
                output_string.append(f"{all_times[route_idx][idx]:g}")
            f.write(" ".join(output_string) + "\n")

def write_invalid_data(file_path):
    with open(file_path, 'w') as f:
        f.write("-1")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    parser.add_argument("time_limit", type=float, help="Time limit in seconds")

    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    total_time_limit = args.time_limit

    start_time = time.time()
    
    # 1. Load input
    # N --> number of customers
    # K --> maximum number of vans 
    # Q --> capacity of the van
    # gamma --> cost of using a van
    # customers --> [{'id': id, 'size': size, 'window': (window1, window2)}, ...]
    N, K, Q, gamma, customers, travel_time, travel_cost = read_data(input_path)    

    # 2. Run variable neighbourhood search
    best_obj, best_sol = vns_search(customers, travel_time, travel_cost, N, K, gamma)

    # 3. Check if input has solution
    if not best_obj:
        write_invalid_data(output_path)
    else:
        # Compute time
        all_times = compute_time_of_routes(best_sol, customers, travel_time, travel_cost)
        # Write solution to output file
        write_data(output_path, best_sol, all_times, best_obj)