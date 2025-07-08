from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
from datetime import datetime
from typing import Dict, Any, List

class LiteratureSummary(Base):
    """Literature summary model for storing research paper summaries"""
    
    __tablename__ = "literature_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=True)
    journal = Column(String(255), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    doi = Column(String(255), nullable=True)
    pmid = Column(String(50), nullable=True)
    
    # Paper content
    abstract = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    
    # Processing metadata
    source_type = Column(String(50), nullable=False)  # abstract, full_paper, url
    source_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    # AI-generated summary
    summary = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)
    biomarkers = Column(JSON, nullable=True)
    genes = Column(JSON, nullable=True)
    diseases = Column(JSON, nullable=True)
    methods = Column(JSON, nullable=True)
    
    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_log = Column(Text, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="literature_summaries")
    chat_sessions = relationship("ChatSession", back_populates="literature_summary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert literature summary to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "doi": self.doi,
            "pmid": self.pmid,
            "abstract": self.abstract,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "file_name": self.file_name,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "biomarkers": self.biomarkers,
            "genes": self.genes,
            "diseases": self.diseases,
            "methods": self.methods,
            "processing_status": self.processing_status,
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<LiteratureSummary(title='{self.title[:50]}...', user_id={self.user_id})>"

class ChatSession(Base):
    """Chat session model for paper Q&A interactions"""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    literature_summary_id = Column(Integer, ForeignKey("literature_summaries.id"), nullable=False)
    session_name = Column(String(255), nullable=False)
    
    # Session metadata
    total_messages = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    literature_summary = relationship("LiteratureSummary", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat session to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "literature_summary_id": self.literature_summary_id,
            "session_name": self.session_name,
            "total_messages": self.total_messages,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }
    
    def __repr__(self):
        return f"<ChatSession(session_name='{self.session_name}', user_id={self.user_id})>"

class ChatMessage(Base):
    """Chat message model for storing Q&A interactions"""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # Message metadata
    tokens_used = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    
    # Citations and references
    citations = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat message to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "tokens_used": self.tokens_used,
            "response_time": self.response_time,
            "citations": self.citations,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<ChatMessage(message_type='{self.message_type}', session_id={self.session_id})>"

class KnowledgeBase(Base):
    """Knowledge base model for storing structured biomedical knowledge"""
    
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # gene, protein, disease, drug, etc.
    entity_id = Column(String(100), nullable=False)
    entity_name = Column(String(255), nullable=False)
    
    # Entity information
    description = Column(Text, nullable=True)
    synonyms = Column(JSON, nullable=True)
    
    # Relationships
    related_entities = Column(JSON, nullable=True)
    
    # Source information
    source_papers = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge base entry to dictionary"""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "description": self.description,
            "synonyms": self.synonyms,
            "related_entities": self.related_entities,
            "source_papers": self.source_papers,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<KnowledgeBase(entity_name='{self.entity_name}', entity_type='{self.entity_type}')>"

class Report(Base):
    """Report model for storing generated reports"""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # analysis, literature, combined
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Report content
    content = Column(Text, nullable=False)
    
    # Associated data
    dataset_ids = Column(JSON, nullable=True)
    analysis_job_ids = Column(JSON, nullable=True)
    literature_summary_ids = Column(JSON, nullable=True)
    
    # Report metadata
    template_used = Column(String(100), nullable=True)
    format_type = Column(String(50), default="html")  # html, pdf, docx
    
    # File information
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Generation metadata
    generation_time = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reports")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "dataset_ids": self.dataset_ids,
            "analysis_job_ids": self.analysis_job_ids,
            "literature_summary_ids": self.literature_summary_ids,
            "template_used": self.template_used,
            "format_type": self.format_type,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "generation_time": self.generation_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Report(title='{self.title}', report_type='{self.report_type}')>"