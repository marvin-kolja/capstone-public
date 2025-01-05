from enum import StrEnum


class Metric(StrEnum):
    """
    Enum of metrics that can be collected during a test session.
    """

    cpu = "cpu"
    memory = "memory"
    fps = "fps"
    gpu = "gpu"
