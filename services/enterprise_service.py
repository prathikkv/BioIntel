"""
Enterprise Service
Team collaboration, API access, and enterprise features for BioIntel.AI
"""

import logging
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
import pandas as pd
from collections import defaultdict
import hashlib
import secrets

from models.database import get_db
from models.user import User
from models.enterprise import Team, TeamMember, Workspace, SharedAnalysis, APIKey, UsageLog, TeamRole
from utils.logging import get_logger
from utils.security import security_utils
from services.research_workflows_service import research_workflows_service
from services.analysis_templates_service import analysis_templates_service

logger = get_logger(__name__)

class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"

class ResourceType(Enum):
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"
    DATASET = "dataset"
    REPORT = "report"
    WORKSPACE = "workspace"

@dataclass
class TeamPermission:
    """Team permission definition"""
    user_id: int
    resource_type: ResourceType
    resource_id: str
    permission_level: PermissionLevel
    granted_by: int
    granted_at: datetime

@dataclass
class APIUsage:
    """API usage tracking"""
    api_key: str
    endpoint: str
    method: str
    user_id: int
    team_id: Optional[int]
    timestamp: datetime
    execution_time: float
    status_code: int
    error_message: Optional[str]

@dataclass
class CollaborationEvent:
    """Collaboration event for activity tracking"""
    event_type: str
    user_id: int
    team_id: int
    resource_type: ResourceType
    resource_id: str
    details: Dict[str, Any]
    timestamp: datetime

