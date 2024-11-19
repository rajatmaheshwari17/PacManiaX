from pacai.agents.capture.capture import CaptureAgent
from pacai.util import reflection
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
        """Check if the agent is on the opponent's side (Pac-Man mode)."""
        if self.red:
            return position[0] >= self.midLine
        else:
            return position[0] < self.midLine

    def offensiveMove(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        ghosts = [gameState.getAgentPosition(i) for i in self.getOpponents(gameState) if gameState.getAgentPosition(i)]
        if any(mazeDistance(myPos, g, gameState) < 3 for g in ghosts):
            return self.escapeGhost(gameState, ghosts)
        foodList = gameState.getFood().asList()
        if foodList:
            targetFood = min(foodList, key=lambda f: mazeDistance(myPos, f, gameState))
            return self.moveTowards(gameState, targetFood)
        return self.randomMove(gameState)

    def escapeGhost(self, gameState, ghosts):
        actions = gameState.getLegalActions(self.index)
        safeActions = [
            a for a in actions if all(
                mazeDistance(gameState.generateSuccessor(self.index, a).getAgentPosition(self.index), g, gameState) >= 3
                for g in ghosts
            )
        ]
        return random.choice(safeActions) if safeActions else self.randomMove(gameState)

    def patrolMidLine(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        target = (self.midLine, myPos[1])
        return self.moveTowards(gameState, target)

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

class ReactiveDefensiveAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)

    def chooseAction(self, gameState):
        return self.getAction(gameState)

    def getAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        invaders = [i for i in self.getOpponents(gameState) if gameState.getAgentPosition(i)]
        if invaders:
            closestInvader = min(invaders, key=lambda i: mazeDistance(myPos, gameState.getAgentPosition(i), gameState))
            if mazeDistance(myPos, gameState.getAgentPosition(closestInvader), gameState) <= 2:
                return self.captureInvader(gameState, closestInvader)
            return self.moveTowards(gameState, gameState.getAgentPosition(closestInvader))
        criticalFood = gameState.getFoodYouAreDefending().asList()
        if criticalFood:
            targetFood = min(criticalFood, key=lambda f: mazeDistance(myPos, f, gameState))
            return self.moveTowards(gameState, targetFood)
        return self.randomMove(gameState)

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

def createTeam(firstIndex, secondIndex, isRed,
               first='pacai.student.myTeam.AggressiveOffensiveAgent',
               second='pacai.student.myTeam.ReactiveDefensiveAgent'):
    """
    This function should return a list of two agents that will form the capture team,
    initialized using firstIndex and secondIndex as their agent indexed.
    isRed is True if the red team is being created,
    and will be False if the blue team is being created.
    """
    firstAgent = reflection.qualifiedImport(first)
    secondAgent = reflection.qualifiedImport(second)
    return [
        firstAgent(firstIndex),
        secondAgent(secondIndex),
    ]