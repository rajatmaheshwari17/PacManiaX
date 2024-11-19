# Team Name - PacTactic

from pacai.student.qlearningAgents import ApproximateQAgent
from pacai.student.multiagents import AlphaBetaAgent
from pacai.util import reflection
# from pacai.student.multiagents import MinimaxAgent
# from pacai.student.multiagents import ExpectimaxAgent

class SmartOffensiveQAgent(ApproximateQAgent):

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)
        self.capsules = self.getCapsules(gameState)

    def getAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        if self.capsules:
            closestCapsule = min(self.capsules, key=lambda c: self.getMazeDistance(myPos, c))
            if self.getMazeDistance(myPos, closestCapsule) < 5:
                return self.moveTowards(gameState, closestCapsule)
        foodList = [f for f in self.getFood(gameState).asList() if not self.isDeadEnd(gameState, f)]
        if foodList:
            targetFood = min(foodList, key=lambda f: self.getMazeDistance(myPos, f))
            return self.moveTowards(gameState, targetFood)
        return super().getAction(gameState)

    def isDeadEnd(self, gameState, position):
        legalMoves = gameState.getLegalActions(self.index)
        return len(legalMoves) <= 2

    def moveTowards(self, gameState, target):
        actions = gameState.getLegalActions(self.index)
        return min(actions, 
                   key=lambda a: self.getMazeDistance(
                       gameState.generateSuccessor(self.index, a).getAgentPosition(self.index),
                       target))

class AggressiveDefensiveAgent(AlphaBetaAgent):

    def registerInitialState(self, gameState):
        super().registerInitialState(gameState)

    def getAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        invaders = [i for i in self.getOpponents(gameState)
                    if gameState.getAgentPosition(i) is not None]
        if invaders:
            closestInvader = min(invaders, key=lambda i: self.getMazeDistance(myPos, gameState.getAgentPosition(i)))
            return self.moveTowards(gameState, gameState.getAgentPosition(closestInvader))
        criticalFood = self.getFoodYouAreDefending(gameState).asList()
        if criticalFood:
            targetFood = min(criticalFood, key=lambda f: self.getMazeDistance(myPos, f))
            return self.moveTowards(gameState, targetFood)
        return super().getAction(gameState)

    def moveTowards(self, gameState, target):
        actions = gameState.getLegalActions(self.index)
        return min(actions, 
                   key=lambda a: self.getMazeDistance(
                       gameState.generateSuccessor(self.index, a).getAgentPosition(self.index),
                       target))

def createTeam(firstIndex, secondIndex, isRed,
               first='pacai.student.myTeam.SmartOffensiveQAgent',
               second='pacai.student.myTeam.AggressiveDefensiveAgent'):
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