class EnterpriseService:
    """Service for enterprise features and team collaboration"""
    
    def __init__(self):
        self.db = next(get_db())
        self.active_sessions = {}
        self.usage_cache = defaultdict(list)
    
    @staticmethod
    async def initialize():
        """Initialize enterprise service"""
        logger.info("Enterprise service initialized")
    
    # Team Management
    async def create_team(self, creator_id: int, team_name: str, description: str = "", 
                         team_type: str = "research") -> Dict[str, Any]:
        """Create a new team"""
        try:
            # Check if team name already exists for this user
            existing_team = self.db.query(Team).filter(
                and_(Team.name == team_name, Team.creator_id == creator_id)
            ).first()
            
            if existing_team:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Team name already exists"
                )
            
            # Create new team
            team = Team(
                name=team_name,
                description=description,
                creator_id=creator_id,
                team_type=team_type,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(team)
            self.db.commit()
            self.db.refresh(team)
            
            # Add creator as owner
            team_member = TeamMember(
                team_id=team.id,
                user_id=creator_id,
                role=TeamRole.OWNER,
                joined_at=datetime.utcnow(),
                added_by=creator_id
            )
            
            self.db.add(team_member)
            self.db.commit()
            
            # Create default workspace
            workspace = await self.create_workspace(
                team_id=team.id,
                creator_id=creator_id,
                name="Default Workspace",
                description="Default workspace for team collaboration"
            )
            
            logger.info(f"Team created: {team.name} (ID: {team.id})")
            
            return {
                "team_id": team.id,
                "team_name": team.name,
                "description": team.description,
                "creator_id": creator_id,
                "workspace_id": workspace["workspace_id"],
                "created_at": team.created_at.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def invite_team_member(self, team_id: int, inviter_id: int, 
                               user_email: str, role: TeamRole) -> Dict[str, Any]:
        """Invite a user to join a team"""
        try:
            # Check if inviter has permission
            inviter_membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == inviter_id)
            ).first()
            
            if not inviter_membership or inviter_membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to invite members"
                )
            
            # Find user by email
            user = self.db.query(User).filter(User.email == user_email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if user is already a member
            existing_membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user.id)
            ).first()
            
            if existing_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a team member"
                )
            
            # Create team membership
            team_member = TeamMember(
                team_id=team_id,
                user_id=user.id,
                role=role,
                joined_at=datetime.utcnow(),
                added_by=inviter_id
            )
            
            self.db.add(team_member)
            self.db.commit()
            
            # Log collaboration event
            await self._log_collaboration_event(
                event_type="member_invited",
                user_id=inviter_id,
                team_id=team_id,
                resource_type=ResourceType.WORKSPACE,
                resource_id=str(team_id),
                details={
                    "invited_user": user.email,
                    "role": role.value
                }
            )
            
            logger.info(f"User {user.email} invited to team {team_id}")
            
            return {
                "message": "User invited successfully",
                "team_id": team_id,
                "user_id": user.id,
                "role": role.value
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error inviting team member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_team_members(self, team_id: int, requester_id: int) -> List[Dict[str, Any]]:
        """Get list of team members"""
        try:
            # Check if requester is a team member
            requester_membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == requester_id)
            ).first()
            
            if not requester_membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get team members
            members = self.db.query(TeamMember, User).join(
                User, TeamMember.user_id == User.id
            ).filter(TeamMember.team_id == team_id).all()
            
            return [
                {
                    "user_id": member.TeamMember.user_id,
                    "email": member.User.email,
                    "full_name": member.User.full_name,
                    "role": member.TeamMember.role.value,
                    "joined_at": member.TeamMember.joined_at.isoformat(),
                    "is_active": member.TeamMember.is_active
                }
                for member in members
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting team members: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    # Workspace Management
    async def create_workspace(self, team_id: int, creator_id: int, 
                             name: str, description: str = "") -> Dict[str, Any]:
        """Create a new workspace"""
        try:
            # Check if user is team member
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == creator_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Create workspace
            workspace = Workspace(
                name=name,
                description=description,
                team_id=team_id,
                creator_id=creator_id,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(workspace)
            self.db.commit()
            self.db.refresh(workspace)
            
            logger.info(f"Workspace created: {workspace.name} (ID: {workspace.id})")
            
            return {
                "workspace_id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "team_id": team_id,
                "creator_id": creator_id,
                "created_at": workspace.created_at.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_team_workspaces(self, team_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get workspaces for a team"""
        try:
            # Check if user is team member
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get workspaces
            workspaces = self.db.query(Workspace).filter(
                and_(Workspace.team_id == team_id, Workspace.is_active == True)
            ).all()
            
            return [
                {
                    "workspace_id": workspace.id,
                    "name": workspace.name,
                    "description": workspace.description,
                    "creator_id": workspace.creator_id,
                    "created_at": workspace.created_at.isoformat(),
                    "analysis_count": len(workspace.shared_analyses)
                }
                for workspace in workspaces
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting workspaces: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    # Shared Analysis Management
    async def share_analysis(self, user_id: int, team_id: int, workspace_id: int,
                           analysis_type: str, analysis_results: Dict[str, Any],
                           title: str, description: str = "") -> Dict[str, Any]:
        """Share analysis results with team"""
        try:
            # Check permissions
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Verify workspace belongs to team
            workspace = self.db.query(Workspace).filter(
                and_(Workspace.id == workspace_id, Workspace.team_id == team_id)
            ).first()
            
            if not workspace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found"
                )
            
            # Create shared analysis
            shared_analysis = SharedAnalysis(
                title=title,
                description=description,
                analysis_type=analysis_type,
                analysis_results=analysis_results,
                user_id=user_id,
                team_id=team_id,
                workspace_id=workspace_id,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(shared_analysis)
            self.db.commit()
            self.db.refresh(shared_analysis)
            
            # Log collaboration event
            await self._log_collaboration_event(
                event_type="analysis_shared",
                user_id=user_id,
                team_id=team_id,
                resource_type=ResourceType.ANALYSIS,
                resource_id=str(shared_analysis.id),
                details={
                    "title": title,
                    "analysis_type": analysis_type,
                    "workspace_id": workspace_id
                }
            )
            
            logger.info(f"Analysis shared: {title} (ID: {shared_analysis.id})")
            
            return {
                "analysis_id": shared_analysis.id,
                "title": title,
                "analysis_type": analysis_type,
                "workspace_id": workspace_id,
                "created_at": shared_analysis.created_at.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sharing analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_shared_analyses(self, workspace_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get shared analyses in a workspace"""
        try:
            # Verify user has access to workspace
            workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if not workspace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found"
                )
            
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == workspace.team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get shared analyses
            analyses = self.db.query(SharedAnalysis, User).join(
                User, SharedAnalysis.user_id == User.id
            ).filter(
                and_(SharedAnalysis.workspace_id == workspace_id, SharedAnalysis.is_active == True)
            ).all()
            
            return [
                {
                    "analysis_id": analysis.SharedAnalysis.id,
                    "title": analysis.SharedAnalysis.title,
                    "description": analysis.SharedAnalysis.description,
                    "analysis_type": analysis.SharedAnalysis.analysis_type,
                    "created_by": analysis.User.full_name,
                    "created_at": analysis.SharedAnalysis.created_at.isoformat(),
                    "has_results": bool(analysis.SharedAnalysis.analysis_results)
                }
                for analysis in analyses
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting shared analyses: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_shared_analysis_details(self, analysis_id: int, user_id: int) -> Dict[str, Any]:
        """Get detailed shared analysis results"""
        try:
            # Get analysis and verify access
            analysis = self.db.query(SharedAnalysis).filter(
                SharedAnalysis.id == analysis_id
            ).first()
            
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis not found"
                )
            
            # Check team membership
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == analysis.team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get creator info
            creator = self.db.query(User).filter(User.id == analysis.user_id).first()
            
            return {
                "analysis_id": analysis.id,
                "title": analysis.title,
                "description": analysis.description,
                "analysis_type": analysis.analysis_type,
                "analysis_results": analysis.analysis_results,
                "created_by": creator.full_name if creator else "Unknown",
                "created_at": analysis.created_at.isoformat(),
                "team_id": analysis.team_id,
                "workspace_id": analysis.workspace_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis details: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    # API Key Management
    async def create_api_key(self, user_id: int, team_id: int, name: str, 
                           permissions: List[str], expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Create an API key for team use"""
        try:
            # Check if user can create API keys
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create API keys"
                )
            
            # Generate API key
            api_key = f"bk_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Set default expiration (1 year)
            if expires_at is None:
                expires_at = datetime.utcnow() + timedelta(days=365)
            
            # Create API key record
            api_key_record = APIKey(
                key_hash=key_hash,
                name=name,
                permissions=permissions,
                user_id=user_id,
                team_id=team_id,
                expires_at=expires_at,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(api_key_record)
            self.db.commit()
            self.db.refresh(api_key_record)
            
            logger.info(f"API key created: {name} for team {team_id}")
            
            return {
                "api_key_id": api_key_record.id,
                "api_key": api_key,  # Only returned once
                "name": name,
                "permissions": permissions,
                "expires_at": expires_at.isoformat(),
                "created_at": api_key_record.created_at.isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return permissions"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Get API key record
            api_key_record = self.db.query(APIKey).filter(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True,
                    APIKey.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not api_key_record:
                return None
            
            # Update last used
            api_key_record.last_used_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "api_key_id": api_key_record.id,
                "user_id": api_key_record.user_id,
                "team_id": api_key_record.team_id,
                "permissions": api_key_record.permissions,
                "name": api_key_record.name
            }
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    async def get_team_api_keys(self, team_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get API keys for a team"""
        try:
            # Check permissions
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Get API keys
            api_keys = self.db.query(APIKey).filter(
                and_(APIKey.team_id == team_id, APIKey.is_active == True)
            ).all()
            
            return [
                {
                    "api_key_id": key.id,
                    "name": key.name,
                    "permissions": key.permissions,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat(),
                    "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None
                }
                for key in api_keys
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting API keys: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    # Usage Analytics
    async def log_api_usage(self, api_key_id: int, endpoint: str, method: str,
                          execution_time: float, status_code: int, 
                          error_message: str = None) -> None:
        """Log API usage for analytics"""
        try:
            # Get API key info
            api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if not api_key:
                return
            
            # Create usage log
            usage_log = UsageLog(
                api_key_id=api_key_id,
                endpoint=endpoint,
                method=method,
                user_id=api_key.user_id,
                team_id=api_key.team_id,
                execution_time=execution_time,
                status_code=status_code,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(usage_log)
            self.db.commit()
            
            # Cache for real-time analytics
            self.usage_cache[api_key.team_id].append({
                'timestamp': datetime.utcnow(),
                'endpoint': endpoint,
                'execution_time': execution_time,
                'status_code': status_code
            })
            
            # Keep only last 1000 entries in cache
            if len(self.usage_cache[api_key.team_id]) > 1000:
                self.usage_cache[api_key.team_id] = self.usage_cache[api_key.team_id][-1000:]
            
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
    
    async def get_team_usage_analytics(self, team_id: int, user_id: int, 
                                     days: int = 30) -> Dict[str, Any]:
        """Get usage analytics for a team"""
        try:
            # Check permissions
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get usage logs
            start_date = datetime.utcnow() - timedelta(days=days)
            usage_logs = self.db.query(UsageLog).filter(
                and_(
                    UsageLog.team_id == team_id,
                    UsageLog.timestamp >= start_date
                )
            ).all()
            
            # Calculate analytics
            total_requests = len(usage_logs)
            successful_requests = len([log for log in usage_logs if log.status_code < 400])
            failed_requests = total_requests - successful_requests
            
            avg_execution_time = np.mean([log.execution_time for log in usage_logs]) if usage_logs else 0
            
            # Group by endpoint
            endpoint_stats = defaultdict(lambda: {'count': 0, 'avg_time': 0, 'errors': 0})
            for log in usage_logs:
                endpoint_stats[log.endpoint]['count'] += 1
                endpoint_stats[log.endpoint]['avg_time'] += log.execution_time
                if log.status_code >= 400:
                    endpoint_stats[log.endpoint]['errors'] += 1
            
            # Calculate averages
            for endpoint in endpoint_stats:
                if endpoint_stats[endpoint]['count'] > 0:
                    endpoint_stats[endpoint]['avg_time'] /= endpoint_stats[endpoint]['count']
            
            # Daily usage trend
            daily_usage = defaultdict(int)
            for log in usage_logs:
                date_key = log.timestamp.date().isoformat()
                daily_usage[date_key] += 1
            
            return {
                "team_id": team_id,
                "period_days": days,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
                "avg_execution_time": avg_execution_time,
                "endpoint_statistics": dict(endpoint_stats),
                "daily_usage": dict(daily_usage)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting usage analytics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    # Collaborative Workflows
    async def execute_collaborative_workflow(self, workflow_id: str, team_id: int, 
                                           user_id: int, inputs: Dict[str, Any],
                                           workspace_id: int) -> Dict[str, Any]:
        """Execute a workflow collaboratively and share results"""
        try:
            # Check permissions
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Execute workflow
            execution = await research_workflows_service.execute_workflow(
                workflow_id, inputs, user_id
            )
            
            if execution.status == 'completed':
                # Share results with team
                shared_analysis = await self.share_analysis(
                    user_id=user_id,
                    team_id=team_id,
                    workspace_id=workspace_id,
                    analysis_type=f"workflow_{workflow_id}",
                    analysis_results={
                        'execution_id': execution.execution_id,
                        'workflow_id': workflow_id,
                        'results': execution.results,
                        'summary': execution.summary if hasattr(execution, 'summary') else '',
                        'execution_time': execution.execution_time
                    },
                    title=f"Workflow: {workflow_id}",
                    description=f"Collaborative execution of {workflow_id} workflow"
                )
                
                # Log collaboration event
                await self._log_collaboration_event(
                    event_type="collaborative_workflow_executed",
                    user_id=user_id,
                    team_id=team_id,
                    resource_type=ResourceType.WORKFLOW,
                    resource_id=workflow_id,
                    details={
                        'execution_id': execution.execution_id,
                        'workspace_id': workspace_id,
                        'analysis_id': shared_analysis['analysis_id']
                    }
                )
                
                return {
                    "execution_id": execution.execution_id,
                    "status": execution.status,
                    "analysis_id": shared_analysis['analysis_id'],
                    "workspace_id": workspace_id,
                    "shared_with_team": True
                }
            else:
                return {
                    "execution_id": execution.execution_id,
                    "status": execution.status,
                    "error": execution.error_message,
                    "shared_with_team": False
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing collaborative workflow: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _log_collaboration_event(self, event_type: str, user_id: int, 
                                     team_id: int, resource_type: ResourceType,
                                     resource_id: str, details: Dict[str, Any]) -> None:
        """Log collaboration event"""
        try:
            event = CollaborationEvent(
                event_type=event_type,
                user_id=user_id,
                team_id=team_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                timestamp=datetime.utcnow()
            )
            
            # Store in database (would need a collaboration_events table)
            # For now, just log it
            logger.info(f"Collaboration event: {event_type} by user {user_id} in team {team_id}")
            
        except Exception as e:
            logger.error(f"Error logging collaboration event: {e}")
    
    async def get_team_activity(self, team_id: int, user_id: int, 
                              days: int = 7) -> List[Dict[str, Any]]:
        """Get recent team activity"""
        try:
            # Check permissions
            membership = self.db.query(TeamMember).filter(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            ).first()
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get recent shared analyses
            start_date = datetime.utcnow() - timedelta(days=days)
            recent_analyses = self.db.query(SharedAnalysis, User).join(
                User, SharedAnalysis.user_id == User.id
            ).filter(
                and_(
                    SharedAnalysis.team_id == team_id,
                    SharedAnalysis.created_at >= start_date
                )
            ).order_by(SharedAnalysis.created_at.desc()).limit(50).all()
            
            activities = []
            for analysis, user in recent_analyses:
                activities.append({
                    'type': 'analysis_shared',
                    'user': user.full_name,
                    'title': analysis.title,
                    'analysis_type': analysis.analysis_type,
                    'timestamp': analysis.created_at.isoformat(),
                    'resource_id': analysis.id
                })
            
            return activities
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting team activity: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def cleanup_expired_resources(self):
        """Clean up expired API keys and old logs"""
        try:
            # Deactivate expired API keys
            expired_keys = self.db.query(APIKey).filter(
                and_(
                    APIKey.expires_at <= datetime.utcnow(),
                    APIKey.is_active == True
                )
            ).all()
            
            for key in expired_keys:
                key.is_active = False
            
            # Clean up old usage logs (keep last 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            self.db.query(UsageLog).filter(
                UsageLog.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {len(expired_keys)} expired API keys and old usage logs")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired resources: {e}")

# Global instance
enterprise_service = EnterpriseService()