from pacai.agents.capture.capture import CaptureAgent

class DefensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.walls = gameState.getWalls()
        self.width = self.walls._width
        self.height = self.walls._height
        self.borderline = self.width // 2 - 1 if self.red else self.width // 2
        
    def chooseAction(self, gameState):
        actions = [a for a in gameState.getLegalActions(self.index)
                  if not self.isInEnemyTerritory(
                      gameState.generateSuccessor(self.index, a).getAgentPosition(self.index))]
        
        if not actions:
            actions = gameState.getLegalActions(self.index)
        
        if 'Stop' in actions:
            actions.remove('Stop')
            
        myPos = gameState.getAgentPosition(self.index)
        invaders = self.getVisibleInvaders(gameState)
        
        if invaders:
            closestInvader = min(invaders, key=lambda x: self.getMazeDistance(myPos, x))
            return self.chaseInvader(gameState, closestInvader, actions)
            
        return self.patrolTerritory(gameState, actions)
    
    def getVisibleInvaders(self, gameState):
        invaders = []
        for opponent in self.getOpponents(gameState):
            pos = gameState.getAgentPosition(opponent)
            if pos and self.isInOurTerritory(pos):
                invaders.append(pos)
        return invaders

    def isInEnemyTerritory(self, pos):
        if self.red:
            return pos[0] >= self.borderline
        return pos[0] < self.borderline

    def isInOurTerritory(self, pos):
        return not self.isInEnemyTerritory(pos)

    def chaseInvader(self, gameState, invaderPos, actions):
        return min(actions,
                  key=lambda x: self.getMazeDistance(
                      gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                      invaderPos))

    def patrolTerritory(self, gameState, actions):
        # myPos = gameState.getAgentPosition(self.index)
        food = self.getFoodYouAreDefending(gameState).asList()
        
        if food:
            borderFood = min(food, key=lambda x: abs(x[0] - self.borderline))
            return min(actions,
                      key=lambda x: self.getMazeDistance(
                          gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                          borderFood))
        
        target = (self.borderline, self.height // 2)
        return min(actions,
                  key=lambda x: self.getMazeDistance(
                      gameState.generateSuccessor(self.index, x).getAgentPosition(self.index),
                      target))

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