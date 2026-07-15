#!/usr/bin/env python3

import argparse
import gurobipy as g
import numpy as np

# The 'graph' is a list where each index corresponds to a node ID
   # graph = [
    #     [], # 0: S (Source)
    #     [], # 1: T (Sink)
    #     [], # 2: k 1
    #     [], # 3: k 2
    #     [], # 4: k 3
    #     ...
    #     [], # n: k n
    #     [], # n+1: k+1 1
    #     [], # n+2: k+1 2
    #     [], # n+3: k+1 3
    #     ...
    #     [], # n+n: k+1 n
    #     [], S' (Source dummy)
    # ]

class FlowEdge:
    def __init__(self, to, capacity, cost, edge_idx):
        self.to = to
        self.capacity = capacity
        self.cost = cost
        self.flow = 0
        self.edge_idx = edge_idx
    def __repr__(self):
        return f"Edge(to: {self.to}, cap: {self.capacity}, flow: {self.flow}, cost: {self.cost} edge_idx: {self.edge_idx})"


def read_data(file_path):
    # Load all lines
    with open(file_path, 'r') as f:
        lines = f.readlines()
    n, p = map(int, lines[0].split())

    frames = []
    for i in range(p):
        line = list(map(int, lines[i+1].split()))
        frame = [(line[j], line[j+1]) for j in range(0, len(line), 2)]
        frames.append(frame)

    return n, p, frames

def compute_euclidean_dist(v1, v2):
    return np.sqrt((v2[0] - v1[0])**2 + (v2[1] - v1[1])**2) 

def compute_distance_matrix(frame, frame_next):
    n = len(frame)
    D = [[0.0 for _ in range(n)] for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            dist = compute_euclidean_dist(frame[i], frame_next[j])
            D[i][j] = dist
            
    return D

def add_edge(graph, u, v, cost):
    # Forward edge: u -(0, 1)-> v
    forward = FlowEdge(v, 1, cost, len(graph[v]))

    # Backward edge: v -(0)-> u
    backward = FlowEdge(u, 0, -cost, len(graph[u]))

    # Set edges in graph
    graph[u].append(forward)
    graph[v].append(backward)

def create_graph(frame, frame_next, total_nodes, offset, S_idx, T_idx, D):
    # Define graph
    graph = [[] for _ in range(total_nodes)] # Initialize it as empty list to be able add edges as graph[u]

    # Create graph
    for i, position in enumerate(frame):
        position_idx = offset + i
        # Add edge from S to customer
        add_edge(graph, S_idx, position_idx, 0)

        for j, position_next in enumerate(frame_next):
            position_next_idx = offset + n + j
            add_edge(graph, position_idx, position_next_idx, D[i][j])
    
    for i, position_next in enumerate(frame_next):
            position_next_idx = offset + n + i
            add_edge(graph, position_next_idx, T_idx, 0)
    
    return graph

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
    curr_idx = t
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

def find_negative_cycle(graph, total_nodes):
    dist = [0] * total_nodes
    parent_node = [-1] * total_nodes
    parent_edge_idx = [-1] * total_nodes

    # Last node variable tracks the last node which is reachable from negative cycle
    # WARNING: the last node does not have to be necessary in the negative loop  
    last_node = -1
    # 1. Update table of costs
    # Number of repetition of full graph traverser
    for i in range(total_nodes):
        last_node = -1
        # Go from node 0 up to last node
        for u in range(total_nodes):
            # print(f"For node: {u}")
            for j, edge in enumerate(graph[u]):
                if edge.capacity - edge.flow <= 0:
                    continue
                if dist[edge.to] > dist[u] + edge.cost:
                    dist[edge.to] = dist[u] + edge.cost
                    parent_node[edge.to] = u
                    parent_edge_idx[edge.to] = j
                    last_node = edge.to
            # print("Distance: ", dist)
            # print("Parents: ", parent_node)
    
    if last_node == -1:
        # print("No negative cycle")
        return None

    # print("Distance: ", dist)
    # print("Parents: ", parent_node)
    # print("Parents edge idx: ", parent_edge_idx)
    # print("Last node: ", last_node)
    
    # Backtrack V times to guarantee we are inside the cycle loop
    for _ in range(total_nodes):
        last_node = parent_node[last_node]

    # print("Updated last node: ", last_node)

    # Recreate cycle
    cycle_testing = []
    cycle = []
    curr = last_node
    while(True):
        cycle_testing.append((parent_node[curr], curr))
        # cycle_testing.append((curr, parent_node[curr]))
        cycle.append((parent_node[curr], parent_edge_idx[curr]))
        curr = parent_node[curr]
        if curr == last_node:
            break
    cycle_testing.reverse()
    cycle.reverse()
    # print(cycle_testing)
    # print(cycle)
    return cycle

def augment_cycle(graph, cycle):
    for cycle_edge in cycle:
        node = cycle_edge[0]
        edge_idx = cycle_edge[1]
        # Update cycle forward edge
        graph[node][edge_idx].flow += 1
        # Update cycle backward edge
        to_idx = graph[node][edge_idx].to
        edge_idx_backward = graph[node][edge_idx].edge_idx
        graph[to_idx][edge_idx_backward].flow -= 1

def cycle_cancelling(graph, total_nodes):
    # Add one node to total nodes because we added S dummy
    total_nodes += 1
    while True:
        # 1. Run bellman ford algorithm for finding negative cycle
        cycle = find_negative_cycle(graph, total_nodes)
        # 2. If no negative cycle exists, we have reached the minimum cost
        if cycle == None:
            break    
        # 3. Cancel the cycle: augment flow along the cycle
        augment_cycle(graph, cycle)

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

def print_graph(graph):
    for i, node in enumerate(graph):
        print(f"{i}: {node}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # n --> number of positions
    # p --> number of frames
    n, p, frames = read_data(input_path)
    # print("n", n)
    # print("p", p)
    # print("frames", frames)

    # Node indices
    S_idx, T_idx = 0, 1
    offset = 2
    total_nodes = offset + n + n
    S_dummy_idx = total_nodes
    outputs = []

    for i in range(len(frames) - 1):
        # if i < len(frames) - 2:
        #     continue
        # print(f"Iteration: {i}.")
        # print(frames[i])
        # print(frames[i+1])
        frame = frames[i]
        frame_next = frames[i+1]

        # 1. Compute distance matrix
        D = compute_distance_matrix(frame, frame_next)
        # if i == 3:
        #     for d in D:
        #         print(d)
        # 2. Create graph for ford-fulkerson
        graph = create_graph(frame, frame_next, total_nodes, offset, S_idx, T_idx, D)
        # print_graph(graph)
        # 3. Compute first feasible solution
        max_flow = edmonds_karp(graph, S_idx, T_idx)
        # print_graph(graph)
        # print(max_flow)
        # 4. Run Cycle cancelling - construct residual graph
        S_dummy_edges = []
        for v in range(len(graph)):
            forward = FlowEdge(v, 0, 0, len(S_dummy_edges))
            S_dummy_edges.append(forward)
        # print(S_dummy_edges)
        graph.append(S_dummy_edges)
        # print_graph(graph)
        # 5. Run Cycle cancelling - run bellman ford algorithm
        cycle_cancelling(graph, total_nodes)
        # print_graph(graph)
        # 6. Get flow
        output = []
        for i in range(n):
            edges = graph[i + offset]
            for edge in edges:
                if edge.flow == 1:
                    output.append(edge.to - n - 1)
                    # print(edge.to - n - 1)
                    # print(edge)
        # print(output)
        outputs.append(output)
        # break

    write_data(output_path, outputs)
    
