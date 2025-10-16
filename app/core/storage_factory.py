"""
Storage factory for creating appropriate repository instances based on storage mode.
"""

from typing import Union, Any
from sqlalchemy.orm import Session

from app.core.config import settings, StorageMode
from app.core.memory_storage import memory_storage
from app.repositories.document_repository import DocumentRepository
from app.repositories.memory_document_repository import MemoryDocumentRepository


def get_document_repository(db: Session = None) -> Union[DocumentRepository, MemoryDocumentRepository]:
    """
    Get the appropriate document repository based on storage mode.
    
    Args:
        db: Database session (required for SQLite mode, ignored for memory mode)
        
    Returns:
        Document repository instance
    """
    if settings.storage_mode == StorageMode.MEMORY:
        return MemoryDocumentRepository()
    else:
        return DocumentRepository()


def get_storage_mode() -> StorageMode:
    """Get the current storage mode."""
    return settings.storage_mode


def is_memory_mode() -> bool:
    """Check if running in memory mode."""
    return settings.storage_mode == StorageMode.MEMORY


def clear_storage():
    """Clear all storage data. Used for testing."""
    if is_memory_mode():
        memory_storage.clear_all()
    else:
        # For SQLite mode, we would need to clear tables
        # This is handled by the existing clear_tables() function
        pass
