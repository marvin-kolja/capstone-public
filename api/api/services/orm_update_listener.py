import asyncio
import logging
from typing import Type, TypeVar, AsyncGenerator, Generic, Optional

from sqlalchemy import event
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)


T = TypeVar("T", bound=SQLModel)


class ModelUpdateListener(Generic[T]):
    def __init__(self, db_instance: T, model_class: Type[T]):
        self._model_class = model_class
        self._queue: asyncio.Queue[T] = asyncio.Queue()
        self._queue.put_nowait(
            model_class.model_validate(db_instance)
        )  # Queue initial state
        self._stop_event = asyncio.Event()

    def stop(self):
        self._stop_event.set()

    async def _stream_model_updates(self) -> AsyncGenerator[Optional[T], None]:
        """
        Stream updated model instances from the queue until the stop event is set.
        """
        try:
            while True:
                if self._stop_event.is_set():
                    logger.debug("Request disconnected, stopping listener")
                    break

                try:
                    public_instance = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.1)
                    yield None
                    continue

                logger.debug(f"Yielding updated '{self._model_class.__name__}'")
                yield public_instance
        except asyncio.CancelledError:
            pass

    def _on_model_update(self, mapper, connection, target):
        """
        Listener callback to enqueue updated model instance.
        """
        logger.debug(f"'{self._model_class.__name__}' updated, adding to queue")
        self._queue.put_nowait(self._model_class.model_validate(target))

    async def listen(self) -> AsyncGenerator[Optional[T], None]:
        """
        Register the update listener and stream updated model instances. Remove the listener when done.
        """
        logger.debug(f"Adding update listener for '{self._model_class.__name__}'")
        event.listen(self._model_class, "after_update", self._on_model_update)

        try:
            async for update in self._stream_model_updates():
                yield update
        finally:
            logger.debug(f"Removing update listener for '{self._model_class.__name__}'")
            event.remove(self._model_class, "after_update", self._on_model_update)
