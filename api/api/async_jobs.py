import logging
from multiprocessing import Lock
from typing import Any, Callable, Optional

import apscheduler.events
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class AsyncJobRunner:
    """
    A singleton class that runs jobs immediately in the background.

    It uses APScheduler under the hood to run jobs in the background. It exposes methods to start and stop the
    scheduler and keeps track of the amount of times the scheduler has been started and stopped to ensure that the
    scheduler is only stopped when all references to it have been removed.

    As APScheduler removes jobs from the jobstore as soon as they are executed, this class keeps track of the job ids
    and removes them from the list only when the job has finished (either successfully or with an error).

    Though APScheduler allows adding jobs that run repeatedly, etc., this class only supports adding jobs that run
    immediately and only once.

    Attributes:
        _job_ids: A list of job ids that have been added to the scheduler.

        _instance: The singleton instance of the class.
        _scheduler: The APScheduler instance.
        _lock: A lock to ensure thread safety.
        _ref_count: The reference count of the scheduler.
    """

    _instance = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _lock = Lock()
    _ref_count = 0

    def __new__(cls):
        """
        Singleton pattern to ensure only one instance of the class is created.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._job_ids = set()
        return cls._instance

    @classmethod
    def start_scheduler(cls):
        """
        Create a new scheduler instance if it does not exist and increase the reference count.

        This method is thread-safe as it uses a lock to prevent multiple workers from starting the scheduler at the same
        time.
        """
        with cls._lock:
            if cls._scheduler is None:
                cls._scheduler = AsyncIOScheduler()
                cls._scheduler.start()
                logger.info("Scheduler started")
            cls._ref_count += 1
            logger.debug(f"Reference count: {cls._ref_count}")

    @classmethod
    def shutdown_scheduler(cls):
        """
        Stop the scheduler if the reference count is zero and remove the instance.

        This method is thread-safe as it uses a lock to prevent multiple workers from stopping the scheduler at the same
        time.
        """
        with cls._lock:
            if cls._ref_count > 0:
                cls._ref_count -= 1
                logger.debug(f"Reference count: {cls._ref_count}")

            if cls._ref_count == 0 and cls._scheduler is not None:
                logger.info("Shutting down scheduler")
                cls._scheduler.shutdown()
                cls._scheduler = None

    def add_job(
        self,
        func: callable,
        job_id: str,
        args: Optional[tuple[Any]] = None,
        kwargs: Optional[dict[str, Any]] = None,
        listener: Optional[Callable[[apscheduler.events.JobEvent], None]] = None,
    ):
        """
        Add a job to the scheduler running it immediately.

        :param func: The function to run.
        :param job_id: The job id.
        :param args: The arguments to pass to the function.
        :param kwargs: The keyword arguments to pass to the function.
        :param listener: A listener to call with the job events.

        :raises ValueError: If a job with the given id already exists.
        """
        if self.job_exists(job_id):
            raise ValueError(f"Job with id '{job_id}' already exists")

        self._job_ids.add(job_id)
        try:
            self._scheduler.add_job(func, args=args, kwargs=kwargs, id=job_id)
            logger.info(f"Added job '{job_id}' to the scheduler")
        except Exception:
            self._job_ids.remove(job_id)
            raise

        def _job_listener(event):
            if event.job_id == job_id:
                if listener:
                    listener(event)
                if (
                    event.code == apscheduler.events.EVENT_JOB_ERROR
                    or event.code == apscheduler.events.EVENT_JOB_EXECUTED
                ):
                    if event.code == apscheduler.events.EVENT_JOB_ERROR:
                        logger.error(
                            f"Job '{job_id}' failed unexpectedly",
                            exc_info=event.exception,
                        )
                    if event.code == apscheduler.events.EVENT_JOB_EXECUTED:
                        logger.info(f"Job '{job_id}' executed successfully")

                    logger.debug(f"Removing job '{job_id}' from job ids")
                    self._job_ids.remove(job_id)
                    self._scheduler.remove_listener(_job_listener)

        self._scheduler.add_listener(
            _job_listener,
            apscheduler.events.EVENT_JOB_EXECUTED
            | apscheduler.events.EVENT_JOB_ERROR
            | apscheduler.events.EVENT_JOB_SUBMITTED,
        )

    def job_exists(self, job_id: str) -> bool:
        """
        Check if a job with the given id exists.

        :param job_id: The job id.
        :return: True if the job exists, False otherwise.
        """
        return job_id in self._job_ids
