'''
from pacai.agents.capture.capture import CaptureAgent
from pacai.core.directions import Directions
from pacai.util.priorityQueue import PriorityQueue

def betterHeuristic(pos, goal, gameState):
    x1, y1 = int(pos[0]), int(pos[1])
    x2, y2 = int(goal[0]), int(goal[1])
    base = abs(x1 - x2) + abs(y1 - y2)
    walls = gameState.getWalls()
    wallPenalty = 0
    
    for i in range(min(x1, x2), max(x1, x2) + 1):
        for j in range(min(y1, y2), max(y1, y2) + 1):
            if walls[i][j]:
                wallPenalty += 2
                
    return base + wallPenalty

class SearchProblem:
    def __init__(self, gameState, start, goal, walls):
        self.startState = (int(start[0]), int(start[1]))
        self.goal = (int(goal[0]), int(goal[1]))
        self.walls = walls
        self.costFn = lambda x: 1
        
    def startingState(self):
        return self.startState
        
    def isGoal(self, state):
        return state == self.goal
        
    def successorStates(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x, y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append((nextState, action, cost))
        return successors

class Actions:
    @staticmethod
    def directionToVector(action):
        if action == Directions.NORTH:
            return (0, 1)
        if action == Directions.SOUTH:
            return (0, -1)
        if action == Directions.EAST:
            return (1, 0)
        if action == Directions.WEST:
            return (-1, 0)
        return (0, 0)

class OffensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls.getWidth()
        self.height = self.walls.getHeight()
        self.safeZone = self.width // 2 - 1 if self.red else self.width // 2
        self.foodCarried = 0
        self.maxFoodCarry = 4
        self.retreatThreshold = 3
        self.teamIndex = None
        self.isTopAgent = None
        self.currentTarget = None
        self.pathToTarget = []

    def chooseAction(self, gameState):
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]
            self.isTopAgent = self.index < self.teamIndex

        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        dangerousGhosts = [g for g in ghosts if self.getMazeDistance(myPos, g.getPosition()) <= 2]

        if self.foodCarried >= self.maxFoodCarry or dangerousGhosts:
            self.currentTarget = None
            self.pathToTarget = []
            return self.returnToSafeZone(gameState, actions)

        foodList = self.getFood(gameState).asList()
        
        if len(foodList) == 1:
            target = foodList[0]
            self.currentTarget = target
            problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
            if path:
                return path[0]
            return actions[0]

        teammateState = gameState.getAgentState(self.teamIndex)
        teammatePos = gameState.getAgentPosition(self.teamIndex)
        
        midY = self.height // 2
        if self.isTopAgent:
            zoneFood = [food for food in foodList if food[1] >= midY]
            otherZoneFood = [food for food in foodList if food[1] < midY]
        else:
            zoneFood = [food for food in foodList if food[1] < midY]
            otherZoneFood = [food for food in foodList if food[1] >= midY]

        safeFood = []
        for food in zoneFood:
            isSafe = True
            for ghost in ghosts:
                if self.getMazeDistance(food, ghost.getPosition()) < 3:
                    isSafe = False
                    break
            if isSafe:
                safeFood.append(food)

        if not safeFood:
            safeFood = []
            for food in otherZoneFood:
                isSafe = True
                for ghost in ghosts:
                    if self.getMazeDistance(food, ghost.getPosition()) < 3:
                        isSafe = False
                        break
                if isSafe:
                    safeFood.append(food)

        if self.currentTarget and self.currentTarget in safeFood:
            target = self.currentTarget
        else:
            if safeFood:
                teammate_target = None
                other_agent = gameState.getAgentState(self.teamIndex)
                if other_agent:
                    teammate_pos = other_agent.getPosition()
                    if teammate_pos:
                        possible_targets = [(self.getMazeDistance(teammate_pos, food), food) for food in safeFood]
                        if possible_targets:
                            teammate_target = min(possible_targets)[1]

                if teammate_target:
                    filtered_food = [food for food in safeFood if food != teammate_target]
                else:
                    filtered_food = safeFood

                if filtered_food:
                    target = min(filtered_food, key=lambda x: self.getMazeDistance(myPos, x))
                elif safeFood:
                    target = min(safeFood, key=lambda x: self.getMazeDistance(myPos, x))
                else:
                    return self.returnToSafeZone(gameState, actions)
            else:
                return self.returnToSafeZone(gameState, actions)

        self.currentTarget = target
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        
        if path:
            return path[0]
        return actions[0]

    def returnToSafeZone(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        safeX = self.safeZone
        safeY = myPos[1]
        
        safePoints = []
        for y in range(1, self.height - 1):
            if not gameState.hasWall(safeX, y):
                safePoints.append((safeX, y))
                
        if safePoints:
            target = min(safePoints, key=lambda p: self.getMazeDistance(myPos, p))
            problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
            if path:
                return path[0]
                
        return actions[0]

    def aStarSearch(self, problem, heuristic):
        pq = PriorityQueue()
        visited = set()
        start = problem.startingState()
        pq.push((start, [], 0), 0)
        
        while not pq.isEmpty():
            current_state, path, cost = pq.pop()
            
            if problem.isGoal(current_state):
                return path
                
            if current_state not in visited:
                visited.add(current_state)
                for next_state, action, next_cost in problem.successorStates(current_state):
                    if next_state not in visited:
                        new_cost = cost + next_cost
                        new_path = path + [action]
                        priority = new_cost + heuristic(next_state)
                        pq.push((next_state, new_path, new_cost), priority)
        return []

def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        OffensiveAgent(secondIndex)
    ]
'''
'''
from pacai.agents.capture.capture import CaptureAgent
from pacai.core.directions import Directions
from pacai.util.priorityQueue import PriorityQueue
import time

def betterHeuristic(pos, goal, gameState):
    x1, y1 = int(pos[0]), int(pos[1])
    x2, y2 = int(goal[0]), int(goal[1])
    base = abs(x1 - x2) + abs(y1 - y2)
    walls = gameState.getWalls()
    wallPenalty = 0
    
    for i in range(min(x1, x2), max(x1, x2) + 1):
        for j in range(min(y1, y2), max(y1, y2) + 1):
            if walls[i][j]:
                wallPenalty += 2
                
    return base + wallPenalty

class SearchProblem:
    def __init__(self, gameState, start, goal, walls):
        self.startState = (int(start[0]), int(start[1]))
        self.goal = (int(goal[0]), int(goal[1]))
        self.walls = walls
        self.costFn = lambda x: 1
        
    def startingState(self):
        return self.startState
        
    def isGoal(self, state):
        return state == self.goal
        
    def successorStates(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x, y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append((nextState, action, cost))
        return successors

class Actions:
    @staticmethod
    def directionToVector(action):
        if action == Directions.NORTH:
            return (0, 1)
        if action == Directions.SOUTH:
            return (0, -1)
        if action == Directions.EAST:
            return (1, 0)
        if action == Directions.WEST:
            return (-1, 0)
        return (0, 0)

class OffensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls.getWidth()
        self.height = self.walls.getHeight()
        self.safeZone = self.width // 2 - 1 if self.red else self.width // 2
        self.foodCarried = 0
        self.maxFoodCarry = 4
        self.retreatThreshold = 3
        self.teamIndex = None
        self.isTopAgent = None
        self.currentTarget = None
        self.lastPos = None
        self.borderPatrolThreshold = 2  # Distance to check for border patrol
        self.powerPelletThreshold = 4   # Distance to consider going for power pellet
        self.deadEndThreshold = 1       # Number of escape routes needed to avoid dead end

    def isInDeadEnd(self, pos, gameState):
        """Check if a position is in or leads to a dead end"""
        x, y = int(pos[0]), int(pos[1])
        escapeRoutes = 0
        visited = set()
        
        def countExits(x, y, depth=0):
            if depth > 5:  # Look ahead up to 5 steps
                return 1
            if (x, y) in visited:
                return 0
            visited.add((x, y))
            
            exits = 0
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nextX, nextY = x + dx, y + dy
                if not gameState.hasWall(nextX, nextY):
                    if (nextX == self.safeZone and self.red) or \
                       (nextX == self.safeZone + 1 and not self.red):
                        exits += 1
                    else:
                        exits += countExits(nextX, nextY, depth + 1)
            return exits
        
        return countExits(x, y) < self.deadEndThreshold

    def isBorderPatrolled(self, gameState):
        """Check if opponent ghost is patrolling the border"""
        myPos = gameState.getAgentPosition(self.index)
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        
        borderX = self.safeZone + 1 if self.red else self.safeZone
        for ghost in ghosts:
            ghostPos = ghost.getPosition()
            if abs(ghostPos[0] - borderX) <= self.borderPatrolThreshold:
                if self.getMazeDistance(myPos, ghostPos) <= self.borderPatrolThreshold:
                    return True
        return False

    def isGhostApproaching(self, gameState, direction):
        """Check if ghost is approaching from a specific direction"""
        if not self.lastPos:
            return False
            
        myPos = gameState.getAgentPosition(self.index)
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        
        # Get current movement vector
        currentDir = (myPos[0] - self.lastPos[0], myPos[1] - self.lastPos[1])
        
        for ghost in ghosts:
            ghostPos = ghost.getPosition()
            # Check if ghost is in front relative to our movement
            if direction == 'front':
                if (currentDir[0] > 0 and ghostPos[0] > myPos[0]) or \
                   (currentDir[0] < 0 and ghostPos[0] < myPos[0]) or \
                   (currentDir[1] > 0 and ghostPos[1] > myPos[1]) or \
                   (currentDir[1] < 0 and ghostPos[1] < myPos[1]):
                    return True
        return False

    def chooseAction(self, gameState):
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]
            self.isTopAgent = self.index < self.teamIndex

        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        # Check for immediate threats
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        dangerousGhosts = [g for g in ghosts if self.getMazeDistance(myPos, g.getPosition()) <= self.retreatThreshold]

        # Check if ghost approaching from front
        if self.isGhostApproaching(gameState, 'front'):
            self.currentTarget = None  # Reset current target to force new path selection

        # Check for border patrol
        if not gameState.getAgentState(self.index).isPacman and self.isBorderPatrolled(gameState):
            return self.waitForOpening(gameState, actions)

        # Check if we should go for power pellet
        if dangerousGhosts:
            capsules = self.getCapsules(gameState)
            if capsules:
                closestCapsule = min(capsules, key=lambda x: self.getMazeDistance(myPos, x))
                if self.getMazeDistance(myPos, closestCapsule) <= self.powerPelletThreshold:
                    return self.goToPowerPellet(gameState, closestCapsule, actions)

        # If carrying enough food or in danger, return to safe zone
        if self.foodCarried >= self.maxFoodCarry or dangerousGhosts:
            self.currentTarget = None
            return self.returnToSafeZone(gameState, actions)

        # Get food list and divide into zones
        foodList = self.getFood(gameState).asList()
        
        # If only one food pellet left, both agents can target it
        if len(foodList) == 1:
            target = foodList[0]
            self.currentTarget = target
            return self.getActionToTarget(gameState, target, actions)

        # Define zones
        midY = self.height // 2
        if self.isTopAgent:
            zoneFood = [food for food in foodList if food[1] >= midY]
            otherZoneFood = [food for food in foodList if food[1] < midY]
        else:
            zoneFood = [food for food in foodList if food[1] < midY]
            otherZoneFood = [food for food in foodList if food[1] >= midY]

        # Filter out dangerous food and dead ends
        safeFood = []
        for food in zoneFood:
            if not self.isInDeadEnd(food, gameState):
                isSafe = True
                for ghost in ghosts:
                    if self.getMazeDistance(food, ghost.getPosition()) < 3:
                        isSafe = False
                        break
                if isSafe:
                    safeFood.append(food)

        # If no safe food in our zone, look at other zone
        if not safeFood:
            for food in otherZoneFood:
                if not self.isInDeadEnd(food, gameState):
                    isSafe = True
                    for ghost in ghosts:
                        if self.getMazeDistance(food, ghost.getPosition()) < 3:
                            isSafe = False
                            break
                    if isSafe:
                        safeFood.append(food)

        # Choose target
        if not safeFood:
            return self.returnToSafeZone(gameState, actions)

        # If current target is still valid, keep it
        if self.currentTarget and self.currentTarget in safeFood and \
           not self.isGhostApproaching(gameState, 'front'):
            target = self.currentTarget
        else:
            # Filter out teammate's likely target
            teammate_pos = gameState.getAgentPosition(self.teamIndex)
            if teammate_pos:
                safeFood = [food for food in safeFood if 
                           self.getMazeDistance(myPos, food) < self.getMazeDistance(teammate_pos, food)]
            
            if safeFood:
                target = min(safeFood, key=lambda x: self.getMazeDistance(myPos, x))
            else:
                return self.returnToSafeZone(gameState, actions)

        self.currentTarget = target
        action = self.getActionToTarget(gameState, target, actions)
        self.lastPos = myPos
        return action

    def waitForOpening(self, gameState, actions):
        """Wait in a safe position until border patrol moves away"""
        myPos = gameState.getAgentPosition(self.index)
        safeSpots = []
        
        # Find safe waiting spots near our border
        for y in range(1, self.height - 1):
            spotX = self.safeZone - 1 if self.red else self.safeZone + 1
            if not gameState.hasWall(spotX, y):
                safeSpots.append((spotX, y))
                
        if safeSpots:
            target = min(safeSpots, key=lambda x: self.getMazeDistance(myPos, x))
            return self.getActionToTarget(gameState, target, actions)
        return actions[0]

    def goToPowerPellet(self, gameState, capsule, actions):
        """Navigate to nearest power pellet"""
        return self.getActionToTarget(gameState, capsule, actions)

    def getActionToTarget(self, gameState, target, actions):
        """Get best action to reach target"""
        myPos = gameState.getAgentPosition(self.index)
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        
        if path:
            return path[0]
        return actions[0]

    def returnToSafeZone(self, gameState, actions):
        """Return to safe zone using safest path"""
        myPos = gameState.getAgentPosition(self.index)
        safePoints = []
        safeX = self.safeZone
        
        # Find all possible safe return points
        for y in range(1, self.height - 1):
            if not gameState.hasWall(safeX, y) and \
               not self.isInDeadEnd((safeX, y), gameState):
                safePoints.append((safeX, y))
                
        if safePoints:
            # Choose closest safe point that's not near a ghost
            opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
            ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
            
            safestPoints = []
            for point in safePoints:
                isSafe = True
                for ghost in ghosts:
                    if self.getMazeDistance(point, ghost.getPosition()) < self.retreatThreshold:
                        isSafe = False
                        break
                if isSafe:
                    safestPoints.append(point)
            
            if safestPoints:
                target = min(safestPoints, key=lambda x: self.getMazeDistance(myPos, x))
            else:
                target = min(safePoints, key=lambda x: self.getMazeDistance(myPos, x))
                
            return self.getActionToTarget(gameState, target, actions)
                
        return actions[0]

    def aStarSearch(self, problem, heuristic):
        pq = PriorityQueue()
        visited = set()
        start = problem.startingState()
        pq.push((start, [], 0), 0)
        
        while not pq.isEmpty():
            current_state, path, cost = pq.pop()
            
            if problem.isGoal(current_state):
                return path
                
            if current_state not in visited:
                visited.add(current_state)
                for next_state, action, next_cost in problem.successorStates(current_state):
                    if next_state not in visited:
                        new_cost = cost + next_cost
                        new_path = path + [action]
                        priority = new_cost + heuristic(next_state)
                        pq.push((next_state, new_path, new_cost), priority)
        return []

def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        OffensiveAgent(secondIndex)
    ]
'''

