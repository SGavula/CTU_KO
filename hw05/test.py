def backtrack(n, current_path, unscheduled_tasks, tasks, c_current, c_max, start_times, best_schedule_found):
    if len(current_path) >= n:
        if c_current < c_max:
            # Vracíme: cena, rozvrh, dekompozice_aktivni (zde False)
            return c_current, list(start_times), False
        return c_max, best_schedule_found, False
    
    # Lokální proměnné pro sledování nejlepšího výsledku v této úrovni
    local_best_c = c_max
    local_best_schedule = best_schedule_found
    
    # Pravidlo 3: Dekompozice - zkontrolujte před smyčkou pro efektivitu
    # Pokud c_current <= min(r_j všech nezařazených), stačí zkusit jen jeden úkol.
    is_decomposed_node = compute_decomposition(c_current, unscheduled_tasks, tasks)

    for i in range(n):
        if not unscheduled_tasks[i]:
            task = tasks[i]
            s = max(c_current, task["start"])
            c_new = s + task["time"]
            
            # Pravidlo 2 (Lower Bound): Přesuňte SEM, aby se počítalo s c_new!
            if check_lb(unscheduled_tasks, tasks, c_new, local_best_c):
                continue

            if not is_missed_deadline(unscheduled_tasks, tasks, c_new):
                # Provedení kroku
                unscheduled_tasks[i] = True
                current_path.append(i)
                original_start = start_times[i]
                start_times[i] = s

                # REKURZE: vrací i informaci o dekompozici
                local_best_c, local_best_schedule, child_decomposed = backtrack(
                    n, current_path, unscheduled_tasks, tasks, c_new, 
                    local_best_c, start_times, local_best_schedule
                )

                # Zpětný chod
                unscheduled_tasks[i] = False
                current_path.pop()
                start_times[i] = original_start

                # --- KLÍČOVÁ ZMĚNA PRO PRAVIDLO 3 ---
                # Pokud byla dekompozice splněna u dítěte NEBO platí zde v uzlu
                if child_decomposed or is_decomposed_node:
                    # Přestaneme zkoušet další sourozence v této smyčce
                    # a propagujeme informaci nahoru (True)
                    return local_best_c, local_best_schedule, True

    return local_best_c, local_best_schedule, False