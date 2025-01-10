from enum import StrEnum

from core.xc.commands.xctrace_command import Instrument


class Metric(StrEnum):
    """
    Enum of metrics that can be collected during a test session.
    """

    cpu = "cpu"
    memory = "memory"
    fps = "fps"
    gpu = "gpu"


def parse_metric_to_instrument(metric: Metric) -> Instrument:
    """
    Parses a metric to an instrument.
    :param metric: the metric to parse
    :return: the instrument

    :raises ValueError: if the metric is invalid
    """
    if metric == Metric.cpu:
        return Instrument.activity_monitor
    elif metric == Metric.memory:
        return Instrument.activity_monitor
    elif metric == Metric.fps:
        return Instrument.core_animation_fps
    elif metric == Metric.gpu:
        return Instrument.core_animation_fps
    else:
        raise ValueError(f"Invalid metric: {metric}")


def parse_metrics_to_instruments(metrics: list[Metric]) -> list[Instrument]:
    """
    Parses a list of metrics to a list of instruments.

    :param metrics: the metrics to parse
    :return: the instruments

    :raises ValueError: if any metric is invalid
    """
    instrument_set = set()

    for metric in metrics:
        instrument = parse_metric_to_instrument(metric)
        instrument_set.add(instrument)

    return list(instrument_set)