from pacai.agents.capture.capture import CaptureAgent
from pacai.core.directions import Directions
from pacai.util.priorityQueue import PriorityQueue
import time

def betterHeuristic(pos, goal, gameState):
    x1, y1 = int(pos[0]), int(pos[1])
    x2, y2 = int(goal[0]), int(goal[1])
    base = abs(x1 - x2) + abs(y1 - y2)
    walls = gameState.getWalls()
    wallPenalty = 0
    
    for i in range(min(x1, x2), max(x1, x2) + 1):
        for j in range(min(y1, y2), max(y1, y2) + 1):
            if walls[i][j]:
                wallPenalty += 2
                
    return base + wallPenalty

class SearchProblem:
    def __init__(self, gameState, start, goal, walls, avoidUTurn=None):
        self.startState = (int(start[0]), int(start[1]))
        self.goal = (int(goal[0]), int(goal[1]))
        self.walls = walls
        self.costFn = lambda x: 1
        self.avoidUTurn = avoidUTurn  # Direction to avoid U-turn
        
    def startingState(self):
        return self.startState
        
    def isGoal(self, state):
        return state == self.goal
        
    def successorStates(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            # Avoid U-turn if specified
            if self.avoidUTurn:
                if (action == Directions.NORTH and self.avoidUTurn == Directions.SOUTH) or \
                   (action == Directions.SOUTH and self.avoidUTurn == Directions.NORTH) or \
                   (action == Directions.EAST and self.avoidUTurn == Directions.WEST) or \
                   (action == Directions.WEST and self.avoidUTurn == Directions.EAST):
                    continue
                    
            x, y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append((nextState, action, cost))
        return successors

class Actions:
    @staticmethod
    def directionToVector(action):
        if action == Directions.NORTH:
            return (0, 1)
        if action == Directions.SOUTH:
            return (0, -1)
        if action == Directions.EAST:
            return (1, 0)
        if action == Directions.WEST:
            return (-1, 0)
        return (0, 0)

    @staticmethod
    def getOppositeDirection(action):
        if action == Directions.NORTH:
            return Directions.SOUTH
        if action == Directions.SOUTH:
            return Directions.NORTH
        if action == Directions.EAST:
            return Directions.WEST
        if action == Directions.WEST:
            return Directions.EAST
        return action

class OffensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls.getWidth()
        self.height = self.walls.getHeight()
        self.safeZone = self.width // 2 - 1 if self.red else self.width // 2
        self.foodCarried = 0
        self.retreatThreshold = 3
        self.teamIndex = None
        self.isTopAgent = None
        self.currentTarget = None
        self.lastPos = None
        self.lastAction = None
        self.borderPatrolThreshold = 2
        self.powerPelletThreshold = 4
        self.deadEndThreshold = 1
        self.ghostBackThreshold = 5  # Distance to consider ghost as "behind"
    

    def isInDeadEnd(self, pos, gameState):
        """Check if a position is in or leads to a dead end"""
        x, y = int(pos[0]), int(pos[1])
        escapeRoutes = 0
        visited = set()
        
        def countExits(x, y, depth=0):
            if depth > 5:
                return 1
            if (x, y) in visited:
                return 0
            visited.add((x, y))
            
            exits = 0
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nextX, nextY = x + dx, y + dy
                if not gameState.hasWall(nextX, nextY):
                    if (nextX == self.safeZone and self.red) or \
                       (nextX == self.safeZone + 1 and not self.red):
                        exits += 1
                    else:
                        exits += countExits(nextX, nextY, depth + 1)
            return exits
        
        return countExits(x, y) < self.deadEndThreshold

    def isGhostBehind(self, gameState):
        """Check if non-scared ghost is behind the agent"""
        if not self.lastPos or not self.lastAction:
            return (False, None)
            
        myPos = gameState.getAgentPosition(self.index)
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None 
                 and a.getScaredTimer() == 0]  # Only consider non-scared ghosts
        
        opposite = Actions.getOppositeDirection(self.lastAction)
        dx, dy = Actions.directionToVector(opposite)
        behindPos = (myPos[0] + dx, myPos[1] + dy)
        
        for ghost in ghosts:
            ghostPos = ghost.getPosition()
            if self.getMazeDistance(behindPos, ghostPos) <= self.ghostBackThreshold:
                return (True, opposite)
        return (False, None)

    def isGhostApproaching(self, gameState, direction):
        """Check if non-scared ghost is approaching from a specific direction"""
        if not self.lastPos:
            return False
            
        myPos = gameState.getAgentPosition(self.index)
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None
                 and a.getScaredTimer() == 0]  # Only consider non-scared ghosts
        
        currentDir = (myPos[0] - self.lastPos[0], myPos[1] - self.lastPos[1])
        
        for ghost in ghosts:
            ghostPos = ghost.getPosition()
            if direction == 'front':
                if (currentDir[0] > 0 and ghostPos[0] > myPos[0]) or \
                   (currentDir[0] < 0 and ghostPos[0] < myPos[0]) or \
                   (currentDir[1] > 0 and ghostPos[1] > myPos[1]) or \
                   (currentDir[1] < 0 and ghostPos[1] < myPos[1]):
                    return True
        return False

    def isBorderPatrolled(self, gameState):
        """Check if non-scared opponent ghost is patrolling the border"""
        myPos = gameState.getAgentPosition(self.index)
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None
                 and a.getScaredTimer() == 0]  # Only consider non-scared ghosts
        
        borderX = self.safeZone + 1 if self.red else self.safeZone
        for ghost in ghosts:
            ghostPos = ghost.getPosition()
            if abs(ghostPos[0] - borderX) <= self.borderPatrolThreshold:
                if self.getMazeDistance(myPos, ghostPos) <= self.borderPatrolThreshold:
                    return True
        return False
    '''
    def chooseAction(self, gameState):
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]
            self.isTopAgent = self.index < self.teamIndex

        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        # Check for immediate threats
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None
                 and a.getScaredTimer() == 0]  # Only consider non-scared ghosts
        dangerousGhosts = [g for g in ghosts if self.getMazeDistance(myPos, g.getPosition()) <= self.retreatThreshold]

        # Check if ghost is behind
        ghostBehind, avoidDirection = self.isGhostBehind(gameState)

        # Check if ghost approaching from front
        if self.isGhostApproaching(gameState, 'front'):
            self.currentTarget = None

        # Check for border patrol
        if not gameState.getAgentState(self.index).isPacman and self.isBorderPatrolled(gameState):
            return self.waitForOpening(gameState, actions)

        # Get all food and capsules
        foodList = self.getFood(gameState).asList()
        capsules = self.getCapsules(gameState)
        allTargets = foodList + capsules  # Treat capsules as food

        # If only one target left, both agents can go for it
        if len(allTargets) == 1:
            target = allTargets[0]
            self.currentTarget = target
            return self.getActionToTarget(gameState, target, actions, avoidDirection if ghostBehind else None)

        # Define zones
        midY = self.height // 2
        if self.isTopAgent:
            zoneTargets = [t for t in allTargets if t[1] >= midY]
            otherZoneTargets = [t for t in allTargets if t[1] < midY]
        else:
            zoneTargets = [t for t in allTargets if t[1] < midY]
            otherZoneTargets = [t for t in allTargets if t[1] >= midY]

        # Filter out dangerous targets and dead ends
        safeTargets = []
        for target in zoneTargets:
            if not self.isInDeadEnd(target, gameState):
                isSafe = True
                for ghost in ghosts:
                    if self.getMazeDistance(target, ghost.getPosition()) < 3:
                        isSafe = False
                        break
                if isSafe:
                    safeTargets.append(target)

        # If no safe targets in our zone, look at other zone
        if not safeTargets:
            for target in otherZoneTargets:
                if not self.isInDeadEnd(target, gameState):
                    isSafe = True
                    for ghost in ghosts:
                        if self.getMazeDistance(target, ghost.getPosition()) < 3:
                            isSafe = False
                            break
                    if isSafe:
                        safeTargets.append(target)

        # Choose target
        if not safeTargets:
            return self.returnToSafeZone(gameState, actions, avoidDirection if ghostBehind else None)

        # If current target is still valid, keep it
        if self.currentTarget and self.currentTarget in safeTargets and \
           not self.isGhostApproaching(gameState, 'front'):
            target = self.currentTarget
        else:
            # Filter out teammate's likely target
            teammate_pos = gameState.getAgentPosition(self.teamIndex)
            if teammate_pos:
                safeTargets = [t for t in safeTargets if 
                              self.getMazeDistance(myPos, t) < self.getMazeDistance(teammate_pos, t)]
            
            if safeTargets:
                target = min(safeTargets, key=lambda x: self.getMazeDistance(myPos, x))

        self.currentTarget = target
        action = self.getActionToTarget(gameState, target, actions, avoidDirection if ghostBehind else None)
        self.lastPos = myPos
        self.lastAction = action
        return action
    '''

    def chooseAction(self, gameState):
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]
            self.isTopAgent = self.index < self.teamIndex

        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        # Get initial threats
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None
                 and a.getScaredTimer() == 0]
        dangerousGhosts = [g for g in ghosts if self.getMazeDistance(myPos, g.getPosition()) <= self.retreatThreshold]

        # Get ghost positions relative to current direction
        ghostBehind, avoidDirection = self.isGhostBehind(gameState)
        ghostInFront = self.isGhostApproaching(gameState, 'front')

        # If ghost in front, force a direction change
        if ghostInFront and self.lastAction:
            # Get the current direction vector
            dx, dy = Actions.directionToVector(self.lastAction)
            currentDir = (dx, dy)
            
            # Get valid escape directions (excluding current direction and its opposite)
            escapeActions = []
            for action in actions:
                newDx, newDy = Actions.directionToVector(action)
                # Don't continue in same direction or do a complete U-turn
                if (newDx, newDy) != currentDir and \
                   (newDx, newDy) != (-dx, -dy):
                    escapeActions.append(action)
            
            if escapeActions:
                # Find the escape action that leads to the safest position
                bestEscapeAction = None
                maxMinGhostDist = -1
                
                for action in escapeActions:
                    dx, dy = Actions.directionToVector(action)
                    nextPos = (myPos[0] + dx, myPos[1] + dy)
                    
                    # Calculate minimum distance to all ghosts from this position
                    minGhostDist = float('inf')
                    for ghost in ghosts:
                        ghostPos = ghost.getPosition()
                        dist = self.getMazeDistance(nextPos, ghostPos)
                        minGhostDist = min(minGhostDist, dist)
                    
                    # Keep track of the action that maximizes distance from ghosts
                    if minGhostDist > maxMinGhostDist:
                        maxMinGhostDist = minGhostDist
                        bestEscapeAction = action
                
                if bestEscapeAction:
                    # Reset current target and force the escape action
                    self.currentTarget = None
                    self.lastAction = bestEscapeAction
                    self.lastPos = myPos
                    return bestEscapeAction

        # Check for border patrol
        if not gameState.getAgentState(self.index).isPacman and self.isBorderPatrolled(gameState):
            return self.waitForOpening(gameState, actions)

        # Get all food and capsules
        foodList = self.getFood(gameState).asList()
        capsules = self.getCapsules(gameState)
        allTargets = foodList + capsules

        # If carrying enough food or in danger, return to safe zone

        # If only one target left, both agents can go for it
        if len(allTargets) == 1:
            target = allTargets[0]
            self.currentTarget = target
            return self.getActionToTarget(gameState, target, actions, avoidDirection if ghostBehind else None)

        # Define zones
        midY = self.height // 2
        if self.isTopAgent:
            zoneTargets = [t for t in allTargets if t[1] >= midY]
            otherZoneTargets = [t for t in allTargets if t[1] < midY]
        else:
            zoneTargets = [t for t in allTargets if t[1] < midY]
            otherZoneTargets = [t for t in allTargets if t[1] >= midY]

        # Filter out dangerous targets and dead ends
        safeTargets = []
        for target in zoneTargets:
            if not self.isInDeadEnd(target, gameState):
                isSafe = True
                for ghost in ghosts:
                    ghostPos = ghost.getPosition()
                    # If ghost in front, prefer targets in opposite direction
                    if ghostInFront:
                        targetDir = (target[0] - myPos[0], target[1] - myPos[1])
                        ghostDir = (ghostPos[0] - myPos[0], ghostPos[1] - myPos[1])
                        # Check if target is in roughly opposite direction from ghost
                        if (targetDir[0] * ghostDir[0] + targetDir[1] * ghostDir[1]) > 0:
                            isSafe = False
                    if self.getMazeDistance(target, ghostPos) < 3:
                        isSafe = False
                        break
                if isSafe:
                    safeTargets.append(target)

        # If no safe targets in our zone, look at other zone
        if not safeTargets:
            for target in otherZoneTargets:
                if not self.isInDeadEnd(target, gameState):
                    isSafe = True
                    for ghost in ghosts:
                        ghostPos = ghost.getPosition()
                        if ghostInFront:
                            targetDir = (target[0] - myPos[0], target[1] - myPos[1])
                            ghostDir = (ghostPos[0] - myPos[0], ghostPos[1] - myPos[1])
                            if (targetDir[0] * ghostDir[0] + targetDir[1] * ghostDir[1]) > 0:
                                isSafe = False
                        if self.getMazeDistance(target, ghostPos) < 3:
                            isSafe = False
                            break
                    if isSafe:
                        safeTargets.append(target)

        # If current target is still valid and no ghost in front, keep it
        if self.currentTarget and self.currentTarget in safeTargets and not ghostInFront:
            target = self.currentTarget
        else:
            # Filter out teammate's likely target
            teammate_pos = gameState.getAgentPosition(self.teamIndex)
            if teammate_pos:
                safeTargets = [t for t in safeTargets if 
                             self.getMazeDistance(myPos, t) < self.getMazeDistance(teammate_pos, t)]
            
            if safeTargets:
                target = min(safeTargets, key=lambda x: self.getMazeDistance(myPos, x))

        self.currentTarget = target
        action = self.getActionToTarget(gameState, target, actions, avoidDirection if ghostBehind else None)
        self.lastPos = myPos
        self.lastAction = action
        return action
    
    def waitForOpening(self, gameState, actions):
        """Wait in a safe position until border patrol moves away"""
        myPos = gameState.getAgentPosition(self.index)
        safeSpots = []
        
        for y in range(1, self.height - 1):
            spotX = self.safeZone - 1 if self.red else self.safeZone + 1
            if not gameState.hasWall(spotX, y):
                safeSpots.append((spotX, y))
                
        if safeSpots:
            target = min(safeSpots, key=lambda x: self.getMazeDistance(myPos, x))
            return self.getActionToTarget(gameState, target, actions)
        return actions[0]

    def getActionToTarget(self, gameState, target, actions, avoidDirection=None):
        """Get best action to reach target"""
        myPos = gameState.getAgentPosition(self.index)
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls(), avoidDirection)
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        
        if path:
            return path[0]
        return actions[0]

    def aStarSearch(self, problem, heuristic):
        """A* search to find optimal path to target"""
        pq = PriorityQueue()
        visited = set()
        start = problem.startingState()
        pq.push((start, [], 0), 0)
        
        while not pq.isEmpty():
            current_state, path, cost = pq.pop()
            
            if problem.isGoal(current_state):
                return path
                
            if current_state not in visited:
                visited.add(current_state)
                for next_state, action, next_cost in problem.successorStates(current_state):
                    if next_state not in visited:
                        new_cost = cost + next_cost
                        new_path = path + [action]
                        priority = new_cost + heuristic(next_state)
                        pq.push((next_state, new_path, new_cost), priority)
        return []

def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        OffensiveAgent(secondIndex)
    ]