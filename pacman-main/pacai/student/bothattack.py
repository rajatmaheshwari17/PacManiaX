from pacai.agents.capture.capture import CaptureAgent
import random
from pacai.core.directions import Directions
from pacai.util.priorityQueue import PriorityQueue

class SearchProblem:
    def __init__(self, gameState, start, goal, walls):
        self.startState = start
        self.goal = goal
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

class OffensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls._width
        self.height = self.walls._height
        self.safeZone = self.width // 2 - 1 if self.red else self.width // 2
        self.foodCarried = 0
        self.maxFoodCarry = 5
        self.retreatThreshold = 5
        self.teamIndex = None

    def chooseAction(self, gameState):
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]

        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        opponentGhosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        
        if (len(opponentGhosts) == 2 and 
            all(self.isInOurTerritory(ghost.getPosition()) for ghost in opponentGhosts)):
            return self.playDefensive(gameState, actions)
        
        opponentPacmen = [a for a in opponents if a.isPacman and a.getPosition() is not None]
        if len(opponentPacmen) == 2:
            return self.coordinatedAttack(gameState, actions)

        powerPellets = self.getPowerPellets(gameState)
        defenders = self.getVisibleDefenders(gameState)

        if powerPellets:
            return self.goToPowerPellet(gameState, actions, powerPellets, defenders)
        if defenders:
            dangerousDefenders = [
                pos for pos in defenders
                if self.getMazeDistance(myPos, pos) <= self.retreatThreshold
            ]
            if dangerousDefenders:
                return self.escapeDefender(gameState, dangerousDefenders, actions)
        if self.foodCarried >= self.maxFoodCarry and not self.isInSafeZone(myPos):
            return self.returnToSafeZone(gameState, actions)
        return self.goToFoodCluster(gameState, actions, defenders)

    def isInOurTerritory(self, pos):
        if self.red:
            return pos[0] < self.width // 2
        return pos[0] >= self.width // 2

    def playDefensive(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        midX = self.safeZone
        bestY = myPos[1]
        target = (midX, bestY)

        while gameState.hasWall(target[0], target[1]) and bestY > 1:
            bestY -= 1
            target = (midX, bestY)
        
        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            target
        ))

    def coordinatedAttack(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return 'Stop'
        
        midY = self.height // 2
        topFood = [food for food in foodList if food[1] >= midY]
        bottomFood = [food for food in foodList if food[1] < midY]
        teamMateState = gameState.getAgentState(self.teamIndex)

        if self.index < self.teamIndex:
            targetFood = topFood if topFood else bottomFood
        else:
            targetFood = bottomFood if bottomFood else topFood
        
        if not targetFood:
            return self.goToFoodCluster(gameState, actions, [])
            
        target = min(targetFood, key=lambda x: self.getMazeDistance(myPos, x))
        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            target
        ))

    def getVisibleDefenders(self, gameState):
        defenders = []
        for opponent in self.getOpponents(gameState):
            pos = gameState.getAgentPosition(opponent)
            if pos and not gameState.getAgentState(opponent).isPacman:
                defenders.append(pos)
        return defenders

    def getPowerPellets(self, gameState):
        return self.getCapsules(gameState)

    def goToPowerPellet(self, gameState, actions, powerPellets, defenders):
        myPos = gameState.getAgentPosition(self.index)
        bestPellet = min(powerPellets, key=lambda pellet: self.getMazeDistance(myPos, pellet))
        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            bestPellet
        ))

    def escapeDefender(self, gameState, defenders, actions):
        myPos = gameState.getAgentPosition(self.index)
        closestDefender = min(defenders, key=lambda x: self.getMazeDistance(myPos, x))
        return max(actions, key=lambda x: self.getMazeDistance(
            closestDefender, gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)
        ))

    def returnToSafeZone(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        target = (self.safeZone, myPos[1])
        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            target
        ))

    def isInSafeZone(self, pos):
        return pos[0] < self.safeZone if self.red else pos[0] >= self.safeZone

    def goToFoodCluster(self, gameState, actions, defenders):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        if not foodList:
            return 'Stop'
        foodClusters = self.identifyFoodClusters(foodList)
        clusterScores = []
        for cluster in foodClusters:
            center = self.calculateClusterCenter(cluster)
            distance = self.getMazeDistance(myPos, center)
            score = len(cluster) * 10 - distance
            for defender in defenders:
                if self.getMazeDistance(center, defender) <= self.retreatThreshold:
                    score -= 100
            clusterScores.append((score, center))
        bestCluster = max(clusterScores, key=lambda x: x[0])[1]
        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            bestCluster
        ))

    def identifyFoodClusters(self, foodList):
        clusters = []
        visited = set()

        def dfs(food, cluster):
            if food in visited:
                return
            visited.add(food)
            cluster.append(food)
            for neighbor in self.getNeighbors(food):
                if neighbor in foodList and neighbor not in visited:
                    dfs(neighbor, cluster)

        for food in foodList:
            if food not in visited:
                cluster = []
                dfs(food, cluster)
                clusters.append(cluster)
        return clusters

    def calculateClusterCenter(self, cluster):
        x = sum(pos[0] for pos in cluster) / len(cluster)
        y = sum(pos[1] for pos in cluster) / len(cluster)
        return (int(x), int(y))

    def getNeighbors(self, pos):
        neighbors = []
        x, y = pos
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (x + dx, y + dy)
            if (
                0 <= neighbor[0] < self.width
                and 0 <= neighbor[1] < self.height
                and not self.walls[neighbor[0]][neighbor[1]]
            ):
                neighbors.append(neighbor)
        return neighbors

    def coordinatedAttack(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return 'Stop'
        
        midY = self.height // 2
        topFood = [food for food in foodList if food[1] >= midY]
        bottomFood = [food for food in foodList if food[1] < midY]

        if self.index < self.teamIndex:
            targetFood = topFood if topFood else bottomFood
        else:
            targetFood = bottomFood if bottomFood else topFood
        
        if not targetFood:
            return self.goToFoodCluster(gameState, actions, [])
            
        target = min(targetFood, key=lambda x: self.getMazeDistance(myPos, x))
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        
        if path:
            return path[0]
        return 'Stop'

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

class DefensiveAgent(CaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)
        self.patrolPoints = []
        self.target = None
        self.teamIndex = None
        self.walls = None
        self.isOffensive = False
        self.assignedRegion = None

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        
        self.walls = gameState.getWalls()
        midX = self.walls.getWidth() // 2
        if self.red:
            midX = midX - 1
        height = self.walls.getHeight()
        
        self.patrolPoints = []
        for y in range(1, height - 1):
            if not gameState.hasWall(midX, y):
                self.patrolPoints.append((midX, y))

    def chooseAction(self, gameState):
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]

        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()
        
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        opponentGhosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        
        if len(opponentGhosts) == 2 and all(self.isInTheirTerritory(ghost.getPosition()) for ghost in opponentGhosts):
            self.isOffensive = True
            return self.playOffensive(gameState)
        
        self.isOffensive = False
        invaders = [a for a in opponents if a.isPacman and a.getPosition() is not None]
        
        if invaders:
            invaderPos = min([(self.getMazeDistance(myPos, a.getPosition()), a.getPosition()) 
                            for a in invaders])[1]
            problem = SearchProblem(gameState, myPos, invaderPos, gameState.getWalls())
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, invaderPos, gameState))
            if path:
                return path[0]
        
        if self.patrolPoints:
            if self.target is None or myPos == self.target:
                self.target = random.choice(self.patrolPoints)
            
            if self.target:
                problem = SearchProblem(gameState, myPos, self.target, gameState.getWalls())
                path = self.aStarSearch(problem, lambda x: betterHeuristic(x, self.target, gameState))
                if path:
                    return path[0]
        
        return Directions.STOP

    def playOffensive(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return Directions.STOP
        
        midY = gameState.getWalls().getHeight() // 2
        if self.index > self.teamIndex:
            foodList = [food for food in foodList if food[1] >= midY]
        else:
            foodList = [food for food in foodList if food[1] < midY]
            
        if not foodList:
            foodList = self.getFood(gameState).asList()
            
        target = min(foodList, key=lambda x: self.getMazeDistance(myPos, x))
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        
        if path:
            return path[0]
        return Directions.STOP

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

    def isInTheirTerritory(self, pos):
        midX = self.walls.getWidth() // 2
        if self.red:
            return pos[0] >= midX
        return pos[0] < midX
    
def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        DefensiveAgent(secondIndex)
    ]