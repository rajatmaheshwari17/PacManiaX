from pacai.agents.capture.capture import CaptureAgent
import random

class DefensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls._width
        self.height = self.walls._height
        self.borderline = self.width // 2 - 1 if self.red else self.width // 2
        self.patrolPoints = self.getFullBorderPatrolPoints()
        self.currentPatrolIndex = 0
        self.initialTarget = None
        self.initialTargetReached = False

    def getFullBorderPatrolPoints(self):
        points = []
        x = self.borderline
        for y in range(self.height):
            if not self.walls[x][y]:
                points.append((x, y))
        return points

    def chooseAction(self, gameState):
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')

        myPos = gameState.getAgentPosition(self.index)
        # myState = gameState.getAgentState(self.index)
        # isScared = myState._scaredTimer > 0
        invaders = self.getVisibleInvaders(gameState)
        defendingFood = self.getFoodYouAreDefending(gameState).asList()

        print(f"Current Position: {myPos}")
        print(f"Visible Invaders: {invaders}")
        print(f"Defending Food: {defendingFood}")

        if invaders:
            print("Chasing invader.")
            return self.chaseSafely(gameState, invaders[0], actions)

        if not self.initialTargetReached:
            if self.initialTarget is None:
                self.initialTarget = self.getFarthestFood(defendingFood)
                print(f"Initial Target (Farthest Food): {self.initialTarget}")
            if self.initialTarget:
                if myPos == self.initialTarget:
                    self.initialTargetReached = True
                    print("Reached the initial target.")
                else:
                    print(f"Moving towards initial target: {self.initialTarget}")
                    return self.moveTowardsSafely(gameState, self.initialTarget, actions)

        if self.initialTargetReached or not defendingFood:
            print(f"Patrolling the border. Current Patrol Index: {self.currentPatrolIndex}")
            return self.patrolBorder(gameState, actions, myPos)

        # Default action if no specific goal
        return random.choice(actions)

    def getFarthestFood(self, foodList):
        if not foodList:
            return None
        if self.red:
            return min(foodList, key=lambda x: x[1])
        else:
            return max(foodList, key=lambda x: x[1])

    def patrolBorder(self, gameState, actions, myPos):
        if not self.patrolPoints:
            return random.choice(actions)

        targetPatrolPoint = self.patrolPoints[self.currentPatrolIndex]
        if self.getMazeDistance(myPos, targetPatrolPoint) < 2:
            self.currentPatrolIndex = (self.currentPatrolIndex + 1) % len(self.patrolPoints)
            print(f"Updated Patrol Index: {self.currentPatrolIndex}")

        return self.moveTowardsSafely(gameState, targetPatrolPoint, actions)

    def moveTowardsSafely(self, gameState, target, actions):
        if not actions or target is None:
            return random.choice(actions) if actions else 'Stop'

        validActions = [
            action for action in actions
            if self.isInOurTerritory(
                gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
            )
        ]

        if validActions:
            return min(validActions,
                       key=lambda x: self.getMazeDistance(
                           gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                           target))
        return random.choice(actions)

    def retreatSafely(self, gameState, invaderPos, actions):
        safeActions = [
            (a, self.getMazeDistance(
                gameState.generateSuccessor(self.index, a).getAgentPosition(self.index),
                invaderPos))
            for a in actions if self.isInOurTerritory(
                gameState.generateSuccessor(self.index, a).getAgentPosition(self.index))
        ]

        if safeActions:
            return max(safeActions, key=lambda x: x[1])[0]
        return random.choice(actions)

    def chaseSafely(self, gameState, invaderPos, actions):
        validActions = [
            action for action in actions
            if self.isInOurTerritory(
                gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
            )
        ]

        if validActions:
            return min(validActions,
                       key=lambda x: self.getMazeDistance(
                           gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                           invaderPos))
        return random.choice(actions)

    def getVisibleInvaders(self, gameState):
        invaders = []
        for opponent in self.getOpponents(gameState):
            pos = gameState.getAgentPosition(opponent)
            if pos and self.isInOurTerritory(pos):
                invaders.append(pos)
        return invaders

    def isInOurTerritory(self, pos):
        if not pos:
            return False
        if self.red:
            return pos[0] <= self.borderline
        else:
            return pos[0] > self.borderline

class OffensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls._width
        self.height = self.walls._height
        self.midline = self.width // 2
        
    def chooseAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        ghosts = self.getVisibleGhosts(gameState)
        
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')
        
        dangerousGhosts = [(pos, scared) for pos, scared in ghosts
                          if not scared and self.getMazeDistance(myPos, pos) <= 1]
                          
        if dangerousGhosts:
            return self.escapeGhost(gameState, dangerousGhosts[0][0], actions)
        
        return self.huntFood(gameState, ghosts, actions)
    
    def getVisibleGhosts(self, gameState):
        ghosts = []
        for opponent in self.getOpponents(gameState):
            pos = gameState.getAgentPosition(opponent)
            if pos:
                scared = bool(gameState.getAgentState(opponent)._scaredTimer > 0)
                ghosts.append((pos, scared))
        return ghosts
    
    def escapeGhost(self, gameState, ghostPos, actions):
        return max(actions,
                  key=lambda x: self.getMazeDistance(
                      gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                      ghostPos))
    
    def huntFood(self, gameState, ghosts, actions):
        myPos = gameState.getAgentPosition(self.index)
        foodList = self.getFood(gameState).asList()
        
        if not foodList:
            return 'Stop'
    
        foodScores = []
        for food in foodList:
            score = -self.getMazeDistance(myPos, food)
            
            for ghostPos, scared in ghosts:
                if not scared:
                    ghostDist = self.getMazeDistance(food, ghostPos)
                    if ghostDist < 2:
                        score -= 100
            
            foodScores.append((score, food))

        targetFood = max(foodScores, key=lambda x: x[0])[1]
        
        return min(actions,
                  key=lambda x: self.getMazeDistance(
                      gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                      targetFood))

def createTeam(firstIndex, secondIndex, isRed):
    return [
        OffensiveAgent(firstIndex),
        DefensiveAgent(secondIndex)
    ]