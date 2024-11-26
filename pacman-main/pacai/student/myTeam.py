from pacai.agents.capture.capture import CaptureAgent
import random
from pacai.core.directions import Directions

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

    def chooseAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')
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
        return self.navigateToTargetWithFood(gameState, [bestPellet], actions, defenders)

    def escapeDefender(self, gameState, defenders, actions):
        myPos = gameState.getAgentPosition(self.index)
        closestDefender = min(defenders, key=lambda x: self.getMazeDistance(myPos, x))
        return max(actions, key=lambda x: self.getMazeDistance(
            closestDefender, gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)
        ))

    def returnToSafeZone(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        target = (self.safeZone, myPos[1])
        return self.navigateToTargetWithFood(gameState, [target], actions, [])

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
        return self.navigateToTargetWithFood(gameState, [bestCluster], actions, defenders)

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

    def navigateToTargetWithFood(self, gameState, targets, actions, defenders):
        foodList = self.getFood(gameState).asList()

        def foodOnPath(successorPos):
            return len([food for food in foodList if self.getMazeDistance(successorPos, food) == 0])

        def isPathSafe(successorPos):
            for defender in defenders:
                if self.getMazeDistance(successorPos, defender) <= self.retreatThreshold:
                    return False
            return True

        return max(actions, key=lambda x: (
            isPathSafe(gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)),
            foodOnPath(gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)),
            -min(
                self.getMazeDistance(
                    gameState.generateSuccessor(self.index, x).getAgentPosition(self.index), target
                ) for target in targets
            )
        ))

class DefensiveAgent(CaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)
        self.patrolPoints = []
        self.target = None

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        
        midX = gameState.getWalls().getWidth() // 2
        if self.red:
            midX = midX - 1
        height = gameState.getWalls().getHeight()
        
        self.patrolPoints = []
        for y in range(1, height - 1):
            if not gameState.hasWall(midX, y):
                self.patrolPoints.append((midX, y))

    def chooseAction(self, gameState):
        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()
        
        invaders = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in invaders if a.isPacman() and a.getPosition() is not None]
        
        if len(invaders) > 0:
            dists = [(self.getMazeDistance(myPos, a.getPosition()), a) for a in invaders]
            closestInvader = min(dists, key=lambda x: x[0])[1]
            self.target = closestInvader.getPosition()
        elif self.target is None or myPos == self.target:
            foodList = self.getFoodYouAreDefending(gameState).asList()
            if len(foodList) <= 4:
                foodToEat = self.getFood(gameState).asList()
                if foodToEat:
                    self.target = random.choice(foodToEat)
            if not self.target and self.patrolPoints:
                self.target = random.choice(self.patrolPoints)
        
        actions = gameState.getLegalActions(self.index)
        bestAction = Directions.STOP
        bestDist = float('inf')
        
        if self.target:
            for action in actions:
                if action == Directions.STOP:
                    continue
                successor = gameState.generateSuccessor(self.index, action)
                newPos = successor.getAgentState(self.index).getPosition()
                dist = self.getMazeDistance(newPos, self.target)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
                    
        return bestAction
    
def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        DefensiveAgent(secondIndex)
    ]
