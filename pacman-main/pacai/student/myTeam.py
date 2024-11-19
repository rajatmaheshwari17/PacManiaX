from pacai.agents.capture.capture import CaptureAgent
from pacai.core.distance import maze as mazeDistance
import random

class AggressiveOffensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        walls = gameState.getWalls()
        self.midLine = walls._width // 2
        self.capsules = gameState.getCapsules()

    def chooseAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        if self.isPacman(gameState, myPos):
            return self.offensiveMove(gameState)
        return self.patrolMidLine(gameState)

    def isPacman(self, gameState, position):
        if self.red:
            return position[0] >= self.midLine
        else:
            return position[0] < self.midLine

    def offensiveMove(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        ghosts = [
            gameState.getAgentPosition(i)
            for i in self.getOpponents(gameState)
            if gameState.getAgentPosition(i)
        ]
        if any(mazeDistance(myPos, g, gameState) < 3 for g in ghosts):
            return self.escapeGhost(gameState, ghosts)
        foodList = gameState.getFood().asList()
        if foodList:
            targetFood = min(foodList, key=lambda f: mazeDistance(myPos, f, gameState))
            return self.moveTowards(gameState, targetFood)
        return self.randomMove(gameState)

    def escapeGhost(self, gameState, ghosts):
        actions = gameState.getLegalActions(self.index)
        safeActions = []
        
        for a in actions:
            successor = gameState.generateSuccessor(self.index, a)
            newPos = successor.getAgentPosition(self.index)
            safe = True
            for g in ghosts:
                if mazeDistance(newPos, g, gameState) < 3:
                    safe = False
                    break
            if safe:
                safeActions.append(a)
        
        return random.choice(safeActions) if safeActions else random.choice(actions)


    def patrolMidLine(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        walls = gameState.getWalls()
        y = myPos[1]
        while walls[self.midLine][y]:
            y = (y + 1) % walls._height
        target = (self.midLine, y)
        return self.moveTowards(gameState, target)

    def moveTowards(self, gameState, target):
        actions = gameState.getLegalActions(self.index)
        walls = gameState.getWalls()

        validActions = [
            a for a in actions
            if not walls[gameState.generateSuccessor(self.index, a).getAgentPosition(self.index)[0]]
                        [gameState.generateSuccessor(self.index, a).getAgentPosition(self.index)[1]]
        ]

        if not validActions:
            return random.choice(actions)

        return min(
            validActions,
            key=lambda a: mazeDistance(
                gameState.generateSuccessor(self.index, a).getAgentPosition(self.index),
                target,
                gameState
            )
        )

    def randomMove(self, gameState):
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')
        return random.choice(actions)

class ReactiveDefensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)

    def chooseAction(self, gameState):
        return self.getAction(gameState)

    def getAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        invaders = [
            i for i in self.getOpponents(gameState) 
            if gameState.getAgentPosition(i) and self.isOpponentPacman(gameState, i)
        ]
        if invaders:
            closestInvader = min(
                invaders, 
                key=lambda i: mazeDistance(myPos, gameState.getAgentPosition(i), gameState)
            )
            if mazeDistance(myPos, gameState.getAgentPosition(closestInvader), gameState) <= 2:
                return self.captureInvader(gameState, closestInvader)
            return self.moveTowards(gameState, gameState.getAgentPosition(closestInvader))
        
        criticalFood = gameState.getFoodYouAreDefending().asList()
        if criticalFood:
            targetFood = min(criticalFood, key=lambda f: mazeDistance(myPos, f, gameState))
            return self.moveTowards(gameState, targetFood)
        
        return self.randomMove(gameState)

    def isOpponentPacman(self, gameState, opponentIndex):
        opponentPos = gameState.getAgentPosition(opponentIndex)
        if opponentPos:
            if self.red:
                return opponentPos[0] >= gameState.getWalls()._width // 2
            else:
                return opponentPos[0] < gameState.getWalls()._width // 2
        return False


    def captureInvader(self, gameState, invader):
        return self.moveTowards(gameState, gameState.getAgentPosition(invader))

    def moveTowards(self, gameState, target):
        actions = gameState.getLegalActions(self.index)
        return min(
            actions,
            key=lambda a: mazeDistance(
                gameState.generateSuccessor(self.index, a).getAgentPosition(self.index),
                target,
                gameState
            )
        )

    def randomMove(self, gameState):
        actions = gameState.getLegalActions(self.index)
        if 'Stop' in actions:
            actions.remove('Stop')
        return random.choice(actions)

def createTeam(firstIndex, secondIndex, isRed):
    return [
        AggressiveOffensiveAgent(firstIndex),
        ReactiveDefensiveAgent(secondIndex),
    ]