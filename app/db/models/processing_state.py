"""
Processing State Model

Defines the SQLAlchemy ProcessingState model for tracking workflow steps.

Author: LinkedIn AI Studio
"""

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ProcessingState(Base):
    __tablename__ = "processing_state"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    step = Column(String, nullable=False)
    completed = Column(Boolean, nullable=False)
    timestamp = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    topic = relationship("Topic", back_populates="processing_states")