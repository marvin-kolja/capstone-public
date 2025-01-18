import asyncio

import pytest
from unittest.mock import MagicMock, patch
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.async_jobs import AsyncJobRunner


@pytest.fixture
def job_runner():
    """
    Fixture to provide a fresh instance of AsyncJobRunner before each test.
    """
    AsyncJobRunner._instance = None
    AsyncJobRunner._scheduler = None
    AsyncJobRunner._ref_count = 0
    yield AsyncJobRunner()


def test_singleton_behavior(job_runner):
    """
    GIVEN: A new instance of AsyncJobRunner

    WHEN: Another instance is created

    THEN: Both instances should be the same object.
    """
    runner1 = AsyncJobRunner()
    runner2 = AsyncJobRunner()
    assert runner1 is runner2, "AsyncJobRunner should be a singleton."


@pytest.mark.asyncio
async def test_scheduler_starts_once(job_runner):
    """
    GIVEN: A new instance of AsyncJobRunner

    WHEN: The scheduler is started

    THEN: The scheduler should only start once.
    """
    assert AsyncJobRunner._scheduler is None

    with patch.object(AsyncIOScheduler, "start") as mock_start:
        job_runner.start_scheduler()

        scheduler = AsyncJobRunner._scheduler

        assert isinstance(scheduler, AsyncIOScheduler)
        assert AsyncJobRunner._ref_count == 1

        job_runner.start_scheduler()
        assert AsyncJobRunner._ref_count == 2
        assert (
            scheduler is AsyncJobRunner._scheduler
        ), "Scheduler should not be recreated."

        mock_start.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_shuts_down_correctly(job_runner):
    """
    GIVEN: A AsyncJobRunner singleton

    WHEN: The scheduler multiple times.
    AND: The scheduler is shut an equal number of times.

    THEN: The scheduler should be stopped when the reference count reaches 0.
    """
    with patch.object(AsyncIOScheduler, "shutdown") as mock_shutdown:
        job_runner.start_scheduler()
        job_runner.start_scheduler()
        assert AsyncJobRunner._ref_count == 2

        job_runner.shutdown_scheduler()
        assert AsyncJobRunner._ref_count == 1
        assert AsyncJobRunner._scheduler is not None  # Scheduler should still be active

        job_runner.shutdown_scheduler()
        assert AsyncJobRunner._ref_count == 0
        assert AsyncJobRunner._scheduler is None  # Scheduler should be stopped

        mock_shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_add_job_successfully(job_runner):
    """
    GIVEN: A running scheduler

    WHEN: A new job is added

    THEN: The job id should be added to the job ids list.
    AND: The job should be added to the scheduler.
    """
    job_runner.start_scheduler()

    mock_func = MagicMock()
    job_id = "test_job"

    with patch.object(AsyncIOScheduler, "add_job") as mock_add_job:
        job_runner.add_job(mock_func, job_id)
        assert job_runner.job_exists(job_id), "Job should be added successfully."
        mock_add_job.assert_called_once()


@pytest.mark.asyncio
async def test_add_duplicate_job(job_runner):
    """
    GIVEN: A running scheduler

    WHEN: A job is added with the same id as an existing job

    THEN: The job should be added successfully.
    """
    job_runner.start_scheduler()

    mock_func = MagicMock()
    job_id = "test_job"

    with patch.object(AsyncIOScheduler, "add_job") as mock_add_job:
        job_runner.add_job(mock_func, job_id)

        with pytest.raises(ValueError):
            job_runner.add_job(mock_func, job_id)  # Try to add the same job again


@pytest.mark.asyncio
async def test_job_execution_and_removal(job_runner):
    """
    GIVEN: A running scheduler

    WHEN: A job is executed and finishes

    THEN: The job should be removed from the job list.
    """
    job_runner.start_scheduler()

    async def test_func():
        await asyncio.sleep(0.1)

    job_id = "test_execution"
    job_runner.add_job(test_func, job_id)

    assert job_runner.job_exists(
        job_id
    ), "Job should be in the job list before execution."

    await asyncio.sleep(0.2)  # Wait for the job to finish

    assert not job_runner.job_exists(job_id), "Job should be removed after execution."


@pytest.mark.asyncio
async def test_job_failure(job_runner):
    """
    GIVEN: A running scheduler

    WHEN: A job fails unexpectedly

    THEN: The job should be removed from the job list.
    """
    job_runner.start_scheduler()

    def test_func():
        raise ValueError("Intentional Error")

    job_id = "test_failure"
    job_runner.add_job(test_func, job_id)

    assert job_runner.job_exists(job_id), "Job should be added before execution."

    await asyncio.sleep(0.1)  # Wait for the job to finish

    assert not job_runner.job_exists(job_id), "Failed job should be removed."
