"""
Enterprise API endpoints for team collaboration and API management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from services.enterprise_service import enterprise_service
from services.auth_service import auth_service
from utils.security import get_current_user
from models.user import User

router = APIRouter()
security = HTTPBearer()

# Request/Response Models
class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    team_type: str = Field(default="research", max_length=50)

class TeamInviteRequest(BaseModel):
    user_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: str = Field(..., regex=r'^(owner|admin|member|viewer)$')

class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)

class ShareAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    analysis_type: str = Field(..., min_length=1, max_length=100)
    analysis_results: Dict[str, Any]

class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default=["read"])
    expires_at: Optional[datetime] = None

class WorkflowExecuteRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    inputs: Dict[str, Any] = Field(default={})
    custom_parameters: Dict[str, Any] = Field(default={})

# Team Management Endpoints
@router.post("/teams", response_model=Dict[str, Any])
async def create_team(
    request: TeamCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new team"""
    try:
        result = await enterprise_service.create_team(
            creator_id=current_user.id,
            team_name=request.name,
            description=request.description,
            team_type=request.team_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/teams/{team_id}/invite", response_model=Dict[str, Any])
async def invite_team_member(
    team_id: int,
    request: TeamInviteRequest,
    current_user: User = Depends(get_current_user)
):
    """Invite a user to join a team"""
    try:
        from models.enterprise import TeamRole
        role = TeamRole(request.role)
        
        result = await enterprise_service.invite_team_member(
            team_id=team_id,
            inviter_id=current_user.id,
            user_email=request.user_email,
            role=role
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/teams/{team_id}/members", response_model=List[Dict[str, Any]])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get team members"""
    try:
        result = await enterprise_service.get_team_members(
            team_id=team_id,
            requester_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Workspace Management Endpoints
@router.post("/teams/{team_id}/workspaces", response_model=Dict[str, Any])
async def create_workspace(
    team_id: int,
    request: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new workspace"""
    try:
        result = await enterprise_service.create_workspace(
            team_id=team_id,
            creator_id=current_user.id,
            name=request.name,
            description=request.description
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/teams/{team_id}/workspaces", response_model=List[Dict[str, Any]])
async def get_team_workspaces(
    team_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get workspaces for a team"""
    try:
        result = await enterprise_service.get_team_workspaces(
            team_id=team_id,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Shared Analysis Endpoints
@router.post("/teams/{team_id}/workspaces/{workspace_id}/analyses", response_model=Dict[str, Any])
async def share_analysis(
    team_id: int,
    workspace_id: int,
    request: ShareAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Share analysis results with team"""
    try:
        result = await enterprise_service.share_analysis(
            user_id=current_user.id,
            team_id=team_id,
            workspace_id=workspace_id,
            analysis_type=request.analysis_type,
            analysis_results=request.analysis_results,
            title=request.title,
            description=request.description
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/workspaces/{workspace_id}/analyses", response_model=List[Dict[str, Any]])
async def get_shared_analyses(
    workspace_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get shared analyses in a workspace"""
    try:
        result = await enterprise_service.get_shared_analyses(
            workspace_id=workspace_id,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/analyses/{analysis_id}", response_model=Dict[str, Any])
async def get_shared_analysis_details(
    analysis_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get detailed shared analysis results"""
    try:
        result = await enterprise_service.get_shared_analysis_details(
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# API Key Management Endpoints
@router.post("/teams/{team_id}/api-keys", response_model=Dict[str, Any])
async def create_api_key(
    team_id: int,
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create an API key for team use"""
    try:
        result = await enterprise_service.create_api_key(
            user_id=current_user.id,
            team_id=team_id,
            name=request.name,
            permissions=request.permissions,
            expires_at=request.expires_at
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/teams/{team_id}/api-keys", response_model=List[Dict[str, Any]])
async def get_team_api_keys(
    team_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get API keys for a team"""
    try:
        result = await enterprise_service.get_team_api_keys(
            team_id=team_id,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Usage Analytics Endpoints
@router.get("/teams/{team_id}/usage", response_model=Dict[str, Any])
async def get_team_usage_analytics(
    team_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get usage analytics for a team"""
    try:
        result = await enterprise_service.get_team_usage_analytics(
            team_id=team_id,
            user_id=current_user.id,
            days=days
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/teams/{team_id}/activity", response_model=List[Dict[str, Any]])
async def get_team_activity(
    team_id: int,
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get recent team activity"""
    try:
        result = await enterprise_service.get_team_activity(
            team_id=team_id,
            user_id=current_user.id,
            days=days
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Collaborative Workflow Endpoints
@router.post("/teams/{team_id}/workspaces/{workspace_id}/workflows/execute", response_model=Dict[str, Any])
async def execute_collaborative_workflow(
    team_id: int,
    workspace_id: int,
    request: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute a workflow collaboratively and share results"""
    try:
        result = await enterprise_service.execute_collaborative_workflow(
            workflow_id=request.workflow_id,
            team_id=team_id,
            user_id=current_user.id,
            inputs=request.inputs,
            workspace_id=workspace_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )