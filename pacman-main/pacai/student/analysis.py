NOT_POSSIBLE = None

def question2():
    """
    Reduce noise to make the agent take the risk of crossing the bridge.
    """
    answerDiscount = 0.9
    answerNoise = 0.0
    return answerDiscount, answerNoise

def question3a():
    """
    Prefer the close exit, risking the cliff.
    """
    answerDiscount = 0.1
    answerNoise = 0.0
    answerLivingReward = -0.1
    return answerDiscount, answerNoise, answerLivingReward

def question3b():
    """
    Prefer the close exit, avoiding the cliff.
    """
    answerDiscount = 0.95
    answerNoise = 0.4
    answerLivingReward = -0.1
    return answerDiscount, answerNoise, answerLivingReward

def question3c():
    """
    Prefer the distant exit, risking the cliff.
    """
    answerDiscount = 0.9
    answerNoise = 0.1
    answerLivingReward = -0.5
    return answerDiscount, answerNoise, answerLivingReward

def question3d():
    """
    Prefer the distant exit, avoiding the cliff.
    """
    answerDiscount = 0.9
    answerNoise = 0.2
    answerLivingReward = -0.2
    return answerDiscount, answerNoise, answerLivingReward

def question3e():
    """
    Avoid both exits, also avoiding the cliff.
    """
    answerDiscount = 0.1
    answerNoise = 0.2
    answerLivingReward = 2.0
    return answerDiscount, answerNoise, answerLivingReward

def question6():
    """
    Set epsilon and learning rate to ensure the optimal policy is learned.
    """
    answerEpsilon = 0.1
    answerLearningRate = 0.0
    return answerEpsilon, answerLearningRate

if __name__ == '__main__':
    questions = [
        question2,
        question3a,
        question3b,
        question3c,
        question3d,
        question3e,
        question6,
    ]

    print('Answers to analysis questions:')
    for question in questions:
        response = question()
        print('    Question %-10s:	%s' % (question.__name__, str(response)))