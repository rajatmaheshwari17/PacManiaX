"""
In this file, you will implement generic search algorithms which are called by Pacman agents.
"""

from pacai.util.queue import Queue
from pacai.util.priorityQueue import PriorityQueue

def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first [p 85].

    Your search algorithm needs to return a list of actions that reaches the goal.
    Make sure to implement a graph search algorithm [Fig. 3.7].

    To get started, you might want to try some of these simple commands to
    understand the search problem that is being passed in:
    ```
    print("Start: %s" % (str(problem.startingState())))
    print("Is the start a goal?: %s" % (problem.isGoal(problem.startingState())))
    print("Start's successors: %s" % (problem.successorStates(problem.startingState())))
    ```
    """
    stack = []
    visited = set()
    start = problem.startingState()
    stack.append((start, [], 0))

    while stack:
        current_state, path, cost = stack.pop()
        if current_state in visited:
            continue
        visited.add(current_state)
        if problem.isGoal(current_state):
            return path
        for next_state, action, next_cost in problem.successorStates(current_state):
            if next_state not in visited:
                stack.append((next_state, path + [action], cost + next_cost))
    
    return []

def breadthFirstSearch(problem):
    """
    Search the shallowest nodes in the search tree first. [p 81]
    """
    queue = Queue()
    visited = set()
    start = problem.startingState()
    queue.push((start, [], 0))
    
    while not queue.isEmpty():
        current_state, path, cost = queue.pop()
        if current_state in visited:
            continue
        visited.add(current_state)
        if problem.isGoal(current_state):
            return path
        for next_state, action, next_cost in problem.successorStates(current_state):
            if next_state not in visited:
                queue.push((next_state, path + [action], cost + next_cost))
    
    return []

def uniformCostSearch(problem):
    """
    Search the node of least total cost first.
    """
    pq = PriorityQueue()
    visited = set()
    start = problem.startingState()
    pq.push((start, [], 0), 0)
    
    while not pq.isEmpty():
        current_state, path, cost = pq.pop()
        if current_state in visited:
            continue
        visited.add(current_state)
        if problem.isGoal(current_state):
            return path
        for next_state, action, next_cost in problem.successorStates(current_state):
            if next_state not in visited:
                new_cost = cost + next_cost
                pq.push((next_state, path + [action], new_cost), new_cost)
    
    return []

def aStarSearch(problem, heuristic):
    """
    Search the node that has the lowest combined cost and heuristic first.
    """
    pq = PriorityQueue()
    visited = set()
    start = problem.startingState()
    pq.push((start, [], 0), 0)
    
    while not pq.isEmpty():
        current_state, path, cost = pq.pop()
        if current_state in visited:
            continue
        visited.add(current_state)
        if problem.isGoal(current_state):
            return path
        for next_state, action, next_cost in problem.successorStates(current_state):
            if next_state not in visited:
                new_cost = cost + next_cost
                priority = new_cost + heuristic(next_state, problem)
                pq.push((next_state, path + [action], new_cost), priority)
    
    return []
