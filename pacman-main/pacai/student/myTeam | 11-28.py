from pacai.agents.capture.capture import CaptureAgent
import random

class OffensiveAgent(CaptureAgent):
    agentZones = {}

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls._width
        self.height = self.walls._height
        self.safeZone = self.width // 2 - 1 if self.red else self.width // 2
        self.foodCarried = 0
        self.maxFoodCarry = 5
        self.retreatThreshold = 5
        
        if len(OffensiveAgent.agentZones) == 0:
            OffensiveAgent.agentZones[self.index] = 'upper'
        else:
            OffensiveAgent.agentZones[self.index] = 'lower'

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
        zoneFiltered = self.filterByZone(powerPellets)
        if zoneFiltered:
            bestPellet = min(zoneFiltered, key=lambda pellet: self.getMazeDistance(myPos, pellet))
        else:
            bestPellet = min(powerPellets, key=lambda pellet: self.getMazeDistance(myPos, pellet))
        return self.navigateToTargetWithFood(gameState, [bestPellet], actions, defenders)

    def filterByZone(self, positions):
        midY = self.height // 2
        if OffensiveAgent.agentZones[self.index] == 'upper':
            return [pos for pos in positions if pos[1] >= midY]
        else:
            return [pos for pos in positions if pos[1] < midY]

    def escapeDefender(self, gameState, defenders, actions):
        myPos = gameState.getAgentPosition(self.index)
        closestDefender = min(defenders, key=lambda x: self.getMazeDistance(myPos, x))
        safeActions = []
        for action in actions:
            newPos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
            if self.isInPreferredZone(newPos):
                safeActions.append(action)
        
        if safeActions:
            return max(safeActions, key=lambda x: self.getMazeDistance(
                closestDefender, gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)
            ))
        return max(actions, key=lambda x: self.getMazeDistance(
            closestDefender, gameState.generateSuccessor(self.index, x).getAgentPosition(self.index)
        ))

    def isInPreferredZone(self, pos):
        midY = self.height // 2
        if OffensiveAgent.agentZones[self.index] == 'upper':
            return pos[1] >= midY
        return pos[1] < midY

    def returnToSafeZone(self, gameState, actions):
        myPos = gameState.getAgentPosition(self.index)
        preferredY = self.height * 3 // 4 if OffensiveAgent.agentZones[self.index] == 'upper' else self.height // 4
        target = (self.safeZone, preferredY)
        return self.navigateToTargetWithFood(gameState, [target], actions, [])

    def isInSafeZone(self, pos):
        return pos[0] < self.safeZone if self.red else pos[0] >= self.safeZone

    def goToFoodCluster(self, gameState, actions, defenders):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        foodList = self.filterByZone(foodList)
        
        if not foodList:
            foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return 'Stop'
            
        foodClusters = self.identifyFoodClusters(foodList)
        clusterScores = []
        for cluster in foodClusters:
            center = self.calculateClusterCenter(cluster)
            distance = self.getMazeDistance(myPos, center)
            score = len(cluster) * 10 - distance
            
            if self.isInPreferredZone(center):
                score += 50
                
            for defender in defenders:
                if self.getMazeDistance(center, defender) <= self.retreatThreshold:
                    score -= 100
            clusterScores.append((score, center))
        
        if not clusterScores:
            return random.choice(actions)
            
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

def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        OffensiveAgent(secondIndex)
    ]