import pytest

from core.subprocesses.xctrace_command import Instrument
from core.test_session.metrics import (
    Metric,
    parse_metric_to_instrument,
    parse_metrics_to_instruments,
)


class TestMetricParser:
    @pytest.mark.parametrize(
        "metric,expected_instrument",
        [
            (Metric.cpu, Instrument.activity_monitor),
            (Metric.memory, Instrument.activity_monitor),
            (Metric.fps, Instrument.core_animation_fps),
            (Metric.gpu, Instrument.core_animation_fps),
        ],
    )
    def test_parse_metric_to_instrument(self, metric, expected_instrument):
        """
        GIVEN: a metric

        WHEN: the metric is parsed to an instrument

        THEN: the expected instrument is returned
        """
        assert parse_metric_to_instrument(metric) == expected_instrument

    def test_parse_metric_to_instrument_invalid_metric(self):
        """
        GIVEN: an invalid metric

        WHEN: the metric is parsed to an instrument

        THEN: a ValueError is raised
        """
        with pytest.raises(ValueError):
            parse_metric_to_instrument("invalid_metric")

    def test_parse_metrics_to_instruments_empty_list(self):
        """
        GIVEN: an empty list of metrics

        WHEN: the metrics are parsed to instruments

        THEN: an empty list is returned
        """
        assert parse_metrics_to_instruments([]) == []

    def test_parse_metrics_to_instruments_no_duplicates(self):
        """
        GIVEN: a list of metrics pointing to the same instrument

        WHEN: the metrics are parsed to instruments

        THEN: the expected instruments are returned without duplicates
        """
        metrics = [Metric.cpu, Metric.memory]
        assert parse_metrics_to_instruments(metrics) == [Instrument.activity_monitor]

    def test_parse_metrics_to_instruments_mixed_metrics(self):
        """
        GIVEN: a list of metrics pointing to different instruments

        WHEN: the metrics are parsed to instruments

        THEN: the expected instruments are returned
        """
        metrics = [Metric.cpu, Metric.memory, Metric.fps, Metric.gpu]

        result = parse_metrics_to_instruments(metrics)

        assert len(result) == len(
            [
                Instrument.activity_monitor,
                Instrument.core_animation_fps,
            ]
        )
        assert Instrument.activity_monitor in result
        assert Instrument.core_animation_fps in result

    def test_parse_metrics_to_instruments_invalid_metric(self):
        """
        GIVEN: a list of metrics with an invalid metric

        WHEN: the metrics are parsed to instruments

        THEN: a ValueError is raised
        """
        with pytest.raises(ValueError):
            parse_metrics_to_instruments(
                [
                    Metric.cpu,
                    "invalid_metric",
                ]
            )

    def test_parse_all_metrics(self):
        """
        GIVEN: a list of all metrics

        WHEN: the metrics are parsed to instruments

        THEN: no exceptions are raised
        """
        metrics = list(map(lambda m: m.value, Metric))

        parse_metrics_to_instruments(metrics)

        for metric in metrics:
            parse_metric_to_instrument(metric)
