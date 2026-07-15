#!/usr/bin/env python3

import argparse
import gurobipy as g
import numpy as np

# The 'graph' is a list where each index corresponds to a node ID
    # graph = [
    #     [], # 0: S (Original Source)
    #     [], # 1: T (Original Sink)
    #     [], # 2: S' (Super Source)
    #     [], # 3: T' (Super Sink)
    #     [], # 4: Customer 1
    #     [], # 5: Customer 2
    #     [], # 6: Customer 3
    #     [], # 7: Customer 4
    #     [], # 8: Product 1
    #     [], # 9: Product 2
    #     [], # 10: Product 3
    #     [], # 11: Product 4
    #     [], # 12: Product 5
    #     # ... more customers
    #     [], # 4 + m - 1: customer m
    #     [], # 4 + m: Product 1
    #     [], # 4 + m + 1: Product 2
    #     # ... more products ...
    #     [], # 4 + m + n - 1: product n
    # ]

class FlowEdge:
    def __init__(self, to , capacity, edge_idx):
        self.to = to
        self.capacity = capacity # Saving only upper capacity because we will work with normalized graph
        self.flow = 0
        self.edge_idx = edge_idx # Index of edge in the list of edges for node to
    def __repr__(self):
        return f"Edge(to: {self.to}, cap: {self.capacity}, flow: {self.flow}, edge_idx: {self.edge_idx})"


def read_data(file_path):
    # Load all lines
    with open(file_path, 'r') as f:
        lines = f.readlines()
    m, n = map(int, lines[0].split())

    customers = []
    for i in range(m):
        parts = list(map(int, lines[i+1].split()))
        l, u = parts[0], parts[1]
        products = parts[2:]
        customers.append((l, u, products))

    v = list(map(int, lines[-1].split()))

    return m, n, customers, v

def add_edge(graph, u, v, cap):
    # Forward edge: u -(0, 1)-> v
    forward = FlowEdge(v, cap, len(graph[v]))

    # Backward edge: v -(0)-> u
    backward = FlowEdge(u, 0, len(graph[u]))

    # Set edges in graph
    graph[u].append(forward)
    graph[v].append(backward)

def create_graph(customers, total_nodes, m, offset, S_idx, T_idx, S_dummy_idx, T_dummy_idx):
    # Define graph
    graph = [[] for _ in range(total_nodes)] # Initialize it as empty list to be able add edges as graph[u]
    # Define balances
    B = [0] * total_nodes

    # Create graph
    for i, customer in enumerate(customers):
        # print(customer)
        l = customer[0]
        u = customer[1]
        products = customer[2]
        
        customer_idx = offset + i
        # Add edge from S to customer
        add_edge(graph, S_idx, customer_idx, u - l)

        for product in products:
            product_idx = offset + m + product - 1
            add_edge(graph, customer_idx, product_idx, 1)
            # Update balance of products
        # Update balance of customer               
        B[customer_idx] += l
        # Update balance of start node               
        B[S_idx] -= l
    
    # Update balances for minimum product reviews (v)
    for i, v_value in enumerate(v):
        # Update balance for T node
        B[T_idx] += v_value
        # Update balance for product
        product_idx = offset + m + i
        B[product_idx] -= v_value

        # Add edge product_i --> T
        add_edge(graph, product_idx, T_idx, m - v_value)

    # Add the return edge from T to S
    add_edge(graph, T_idx, S_idx, float("inf"))

    total_balance = 0
    for i, b in enumerate(B):
        if b > 0:
            add_edge(graph, S_dummy_idx, i, b)
            total_balance += b
        elif b < 0:
            add_edge(graph, i, T_dummy_idx, abs(b))
    
    return graph, total_balance

def bfs(graph, s:int, t:int):
    path = [-1] * len(graph)
    q = [s]
    path[s] = None # Mark parent as visited

    while q:
        current = q.pop(0)
        neighbours = graph[current]

        for i, neighbour in enumerate(neighbours):
            # Go to only unvisited nodes
            if path[neighbour.to] == -1:
                # Skip edges that have available flow less than or equal to 0 
                available_flow = neighbour.capacity - neighbour.flow
                if available_flow <= 0:
                    continue
                # Update parent / mark as visited
                path[neighbour.to] = (current, i)
                if neighbour.to == t:
                    return path
                # Add neighbour node to queue
                q.append(neighbour.to)
    return None

def find_bottleneck(graph, s, t, path):
    bottle_neck = float('inf')
    # curr_idx = T_dummy_idx
    curr_idx = t
    # while curr_idx != S_dummy_idx:
    while curr_idx != s:
        parent_idx, edge_idx = path[curr_idx]
        edge = graph[parent_idx][edge_idx]
        available_capacity = edge.capacity - edge.flow
        bottle_neck = min(bottle_neck, available_capacity)
        curr_idx = parent_idx
    return bottle_neck

def update_edges_with_bottleneck(graph, s, t, bottle_neck, path):
    curr_idx = t
    while curr_idx != s:
        parent_idx, edge_idx = path[curr_idx]
        edge = graph[parent_idx][edge_idx]
        # Upload flow in forward edge
        graph[parent_idx][edge_idx].flow += bottle_neck
        # Upload flow in backward edge
        edge = graph[parent_idx][edge_idx]
        graph[curr_idx][edge.edge_idx].flow -= bottle_neck
        curr_idx = parent_idx

def edmonds_karp(graph, s, t):
    max_flow = 0
    while True:
        # 1. Find path
        path = bfs(graph, s, t)
        if not path:
            # No more paths, end
            break
        # 2. Find the bottleneck
        bottle_neck = find_bottleneck(graph, s, t, path)
        max_flow += bottle_neck
        # 3. Add bottlenect to flow of edge
        update_edges_with_bottleneck(graph, s, t, bottle_neck, path)
    return max_flow

def process_results(graph, m, offset):
    solutions = []
    for c_i in range(m):
        solution = []
        for edge in graph[c_i + offset]:
            if edge.flow == 1:
                product_number = edge.to - offset - m + 1
                solution.append(product_number)
        solution.sort()
        solutions.append(solution)
    return solutions

def write_data(file_path, solutions):
    with open(file_path, 'w') as f:
        for sol in solutions:
            output_string = " ".join(str(x) for x in sol)
            f.write(output_string + "\n")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # m --> number of customers
    # n --> number of products
    m, n, customers, v = read_data(input_path)

    # Node indices
    S_idx, T_idx = 0, 1
    S_dummy_idx, T_dummy_idx = 2, 3
    offset = 4
    total_nodes = 4 + m + n

    graph, total_balance = create_graph(customers, total_nodes, m, offset, S_idx, T_idx, S_dummy_idx, T_dummy_idx)

    # total_demand was the sum of positive balances B[v]
    flow_p1 = edmonds_karp(graph, S_dummy_idx, T_dummy_idx)

    solutions = []
    if flow_p1 < total_balance:
        solutions = [[-1]]
    else:
        flow_p2 = edmonds_karp(graph, S_idx, T_idx)
        solutions = process_results(graph, m, offset)
    
    write_data(output_path, solutions)
    
