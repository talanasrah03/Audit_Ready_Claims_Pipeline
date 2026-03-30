"""
Consistency analysis module.

Goal:
Measure how stable and reliable AI outputs are when the same input is processed multiple times.

What this function does:
- Takes multiple AI outputs for the same input
- Finds the most common result
- Computes a consistency score

Important concept:
AI models can produce slightly different results for the same input.
This function helps detect how consistent (stable) the AI is.

Example:
If AI is run 5 times:
Output 1 → {"amount": 1000}
Output 2 → {"amount": 1000}
Output 3 → {"amount": 1200}
Output 4 → {"amount": 1000}
Output 5 → {"amount": 1000}

→ Most common = {"amount": 1000}
→ Appears 4 times

→ Consistency score = 4 / 5 = 0.8 (80%)
"""

import json   # Used to convert dictionaries to strings and back (for comparison)
from collections import Counter   # Used to count how many times each output appears


def compute_consistency(outputs):
    """
    Goal:
    Compute a consistency score from repeated AI outputs.

    Logic:
    - Convert each output into a comparable format (string)
    - Count how many times each output appears
    - Identify the most common output
    - Compute ratio of most common output to total outputs

    Example:
    outputs = [A, A, B, A, C]

    Step 1:
    Count occurrences:
    A → 3 times
    B → 1 time
    C → 1 time

    Step 2:
    Most common = A

    Step 3:
    Score = 3 / 5 = 0.6 (60%)

    Returns:
        - score → how consistent the AI is (between 0 and 1)
        - stable_output → the most reliable version

    Important assumption:
    This function expects outputs to contain at least one element.

    Why:
    - If outputs is empty, there is no "most common" result to select
    - The score cannot be computed without at least one output
    """


    # =========================
    # SERIALIZATION STEP
    # =========================
    """
    Goal:
    Convert dictionaries into strings for comparison.

    Why needed:
    Dictionaries are not directly hashable,
    which means they cannot be used inside Counter in a reliable way.

    Solution:
    Convert each dictionary into a JSON string.

    sort_keys=True:
    → ensures consistent ordering of keys

    Example:
    {"a":1, "b":2}
    {"b":2, "a":1}

    Without sorting:
    → they may look different as strings

    With sorting:
    → both become '{"a": 1, "b": 2}'
    """

    serialized = [json.dumps(output, sort_keys=True) for output in outputs]


    # =========================
    # COUNT OCCURRENCES
    # =========================
    """
    Goal:
    Count how many times each output appears.

    Counter:
    → creates a dictionary-like object where:
      - key = output
      - value = how many times it appears

    Example:
    ["A", "A", "B"] → {"A": 2, "B": 1}
    """

    counter = Counter(serialized)


    # =========================
    # MOST COMMON OUTPUT
    # =========================
    """
    Goal:
    Find the most frequent output.

    counter.most_common(1):
    → returns a list with the single most common item

    Example:
    {"A": 3, "B": 1}
    → [("A", 3)]

    [0]:
    → takes the first result from that list
    """

    most_common_output, count = counter.most_common(1)[0]


    # =========================
    # CONSISTENCY SCORE
    # =========================
    """
    Goal:
    Measure stability of AI output.

    Formula:
    score = count / total_outputs

    Example:
    4 identical outputs out of 5
    → score = 4 / 5 = 0.8 (80%)

    Meaning:
    - score = 1 → perfectly stable
    - lower score → more variation between runs
    """

    score = count / len(outputs)


    # =========================
    # RECONVERT TO DICTIONARY
    # =========================
    """
    Goal:
    Convert the most common output back into dictionary format.

    Logic:
    Reverse the earlier JSON conversion.

    Example:
    '{"amount": 1000}' → {"amount": 1000}
    """

    stable_output = json.loads(most_common_output)


    # =========================
    # RETURN RESULT
    # =========================
    """
    Returns:
    - score → consistency level between 0 and 1
    - stable_output → the most reliable output
    """

    return score, stable_output