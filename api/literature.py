from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from services.literature_service import literature_service
from api.auth import get_current_user
from models.user import User
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Pydantic models
class AbstractRequest(BaseModel):
    abstract: str = Field(..., min_length=100, max_length=10000)
    title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    
    class Config:
        schema_extra = {
            "example": {
                "abstract": "Background: Cancer is a leading cause of death worldwide. This study investigates novel biomarkers for early detection. Methods: We analyzed RNA-seq data from 500 patients. Results: We identified 15 genes significantly associated with cancer progression. Conclusion: These biomarkers show promise for clinical application.",
                "title": "Novel Biomarkers for Cancer Detection",
                "authors": "Smith, J., Johnson, M., Brown, K.",
                "journal": "Nature Medicine",
                "publication_date": "2024-01-15",
                "doi": "10.1038/s41591-024-0001-1",
                "pmid": "38123456"
            }
        }

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)
    session_id: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What biomarkers were identified in this study?",
                "session_id": 1
            }
        }

class LiteratureSummaryResponse(BaseModel):
    id: int
    title: str
    authors: Optional[str]
    journal: Optional[str]
    publication_date: Optional[datetime]
    doi: Optional[str]
    pmid: Optional[str]
    source_type: str
    summary: Optional[str]
    key_findings: Optional[List[str]]
    biomarkers: Optional[List[str]]
    genes: Optional[List[str]]
    diseases: Optional[List[str]]
    methods: Optional[List[str]]
    confidence_score: Optional[float]
    processing_status: str
    created_at: Optional[datetime]

class ChatSessionResponse(BaseModel):
    id: int
    session_name: str
    literature_summary_id: int
    total_messages: int
    is_active: bool
    created_at: Optional[datetime]
    last_activity: Optional[datetime]

class ChatMessageResponse(BaseModel):
    id: int
    message_type: str
    content: str
    citations: Optional[List[str]]
    confidence_score: Optional[float]
    created_at: Optional[datetime]

@router.post("/abstract", status_code=status.HTTP_201_CREATED)
async def process_abstract(
    abstract_request: AbstractRequest,
    current_user: User = Depends(get_current_user)
):
    """Process and summarize research paper abstract"""
    try:
        # Convert request to metadata dict
        metadata = {
            "title": abstract_request.title,
            "authors": abstract_request.authors,
            "journal": abstract_request.journal,
            "publication_date": abstract_request.publication_date,
            "doi": abstract_request.doi,
            "pmid": abstract_request.pmid,
            "source_url": str(abstract_request.source_url) if abstract_request.source_url else None
        }
        
        # Process abstract
        result = await literature_service.process_abstract(
            user_id=current_user.id,
            abstract_text=abstract_request.abstract,
            metadata=metadata
        )
        
        logger.info(f"Abstract processed by user {current_user.id}")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing abstract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during abstract processing"
        )

@router.post("/pdf", status_code=status.HTTP_201_CREATED)
async def process_pdf(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Process and summarize PDF research paper"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata format"
            )
        
        # Add filename to metadata
        metadata_dict["file_name"] = file.filename
        
        # Read PDF content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty PDF file"
            )
        
        # Process PDF
        result = await literature_service.process_pdf(
            user_id=current_user.id,
            pdf_data=pdf_content,
            metadata=metadata_dict
        )
        
        logger.info(f"PDF processed by user {current_user.id}: {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during PDF processing"
        )

