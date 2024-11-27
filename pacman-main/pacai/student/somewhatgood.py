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
        self.maxFoodCarry = 5
        self.retreatThreshold = 5
        self.teamIndex = None
        self.previousPosition = None

    def chooseAction(self, gameState):
        # print("Choose Action | Offensive Class")
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]

        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        opponentGhosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]

        '''
        print(all(self.isInOurTerritory(ghost.getPosition()) for ghost in opponentGhosts))
        if (all(self.isInOurTerritory(ghost.getPosition()) for ghost in opponentGhosts)):
            print("Triggered")
            if not self.isInOurTerritory(myPos):
                print("Retreat")
                self.foodCarried = 0
                return self.returnToSafeZone(gameState, actions)
            return self.playDefensive(gameState, actions)
        '''
            
        frontGhost = self.checkFrontGhost(gameState, myPos, opponentGhosts)
        if frontGhost:
            return self.findAlternatePath(gameState, actions, frontGhost)

        opponentPacmen = [a for a in opponents if a.isPacman and a.getPosition() is not None]
        if len(opponentPacmen) == 2:
            return self.coordinatedAttack(gameState, actions)

        powerPellets = self.getPowerPellets(gameState)
        defenders = self.getVisibleDefenders(gameState)

        if defenders and powerPellets:
            closestDefender = min(defenders, key=lambda x: self.getMazeDistance(myPos, x))
            if self.getMazeDistance(myPos, closestDefender) < self.retreatThreshold:
                return self.goToPowerPellet(gameState, actions, powerPellets, defenders)

        if defenders:
            dangerousDefenders = [
                pos for pos in defenders
                if self.getMazeDistance(myPos, pos) <= self.retreatThreshold
            ]
            if dangerousDefenders:
                return self.escapeDefender(gameState, dangerousDefenders, actions)
        if self.foodCarried >= self.maxFoodCarry:
            return self.returnToSafeZone(gameState, actions)
        return self.goToFoodCluster(gameState, actions, defenders)
    
    def retreat(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        targetX = self.width // 4 if self.red else 3 * self.width // 4
        targetY = self.height // 2
        target = (targetX, targetY)
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: self.getMazeDistance(x, target))
        
        if path:
            return path[0]

        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            target
        ))

    def checkFrontGhost(self, gameState, myPos, opponentGhosts):
        if not opponentGhosts:
            return None
            
        if self.previousPosition:
            currentDirection = self.getCurrentDirection(myPos, self.previousPosition)
            for ghost in opponentGhosts:
                ghostPos = ghost.getPosition()
                if self.isInFront(myPos, ghostPos, currentDirection):
                    return ghostPos
        
        self.previousPosition = myPos
        return None

    def getCurrentDirection(self, currentPos, previousPos):
        dx = currentPos[0] - previousPos[0]
        dy = currentPos[1] - previousPos[1]
        if dx > 0: return 'East'
        if dx < 0: return 'West'
        if dy > 0: return 'North'
        if dy < 0: return 'South'
        return None

    def isInFront(self, myPos, ghostPos, direction):
        if direction == 'East':
            return ghostPos[0] > myPos[0] and abs(ghostPos[1] - myPos[1]) <= 1
        elif direction == 'West':
            return ghostPos[0] < myPos[0] and abs(ghostPos[1] - myPos[1]) <= 1
        elif direction == 'North':
            return ghostPos[1] > myPos[1] and abs(ghostPos[0] - myPos[0]) <= 1
        elif direction == 'South':
            return ghostPos[1] < myPos[1] and abs(ghostPos[0] - myPos[0]) <= 1
        return False

    def findAlternatePath(self, gameState, actions, ghostPos):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return actions[0]
        
        safeFoodList = [food for food in foodList 
                       if self.getMazeDistance(food, ghostPos) > self.retreatThreshold]
        
        if not safeFoodList:
            return self.escapeDefender(gameState, [ghostPos], actions)
           
        def isSafeDirection(food):
            foodDir = self.getCurrentDirection(food, myPos)
            ghostDir = self.getCurrentDirection(ghostPos, myPos)
            return foodDir != ghostDir
            
        safeFood = [food for food in safeFoodList if isSafeDirection(food)]
        
        if safeFood:
            target = min(safeFood, key=lambda x: self.getMazeDistance(myPos, x))
            problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
            if path:
                return path[0]
                
        return self.escapeDefender(gameState, [ghostPos], actions)

    def isInOurTerritory(self, pos):
        if self.red:
            return pos[0] < self.width // 2
        return pos[0] >= self.width // 2

    def playDefensive(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        midX = self.safeZone
        bestY = int(myPos[1])
        target = (midX, bestY)
        
        while gameState.hasWall(target[0], target[1]) and bestY > 1:
            bestY -= 1
            target = (midX, bestY)
            
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        if path:
            return path[0]
        return actions[0]

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
            return actions[0]
            
        target = min(targetFood, key=lambda x: self.getMazeDistance(myPos, x))
        problem = SearchProblem(gameState, myPos, target, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, target, gameState))
        
        if path:
            return path[0]
        return actions[0]

    def goToFoodCluster(self, gameState, actions, defenders):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return 'Stop'
            
        foodClusters = self.identifyFoodClusters(foodList)
        clusterScores = []
        
        for cluster in foodClusters:
            center = self.calculateClusterCenter(cluster)
            center = (int(center[0]), int(center[1]))
            problem = SearchProblem(gameState, myPos, center, gameState.getWalls())
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, center, gameState))
            distance = len(path) if path else 1000
            score = len(cluster) * 10 - distance
            
            for defender in defenders:
                if self.getMazeDistance(center, defender) <= self.retreatThreshold:
                    score -= 100
                    
            if self.isSafeCluster(center, gameState):
                score += 50
                
            clusterScores.append((score, center, path))
        
        if not clusterScores:
            return actions[0]
        
        bestScore, bestCenter, bestPath = max(clusterScores, key=lambda x: x[0])
        self.lastPath = bestPath
        
        if bestPath:
            return bestPath[0]
            
        return min(actions, key=lambda x: self.getMazeDistance(
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
            bestCenter
        ))

    def isSafeCluster(self, center, gameState):
        if self.red:
            safeX = self.width // 2 - 2
            return center[0] < safeX
        else:
            safeX = self.width // 2 + 2
            return center[0] >= safeX

    def identifyFoodClusters(self, foodList):
        clusters = []
        visited = set()
        
        def getNearbyFood(food, cluster):
            if food in visited:
                return
            
            visited.add(food)
            cluster.append(food)
            x, y = food

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nextFood = (x + dx, y + dy)
                if nextFood in foodList and nextFood not in visited:
                    getNearbyFood(nextFood, cluster)
        
        for food in foodList:
            if food not in visited:
                newCluster = []
                getNearbyFood(food, newCluster)
                if newCluster:
                    clusters.append(newCluster)
        
        return clusters

    def calculateClusterCenter(self, cluster):
        if not cluster:
            return (0, 0)
        sumX = sum(x for x, _ in cluster)
        sumY = sum(y for _, y in cluster)
        return (sumX // len(cluster), sumY // len(cluster))

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
        if not powerPellets:
            return self.goToFoodCluster(gameState, actions, defenders)
            
        bestPellet = min(powerPellets, key=lambda pellet: self.getMazeDistance(myPos, pellet))
        problem = SearchProblem(gameState, myPos, bestPellet, gameState.getWalls())
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, bestPellet, gameState))
        
        if path:
            return path[0]
        return actions[0]

    def escapeDefender(self, gameState, defenders, actions):
        myPos = gameState.getAgentPosition(self.index)
        closestDefender = min(defenders, key=lambda x: self.getMazeDistance(myPos, x))
        safeX = self.safeZone
        safeY = myPos[1]
        safePoints = []

        for y in range(1, self.height - 1):
            if not gameState.hasWall(safeX, y):
                dist_to_defender = self.getMazeDistance((safeX, y), closestDefender)
                if dist_to_defender > self.retreatThreshold:
                    safePoints.append((safeX, y))
        
        if safePoints:
            safeTarget = min(safePoints, 
                           key=lambda p: self.getMazeDistance(myPos, p))
            problem = SearchProblem(gameState, myPos, safeTarget, gameState.getWalls())
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, safeTarget, gameState))
            if path:
                return path[0]
        
        return max(actions, key=lambda x: self.getMazeDistance(
            closestDefender,
            gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)
        ))

    def returnToSafeZone(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        target = (self.safeZone, myPos[1])
        
        while gameState.hasWall(target[0], target[1]):
            target = (target[0], target[1] - 1)
            if target[1] < 1:
                target = (self.safeZone, myPos[1] + 1)
                
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
                successors = problem.successorStates(current_state)
                successors.sort(key=lambda x: self.evaluateSuccessor(x[0]))
                
                for next_state, action, next_cost in successors:
                    if next_state not in visited:
                        new_cost = cost + next_cost
                        new_path = path + [action]
                        priority = new_cost + heuristic(next_state)
                        pq.push((next_state, new_path, new_cost), priority)
        return []

    def evaluateSuccessor(self, state):
        x, y = state
        if self.red:
            distanceFromBorder = abs(x - (self.width // 2 - 1))
        else:
            distanceFromBorder = abs(x - (self.width // 2))
        return distanceFromBorder

class DefensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls.getWidth()
        self.height = self.walls.getHeight()
        self.midX = self.width // 2 - 1 if self.red else self.width // 2
        self.patrolPoints = []
        self.ghostKills = 0 
        
        for y in range(1, self.height - 1):
            if not gameState.hasWall(self.midX, y):
                self.patrolPoints.append((self.midX, y))
        
        self.target = None
        self.teamIndex = None
        self.lastTeammatePath = None
        self.patrolIndex = 0
        self.chaseThreshold = 5

    def chooseAction(self, gameState):
        # print("Choose Action | Defensive Class")
        if self.teamIndex is None:
            allys = self.getTeam(gameState)
            self.teamIndex = [i for i in allys if i != self.index][0]

        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() is not None]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() is not None]
        actions = gameState.getLegalActions(self.index)

        if 'Stop' in actions:
            actions.remove('Stop')

        # print(len(ghosts))
        # print(all(self.isInTheirTerritory(ghost.getPosition()) for ghost in ghosts))
        if (all(self.isInTheirTerritory(ghost.getPosition()) for ghost in ghosts)):
            print("triggered")
            return self.playOffensive(gameState)
        
        if invaders:
            invaderDists = [(self.getMazeDistance(myPos, a.getPosition()), a) for a in invaders]
            closestInvader = min(invaderDists, key=lambda x: x[0])[1]
            invaderPos = closestInvader.getPosition()
            problem = SearchProblem(gameState, myPos, invaderPos, self.walls)
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, invaderPos, gameState))
            
            if path:
                return path[0]
                
            return min(actions, key=lambda x: self.getMazeDistance(
                gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                invaderPos))
        
        return self.patrolBehavior(gameState, myPos, actions)
        
    def patrolBehavior(self, gameState, myPos, actions):
        beliefs = self.getBeliefs(gameState)
        if beliefs:
            mostLikelyPos = max(beliefs, key=beliefs.get)
            problem = SearchProblem(gameState, myPos, mostLikelyPos, self.walls)
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, mostLikelyPos, gameState))
            if path:
                return path[0]
        
        if not self.patrolPoints:
            return actions[0]
            
        if self.target is None or myPos == self.target:
            self.patrolIndex = (self.patrolIndex + 1) % len(self.patrolPoints)
            self.target = self.patrolPoints[self.patrolIndex]
        
        problem = SearchProblem(gameState, myPos, self.target, self.walls)
        path = self.aStarSearch(problem, lambda x: betterHeuristic(x, self.target, gameState))
        
        if path:
            return path[0]
            
        return actions[0]
        
    def getBeliefs(self, gameState):
        beliefs = {}
        for x in range(self.width):
            for y in range(self.height):
                if not self.walls[x][y]:
                    distToMid = abs(x - self.midX)
                    beliefs[(x, y)] = 1.0 / (distToMid + 1)
        
        enemies = self.getOpponents(gameState)
        for enemy in enemies:
            pos = gameState.getAgentPosition(enemy)
            if pos is None:
                noisyDist = gameState.getAgentDistances()[enemy]
                for pos in beliefs:
                    distance = self.getMazeDistance(gameState.getAgentPosition(self.index), pos)
                    beliefs[pos] *= self.getNoisyDistanceProb(distance, noisyDist)
        
        return beliefs
        
    def getNoisyDistanceProb(self, trueDistance, noisyDistance):
        diff = abs(trueDistance - noisyDistance)
        return 1.0 / (diff + 1)
        
    def isInTheirTerritory(self, pos):
        midX = self.width // 2
        if self.red:
            return int(pos[0]) >= midX
        return int(pos[0]) < midX

    def playOffensive(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return Directions.STOP
        
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        safeFood = []

        for food in foodList:
            isSafe = True
            for ghost in ghosts:
                if self.getMazeDistance(food, ghost.getPosition()) < 3:
                    isSafe = False
                    break
            if isSafe:
                safeFood.append(food)
        
        if not safeFood:
            safeFood = foodList
            
        midY = self.height // 2
        if self.index > self.teamIndex:
            targetFood = [food for food in safeFood if food[1] >= midY]
        else:
            targetFood = [food for food in safeFood if food[1] < midY]

        if not targetFood:
            targetFood = safeFood

        foodDistances = []
        for food in targetFood:
            problem = SearchProblem(gameState, myPos, food, self.walls)
            path = self.aStarSearch(problem, lambda x: betterHeuristic(x, food, gameState))
            if path:
                foodDistances.append((len(path), food, path[0]))
                
        if foodDistances:
            return min(foodDistances, key=lambda x: x[0])[2]
            
        if targetFood:
            closestFood = min(targetFood, key=lambda x: self.getMazeDistance(myPos, x))
            return min(actions, key=lambda x: self.getMazeDistance(
                gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                closestFood))
                
        return Directions.STOP

    def isPathSafe(self, gameState, path):
        if not path:
            return False
            
        myPos = gameState.getAgentPosition(self.index)
        opponents = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        ghosts = [a for a in opponents if not a.isPacman and a.getPosition() is not None]
        currentPos = myPos

        for action in path:
            dx, dy = Actions.directionToVector(action)
            currentPos = (int(currentPos[0] + dx), int(currentPos[1] + dy))
            
            for ghost in ghosts:
                if self.getMazeDistance(currentPos, ghost.getPosition()) < 2:
                    return False
                    
        return True
    
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
        DefensiveAgent(secondIndex)
    ]