from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Document model representing a collaborative document."""
    
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)  # UUID as string
    title = Column(String(256), nullable=False)
    owner_id = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    snapshots = relationship("DocumentSnapshot", back_populates="document", cascade="all, delete-orphan")
    updates = relationship("DocumentUpdate", back_populates="document", cascade="all, delete-orphan")


class DocumentSnapshot(Base, TimestampMixin):
    """Document snapshot model for storing CRDT snapshots."""
    
    __tablename__ = "document_snapshots"
    
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, primary_key=True)
    version = Column(Integer, nullable=False, primary_key=True)  # Composite primary key
    snapshot_blob = Column(BLOB, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="snapshots")


class DocumentUpdate(Base, TimestampMixin):
    """Document update model for storing CRDT delta updates."""
    
    __tablename__ = "document_updates"
    
    id = Column(String, primary_key=True)  # UUID as string
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    seq = Column(Integer, nullable=False)  # Sequence number
    op_id = Column(String, unique=True, nullable=False)  # Operation ID for deduplication
    actor_id = Column(String, nullable=False)
    delta_blob = Column(BLOB, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="updates")
