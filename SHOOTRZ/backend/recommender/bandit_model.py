import numpy as np
from mabwiser.mab import MAB, LearningPolicy

def initialize_bandit(arms):
    """
    Create a LinUCB contextual bandit and fit it with a dummy point.
    """
    bandit = MAB(
        arms=list(set(arms)),
        learning_policy=LearningPolicy.LinUCB(alpha=1.4)
    )

    # Initial dummy training data
    dummy_context = np.array([[3, 0.4, 0.7, 0.2, 12]], dtype="float32")
    bandit.fit(
        decisions=[arms[0]],
        rewards=[0.5],
        contexts=dummy_context
    )

    return bandit
