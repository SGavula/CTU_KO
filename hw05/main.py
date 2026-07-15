#!/usr/bin/env python3

import argparse
import gurobipy as g
import numpy as np


def read_data(file_path):
    # Load all lines
    with open(file_path, 'r') as f:
        lines = f.readlines()
    n = int(lines[0])

    tasks = []
    for i in range(n):
        p, r, d = lines[i+1].split()
        task = {"time": int(p), "start": int(r), "deadline": int(d)}
        tasks.append(task)

    return n, tasks

def is_missed_deadline(unscheduled_tasks, tasks, c_current):
    for i, is_scheduled in enumerate(unscheduled_tasks):
        if is_scheduled == False:
            p = tasks[i]["time"]
            d = tasks[i]["deadline"]
            if c_current + p > d:
                return True
    return False

def check_lb(unscheduled_tasks, tasks, c_current, c_max):
    # Compute help
    r_min = float("inf")
    d_max = float("-inf")
    p_sum = 0
    remaining_task = False

    for i, is_scheduled in enumerate(unscheduled_tasks):
        if is_scheduled == False:
            remaining_task = True
            task = tasks[i]
            p_sum += task["time"]
            r_min = min(r_min, task["start"])
            d_max = max(d_max, task["deadline"])
    
    if not remaining_task:
        return False

    # Compute lower bound
    lb = max(c_current, r_min) + p_sum
    
    if r_min == float("inf"):
        lb = c_current + p_sum

    if c_max != float("inf"):
        # Full solution
        return lb >= c_max
    else:
        # Partial solution
        return lb > d_max


def compute_decomposition(c_current, unscheduled_tasks, tasks):
    r_min = float("inf")
    for i, is_scheduled in enumerate(unscheduled_tasks):
        if is_scheduled == False:
            r_min = min(r_min, tasks[i]["start"])
    return c_current <= r_min

def backtrack(n, current_path, unscheduled_tasks, tasks, c_current, c_max, start_times, best_schedule_found):
    if len(current_path) >= n:
        if c_current < c_max:
            return c_current, list(start_times), False
        return c_max, best_schedule_found, False
    
    lower_bound_prune = check_lb(unscheduled_tasks, tasks, c_current, c_max)

    for i in range(n):
        # Check if the task is already schedule
        if unscheduled_tasks[i] == False:
            # Update time
            task = tasks[i]
            s = max(c_current, task["start"])
            c_new = s + task["time"]
            
            # Schedule the task
            current_path.append(i)
            # Mark that task i is scheduled
            unscheduled_tasks[i] = True
            original_start = start_times[i]
            start_times[i] = s

            # Check conditions
            missed_deadline = is_missed_deadline(unscheduled_tasks, tasks, c_new)
            decomposition = compute_decomposition(c_new, unscheduled_tasks, tasks)

            # Backtrack
            if missed_deadline == False and lower_bound_prune == False:
                c_max, best_schedule_found, child_decomp = backtrack(n, current_path, unscheduled_tasks, tasks, c_new, c_max, start_times, best_schedule_found)

            # Undo changes
            unscheduled_tasks[i] = False
            current_path.pop()
            start_times[i] = original_start

            if missed_deadline == False and lower_bound_prune == False:
                if decomposition or child_decomp:
                    return c_max, best_schedule_found, True

    return c_max, best_schedule_found, False

def write_data(file_path, solutions):
    with open(file_path, 'w') as f:
        output_string = "".join(str(x) + "\n" for x in solutions)
        f.write(output_string)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to the input text file")
    parser.add_argument("output", help="Path to the output text file")
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output

    # n --> number of processors
    n, tasks = read_data(input_path)

    current_path = []
    unscheduled_tasks = [False for _ in range(n)]
    c_max = float("inf")
    start_times = [0 for _ in range(n)]

    c_max, best_schedule_found, _ = backtrack(n, current_path, unscheduled_tasks, tasks, 0, c_max, start_times, None)
        
    if not best_schedule_found:
        best_schedule_found = [-1]
    write_data(output_path, best_schedule_found)
    