@router.get("/summaries", response_model=Dict[str, Any])
async def list_literature_summaries(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """List user's literature summaries"""
    try:
        result = await literature_service.list_literature_summaries(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing literature summaries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/summaries/{summary_id}")
async def get_literature_summary(
    summary_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get literature summary details"""
    try:
        from models.database import get_db
        from models.literature import LiteratureSummary
        
        db = next(get_db())
        summary = db.query(LiteratureSummary).filter(
            LiteratureSummary.id == summary_id,
            LiteratureSummary.user_id == current_user.id
        ).first()
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Literature summary not found"
            )
        
        return summary.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting literature summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/summaries/{summary_id}")
async def delete_literature_summary(
    summary_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete literature summary"""
    try:
        from models.database import get_db
        from models.literature import LiteratureSummary, ChatSession, ChatMessage
        
        db = next(get_db())
        
        # Check if summary exists and belongs to user
        summary = db.query(LiteratureSummary).filter(
            LiteratureSummary.id == summary_id,
            LiteratureSummary.user_id == current_user.id
        ).first()
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Literature summary not found"
            )
        
        # Delete related chat messages and sessions
        chat_sessions = db.query(ChatSession).filter(
            ChatSession.literature_summary_id == summary_id
        ).all()
        
        for session in chat_sessions:
            db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
            db.delete(session)
        
        # Delete summary
        db.delete(summary)
        db.commit()
        
        logger.info(f"Literature summary {summary_id} deleted by user {current_user.id}")
        
        return {"message": "Literature summary deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting literature summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/chat/{literature_id}")
async def chat_with_paper(
    literature_id: int,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat with research paper using Q&A"""
    try:
        result = await literature_service.chat_with_paper(
            user_id=current_user.id,
            literature_id=literature_id,
            question=chat_request.question,
            session_id=chat_request.session_id
        )
        
        logger.info(f"Chat with paper {literature_id} by user {current_user.id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat with paper: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during chat"
        )

@router.get("/chat/sessions")
async def get_chat_sessions(
    literature_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's chat sessions"""
    try:
        result = await literature_service.get_chat_sessions(
            user_id=current_user.id,
            literature_id=literature_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get chat messages for a session"""
    try:
        result = await literature_service.get_chat_messages(
            session_id=session_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete chat session"""
    try:
        from models.database import get_db
        from models.literature import ChatSession, ChatMessage
        
        db = next(get_db())
        
        # Check if session exists and belongs to user
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Delete messages
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        
        # Delete session
        db.delete(session)
        db.commit()
        
        logger.info(f"Chat session {session_id} deleted by user {current_user.id}")
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/search")
async def search_literature(
    query: str,
    literature_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Search user's literature summaries"""
    try:
        from models.database import get_db
        from models.literature import LiteratureSummary
        from sqlalchemy import or_
        
        db = next(get_db())
        
        # Build search query
        search_query = db.query(LiteratureSummary).filter(
            LiteratureSummary.user_id == current_user.id
        )
        
        # Add text search
        if query:
            search_query = search_query.filter(
                or_(
                    LiteratureSummary.title.ilike(f"%{query}%"),
                    LiteratureSummary.abstract.ilike(f"%{query}%"),
                    LiteratureSummary.summary.ilike(f"%{query}%"),
                    LiteratureSummary.authors.ilike(f"%{query}%")
                )
            )
        
        # Add type filter
        if literature_type:
            search_query = search_query.filter(
                LiteratureSummary.source_type == literature_type
            )
        
        # Execute search
        results = search_query.offset(skip).limit(limit).all()
        total = search_query.count()
        
        return {
            "results": [result.to_dict() for result in results],
            "total": total,
            "skip": skip,
            "limit": limit,
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error searching literature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_literature_stats(
    current_user: User = Depends(get_current_user)
):
    """Get user's literature processing statistics"""
    try:
        from models.database import get_db
        from models.literature import LiteratureSummary, ChatSession, ChatMessage
        from sqlalchemy import func
        
        db = next(get_db())
        
        # Get summary statistics
        total_summaries = db.query(LiteratureSummary).filter(
            LiteratureSummary.user_id == current_user.id
        ).count()
        
        completed_summaries = db.query(LiteratureSummary).filter(
            LiteratureSummary.user_id == current_user.id,
            LiteratureSummary.processing_status == "completed"
        ).count()
        
        # Get chat statistics
        total_chat_sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).count()
        
        total_chat_messages = db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).count()
        
        # Get processing status breakdown
        status_breakdown = db.query(
            LiteratureSummary.processing_status,
            func.count(LiteratureSummary.id)
        ).filter(
            LiteratureSummary.user_id == current_user.id
        ).group_by(LiteratureSummary.processing_status).all()
        
        # Get source type breakdown
        source_breakdown = db.query(
            LiteratureSummary.source_type,
            func.count(LiteratureSummary.id)
        ).filter(
            LiteratureSummary.user_id == current_user.id
        ).group_by(LiteratureSummary.source_type).all()
        
        return {
            "total_summaries": total_summaries,
            "completed_summaries": completed_summaries,
            "total_chat_sessions": total_chat_sessions,
            "total_chat_messages": total_chat_messages,
            "status_breakdown": dict(status_breakdown),
            "source_breakdown": dict(source_breakdown)
        }
        
    except Exception as e:
        logger.error(f"Error getting literature stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def literature_health_check():
    """Health check for literature service"""
    return {
        "service": "literature",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }