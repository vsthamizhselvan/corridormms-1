"""CorridorKey 2.0 Desktop — Bounded Frame Buffer with Backpressure.

Provides a thread-safe bounded queue mechanism ensuring that fast video decoding
never overruns system RAM while neural network inference or video encoding is processing.
"""

from __future__ import annotations

import queue
import threading
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class BoundedFrameQueue(Generic[T]):
    """Thread-safe bounded queue enforcing backpressure between pipeline stages."""

    def __init__(self, maxsize: int = 16):
        self.maxsize = maxsize
        self._q: queue.Queue = queue.Queue(maxsize=maxsize)
        self._stop_event = threading.Event()
        self._items_pushed = 0
        self._items_popped = 0

    def put(self, item: T, timeout: float = 0.5) -> bool:
        """Puts an item into the queue. Blocks if full (backpressure). Returns False if aborted."""
        while not self._stop_event.is_set():
            try:
                self._q.put(item, block=True, timeout=timeout)
                self._items_pushed += 1
                return True
            except queue.Full:
                continue
        return False

    def get(self, timeout: float = 0.5) -> Optional[T]:
        """Gets an item from the queue. Blocks if empty. Returns None on abort/timeout."""
        while not self._stop_event.is_set():
            try:
                item = self._q.get(block=True, timeout=timeout)
                self._items_popped += 1
                return item
            except queue.Empty:
                if self._stop_event.is_set():
                    return None
                continue
        return None

    def task_done(self) -> None:
        self._q.task_done()

    def abort(self) -> None:
        """Signals abort and empties pending items to unblock waiting threads."""
        self._stop_event.set()
        while not self._q.empty():
            try:
                self._q.get_nowait()
                self._q.task_done()
            except Exception:
                break

    @property
    def is_aborted(self) -> bool:
        return self._stop_event.is_set()

    def qsize(self) -> int:
        return self._q.qsize()
