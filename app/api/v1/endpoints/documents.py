from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage_factory import get_document_repository
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentOut, DocumentListResponse
from app.services.document_service import DocumentService
from app.core.exceptions import DocumentNotFoundError

router = APIRouter()


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Dependency to get document service."""
    repository = get_document_repository(db)
    return DocumentService(repository)


@router.post("/", response_model=DocumentOut, status_code=201)
def create_document(
    *,
    db: Session = Depends(get_db),
    document_in: DocumentCreate,
    service: DocumentService = Depends(get_document_service)
):
    """Create a new document."""
    return service.create_document(
        db, 
        title=document_in.title,
        owner_id=None  # No authentication in this version
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    *,
    db: Session = Depends(get_db),
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Get a document by ID."""
    try:
        return service.get_document(db, document_id=document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document(
    *,
    db: Session = Depends(get_db),
    document_id: str,
    document_in: DocumentUpdate,
    service: DocumentService = Depends(get_document_service)
):
    """Update a document's title and/or deleted status."""
    try:
        return service.update_document(
            db,
            document_id=document_id,
            title=document_in.title,
            deleted=document_in.deleted
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    *,
    db: Session = Depends(get_db),
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Soft delete a document."""
    try:
        service.delete_document(db, document_id=document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    *,
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Search query for document titles"),
    include_deleted: bool = Query(False, description="Include soft-deleted documents"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    service: DocumentService = Depends(get_document_service)
):
    """List documents with optional filtering and pagination."""
    return service.get_documents(
        db,
        query=query,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size
    )
