import json
from collections import Counter


def compute_consistency(outputs):
    """
    Compute a consistency score from repeated AI outputs.

    Parameters:
        outputs (list[dict]): multiple AI outputs for the same input

    Returns:
        tuple:
            - score (float): ratio of most common output / total outputs
            - stable_output (dict): most common output
    """
    serialized = [json.dumps(output, sort_keys=True) for output in outputs]

    counter = Counter(serialized)
    most_common_output, count = counter.most_common(1)[0]

    score = count / len(outputs)
    stable_output = json.loads(most_common_output)

    return score, stable_output