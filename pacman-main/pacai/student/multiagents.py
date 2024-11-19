import random

from pacai.agents.base import BaseAgent
from pacai.agents.search.multiagent import MultiAgentSearchAgent
from pacai.core.distance import manhattan as manhattanDistance

class ReflexAgent(BaseAgent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.
    You are welcome to change it in any way you see fit,
    so long as you don't touch the method headers.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

    def getAction(self, gameState):
        """
        You do not need to change this method, but you're welcome to.

        `ReflexAgent.getAction` chooses among the best options according to the evaluation function.

        Just like in the previous project, this method takes a
        `pacai.core.gamestate.AbstractGameState` and returns some value from
        `pacai.core.directions.Directions`.
        """

        # Collect legal moves.
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions.
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices)  # Pick randomly among the best.

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current `pacai.bin.pacman.PacmanGameState`
        and an action, and returns a number, where higher numbers are better.
        Make sure to understand the range of different values before you combine them
        in your evaluation function.
        """

        successorGameState = currentGameState.generatePacmanSuccessor(action)

        # Useful information you can extract.
        # newPosition = successorGameState.getPacmanPosition()
        # oldFood = currentGameState.getFood()
        # newGhostStates = successorGameState.getGhostStates()
        # newScaredTimes = [ghostState.getScaredTimer() for ghostState in newGhostStates]

        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        score = successorGameState.getScore()
        foodDist = [manhattanDistance(newPos, food) for food in newFood.asList()]
        if len(foodDist) > 0:
            score += 1.0 / min(foodDist)
        for ghost in newGhostStates:
            if manhattanDistance(newPos, ghost.getPosition()) < 2:
                score -= 1000
        return score

class MinimaxAgent(MultiAgentSearchAgent):
    """
    A minimax agent.

    Here are some method calls that might be useful when implementing minimax.

    `pacai.core.gamestate.AbstractGameState.getNumAgents()`:
    Get the total number of agents in the game

    `pacai.core.gamestate.AbstractGameState.getLegalActions`:
    Returns a list of legal actions for an agent.
    Pacman is always at index 0, and ghosts are >= 1.

    `pacai.core.gamestate.AbstractGameState.generateSuccessor`:
    Get the successor game state after an agent takes an action.

    `pacai.core.directions.Directions.STOP`:
    The stop direction, which is always legal, but you may not want to include in your search.

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Returns the minimax action from the current gameState using
    `pacai.agents.search.multiagent.MultiAgentSearchAgent.getTreeDepth`
    and `pacai.agents.search.multiagent.MultiAgentSearchAgent.getEvaluationFunction`.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

    def getAction(self, gameState):
        def minimax(agentIndex, depth, state):
            if state.isWin() or state.isLose() or depth == min(self.getTreeDepth() + 2, 5):
                return self.getEvaluationFunction()(state)
            numAgents = state.getNumAgents()
            if agentIndex == 0:
                legalActions = [
                    action for action in state.getLegalActions(agentIndex)
                    if action != 'Stop'
                ]
                if not legalActions:
                    return self.getEvaluationFunction()(state)
                return max(
                    minimax(1, depth, state.generateSuccessor(agentIndex, action))
                    for action in legalActions
                )
            else:
                nextAgent = (agentIndex + 1) % numAgents
                nextDepth = depth + 1 if nextAgent == 0 else depth
                legalActions = state.getLegalActions(agentIndex)
                if not legalActions:
                    return self.getEvaluationFunction()(state)
                return min(
                    minimax(nextAgent, nextDepth, state.generateSuccessor(agentIndex, action))
                    for action in legalActions
                )
        legalActions = [action for action in gameState.getLegalActions(0) if action != 'Stop']
        if not legalActions:
            return None
        bestAction = max(
            legalActions,
            key=lambda action: minimax(1, 0, gameState.generateSuccessor(0, action))
        )
        return bestAction

