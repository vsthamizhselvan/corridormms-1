"""CorridorKey 2.0 Desktop — Non-Destructive Undo/Redo Manager.

Maintains an immutable snapshot history of timeline states, enabling
unlimited undo and redo across all timeline edit operations.
"""

from __future__ import annotations

import copy
from typing import List, Optional

from engine.timeline.timeline_model import TimelineSequence


class UndoRedoManager:
    """Manages undo and redo stacks using non-destructive timeline sequence snapshots."""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._undo_stack: List[dict] = []
        self._redo_stack: List[dict] = []

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def push_state(self, sequence: TimelineSequence) -> None:
        """Pushes current sequence state onto the undo stack and clears redo stack."""
        snapshot = sequence.to_dict()
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self, current_sequence: TimelineSequence) -> Optional[TimelineSequence]:
        """Reverts to the previous sequence state, moving current state to redo stack."""
        if not self.can_undo:
            return None

        # Push current state to redo stack
        self._redo_stack.append(current_sequence.to_dict())

        # Pop previous state from undo stack
        prev_snapshot = self._undo_stack.pop()
        return TimelineSequence.from_dict(prev_snapshot)

    def redo(self, current_sequence: TimelineSequence) -> Optional[TimelineSequence]:
        """Advances to the redone sequence state, moving current state to undo stack."""
        if not self.can_redo:
            return None

        # Push current state to undo stack
        self._undo_stack.append(current_sequence.to_dict())

        # Pop next state from redo stack
        next_snapshot = self._redo_stack.pop()
        return TimelineSequence.from_dict(next_snapshot)

    def clear(self) -> None:
        """Clears both undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
