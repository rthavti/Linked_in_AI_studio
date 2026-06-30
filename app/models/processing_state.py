"""
Processing State Model

Defines the ProcessingState data model for tracking workflow steps.

Author: LinkedIn AI Studio
"""

from pydantic import BaseModel


class ProcessingState(BaseModel):
    id: int
    topic_id: int
    step: str
    completed: bool

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            topic_id=row["topic_id"],
            step=row["step"],
            completed=bool(row["completed"]),
        )