class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    A minimax agent with alpha-beta pruning.

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Returns the minimax action from the current gameState using
    `pacai.agents.search.multiagent.MultiAgentSearchAgent.getTreeDepth`
    and `pacai.agents.search.multiagent.MultiAgentSearchAgent.getEvaluationFunction`.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)
    
    def getAction(self, gameState):
        def alphaBeta(agentIndex, depth, state, alpha, beta):
            if state.isWin() or state.isLose() or depth == min(self.getTreeDepth() + 2, 5):
                return self.getEvaluationFunction()(state)
            numAgents = state.getNumAgents()
            if agentIndex == 0:
                value = float('-inf')
                legalActions = [
                    action for action in state.getLegalActions(agentIndex)
                    if action != 'Stop'
                ]
                if not legalActions:
                    return self.getEvaluationFunction()(state)
                for action in legalActions:
                    value = max(
                        value,
                        alphaBeta(
                            1, depth, state.generateSuccessor(agentIndex, action), alpha, beta
                        )
                    )
                    if value > beta:
                        return value
                    alpha = max(alpha, value)
                return value
            else:
                value = float('inf')
                nextAgent = (agentIndex + 1) % numAgents
                nextDepth = depth + 1 if nextAgent == 0 else depth
                legalActions = state.getLegalActions(agentIndex)
                if not legalActions:
                    return self.getEvaluationFunction()(state)
                for action in legalActions:
                    value = min(
                        value,
                        alphaBeta(
                            nextAgent,
                            nextDepth,
                            state.generateSuccessor(agentIndex, action),
                            alpha,
                            beta
                        )
                    )
                    if value < alpha:
                        return value
                    beta = min(beta, value)
                return value
        legalActions = [action for action in gameState.getLegalActions(0) if action != 'Stop']
        if not legalActions:
            return None
        bestAction = max(
            legalActions,
            key=lambda action: alphaBeta(
                1, 0, gameState.generateSuccessor(0, action), float('-inf'), float('inf')
            )
        )
        return bestAction

class ExpectimaxAgent(MultiAgentSearchAgent):
    """
    An expectimax agent.

    All ghosts should be modeled as choosing uniformly at random from their legal moves.

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`:
    Returns the expectimax action from the current gameState using
    `pacai.agents.search.multiagent.MultiAgentSearchAgent.getTreeDepth`
    and `pacai.agents.search.multiagent.MultiAgentSearchAgent.getEvaluationFunction`.
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)

    def getAction(self, gameState):
        def expectimax(agentIndex, depth, state):
            if state.isWin() or state.isLose() or depth == self.getTreeDepth():
                return self.getEvaluationFunction()(state)
            numAgents = state.getNumAgents()
            if agentIndex == 0:
                return max(
                    expectimax(1, depth, state.generateSuccessor(agentIndex, action))
                    for action in state.getLegalActions(agentIndex)
                )
            else:
                nextAgent = (agentIndex + 1) % numAgents
                nextDepth = depth + 1 if nextAgent == 0 else depth
                actions = state.getLegalActions(agentIndex)
                if not actions:
                    return 0
                return sum(
                    expectimax(nextAgent, nextDepth, state.generateSuccessor(agentIndex, action))
                    for action in actions
                ) / len(actions)
        bestAction = max(
            gameState.getLegalActions(0),
            key=lambda action: expectimax(1, 0, gameState.generateSuccessor(0, action))
        )
        return bestAction

def betterEvaluationFunction(currentGameState):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable evaluation function.

    DESCRIPTION: <write something here so we know what you did>
    """

    pacmanPos = currentGameState.getPacmanPosition()
    food = currentGameState.getFood()
    ghostStates = currentGameState.getGhostStates()
    capsules = currentGameState.getCapsules()
    score = currentGameState.getScore()
    foodDistances = [manhattanDistance(pacmanPos, foodPos) for foodPos in food.asList()]
    if len(foodDistances) > 0:
        score += 20.0 / min(foodDistances)
    capsuleDistances = [manhattanDistance(pacmanPos, cap) for cap in capsules]
    if len(capsuleDistances) > 0:
        score += 30.0 / min(capsuleDistances)
    for ghost in ghostStates:
        ghostPos = ghost.getPosition()
        dist = manhattanDistance(pacmanPos, ghostPos)
        if ghost.getScaredTimer() > 0:
            score += 200 / (dist + 1)
        else:
            if dist < 2:
                score -= 1500
            else:
                score -= 20.0 / dist
    return score

class ContestAgent(MultiAgentSearchAgent):
    """
    Your agent for the mini-contest.

    You can use any method you want and search to any depth you want.
    Just remember that the mini-contest is timed, so you have to trade off speed and computation.

    Ghosts don't behave randomly anymore, but they aren't perfect either -- they'll usually
    just make a beeline straight towards Pacman (or away if they're scared!)

    Method to Implement:

    `pacai.agents.base.BaseAgent.getAction`
    """

    def __init__(self, index, **kwargs):
        super().__init__(index, **kwargs)