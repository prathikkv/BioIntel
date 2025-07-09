"""
Enterprise Models
Database models for team collaboration and enterprise features
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
import enum

class TeamRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class Team(Base):
    """Team model for collaboration"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_type = Column(String(50), default="research")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User", back_populates="created_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="team", cascade="all, delete-orphan")
    shared_analyses = relationship("SharedAnalysis", back_populates="team")
    api_keys = relationship("APIKey", back_populates="team")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "team_type": self.team_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "member_count": len(self.members) if self.members else 0
        }

class TeamMember(Base):
    """Team membership model"""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    added_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    added_by_user = relationship("User", foreign_keys=[added_by])
    
    def to_dict(self):
        return {
            "id": self.id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "role": self.role.value if self.role else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "is_active": self.is_active
        }

class Workspace(Base):
    """Workspace model for organizing team work"""
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    team = relationship("Team", back_populates="workspaces")
    creator = relationship("User", back_populates="created_workspaces")
    shared_analyses = relationship("SharedAnalysis", back_populates="workspace")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "team_id": self.team_id,
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "analysis_count": len(self.shared_analyses) if self.shared_analyses else 0
        }

class SharedAnalysis(Base):
    """Shared analysis results model"""
    __tablename__ = "shared_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    analysis_type = Column(String(100), nullable=False)
    analysis_results = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="shared_analyses")
    team = relationship("Team", back_populates="shared_analyses")
    workspace = relationship("Workspace", back_populates="shared_analyses")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "analysis_type": self.analysis_type,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "workspace_id": self.workspace_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "has_results": bool(self.analysis_results)
        }

class APIKey(Base):
    """API key model for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    permissions = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    last_used = Column(DateTime(timezone=True))  # Added for compatibility
    rate_limit = Column(Integer, default=100)  # Added for rate limiting
    usage_count = Column(Integer, default=0)  # Added for usage tracking
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    team = relationship("Team", back_populates="api_keys")
    usage_logs = relationship("UsageLog", back_populates="api_key")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "permissions": self.permissions,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "rate_limit": self.rate_limit,
            "usage_count": self.usage_count,
            "is_active": self.is_active
        }

class UsageLog(Base):
    """API usage logging model"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    execution_time = Column(Integer)  # milliseconds
    status_code = Column(Integer, nullable=False)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    user = relationship("User", back_populates="usage_logs")
    team = relationship("Team")
    
    def to_dict(self):
        return {
            "id": self.id,
            "api_key_id": self.api_key_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "execution_time": self.execution_time,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }