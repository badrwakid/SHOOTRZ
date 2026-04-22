import numpy as np
from mabwiser.mab import MAB, LearningPolicy

def initialize_bandit(arms):
    """
    Initialize a LinUCB contextual bandit with safe dummy training.
    """
    unique_arms = list(set(arms))

    bandit = MAB(
        arms=unique_arms,
        learning_policy=LearningPolicy.LinUCB(alpha=1.4)
    )

    # Dummy warm-start (required by mabwiser)
    dummy_context = np.array([[3, 0.4, 0.7, 0.2, 12]], dtype="float32")
    dummy_decision = unique_arms[0]
    dummy_reward = 0.5

    bandit.fit(
        decisions=[dummy_decision],
        rewards=[dummy_reward],
        contexts=dummy_context
    )

    return bandit
