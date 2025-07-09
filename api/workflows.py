"""
Workflows API endpoints for research workflows and analysis templates
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from services.research_workflows_service import research_workflows_service
from services.analysis_templates_service import analysis_templates_service
from utils.security import get_current_user
from models.user import User

router = APIRouter()
security = HTTPBearer()

# Request/Response Models
class WorkflowExecuteRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    inputs: Dict[str, Any] = Field(default={})
    custom_parameters: Dict[str, Any] = Field(default={})

class TemplateExecuteRequest(BaseModel):
    template_id: str = Field(..., min_length=1)
    inputs: Dict[str, Any] = Field(default={})
    custom_parameters: Dict[str, Any] = Field(default={})

# Workflow Management Endpoints
@router.get("/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List available research workflows"""
    try:
        result = research_workflows_service.list_workflows(category=category)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific research workflow"""
    try:
        workflow = research_workflows_service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "category": workflow.category,
            "templates": workflow.templates,
            "parameters": workflow.parameters,
            "expected_duration": workflow.expected_duration
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/workflows/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute a research workflow"""
    try:
        result = await research_workflows_service.execute_workflow(
            workflow_id=workflow_id,
            inputs=request.inputs,
            user_id=current_user.id,
            custom_parameters=request.custom_parameters
        )
        
        return {
            "execution_id": result.execution_id,
            "workflow_id": result.workflow_id,
            "status": result.status,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "execution_time": result.execution_time,
            "results": result.results,
            "summary": result.summary if hasattr(result, 'summary') else None,
            "error_message": result.error_message
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/workflows/executions/{execution_id}", response_model=Dict[str, Any])
async def get_workflow_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get workflow execution status"""
    try:
        result = await research_workflows_service.get_execution_status(execution_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        return {
            "execution_id": result.execution_id,
            "workflow_id": result.workflow_id,
            "status": result.status,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "execution_time": result.execution_time,
            "error_message": result.error_message
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/workflows/executions/{execution_id}/export", response_model=Dict[str, Any])
async def export_workflow_results(
    execution_id: str,
    format: str = "html",
    current_user: User = Depends(get_current_user)
):
    """Export workflow results"""
    try:
        result = await research_workflows_service.export_workflow_results(
            execution_id=execution_id,
            format=format
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found or not completed"
            )
        
        return {
            "execution_id": execution_id,
            "format": format,
            "size": len(result),
            "download_url": f"/api/workflows/executions/{execution_id}/download?format={format}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Template Management Endpoints
@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List available analysis templates"""
    try:
        result = analysis_templates_service.list_templates(category=category)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific analysis template"""
    try:
        template = analysis_templates_service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "parameters": template.parameters,
            "steps": template.steps,
            "expected_inputs": template.expected_inputs,
            "expected_outputs": template.expected_outputs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/templates/{template_id}/execute", response_model=Dict[str, Any])
async def execute_template(
    template_id: str,
    request: TemplateExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute an analysis template"""
    try:
        result = await analysis_templates_service.execute_template(
            template_id=template_id,
            inputs=request.inputs,
            user_id=current_user.id,
            custom_parameters=request.custom_parameters
        )
        
        return {
            "template_id": result.template_id,
            "status": result.status,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat(),
            "results": result.results,
            "plots": result.plots,
            "summary": result.summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Dataset and Public Data Endpoints
@router.get("/datasets", response_model=Dict[str, Any])
async def list_public_datasets(
    source: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List available public datasets"""
    try:
        from services.public_datasets_service import public_datasets_service
        
        if source:
            if source.upper() == "TCGA":
                result = await public_datasets_service.get_tcga_datasets()
            elif source.upper() == "GEO":
                result = await public_datasets_service.search_geo_datasets("")
            elif source.upper() == "GTEX":
                result = await public_datasets_service.get_gtex_datasets()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid source. Use TCGA, GEO, or GTEx"
                )
            
            return {source.upper(): [dataset.__dict__ for dataset in result]}
        else:
            result = await public_datasets_service.list_all_datasets()
            return {
                source: [dataset.__dict__ for dataset in datasets]
                for source, datasets in result.items()
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/datasets/{dataset_id}", response_model=Dict[str, Any])
async def get_dataset_info(
    dataset_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get information about a specific dataset"""
    try:
        from services.public_datasets_service import public_datasets_service
        
        result = await public_datasets_service.get_dataset_info(dataset_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        return result.__dict__
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/datasets/{dataset_id}/sample", response_model=Dict[str, Any])
async def get_sample_data(
    dataset_id: str,
    num_samples: int = 50,
    num_genes: int = 1000,
    current_user: User = Depends(get_current_user)
):
    """Get sample data from a dataset"""
    try:
        from services.public_datasets_service import public_datasets_service
        
        result = await public_datasets_service.generate_sample_data(
            dataset_id=dataset_id,
            num_samples=num_samples,
            num_genes=num_genes
        )
        
        if result.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not generate sample data for this dataset"
            )
        
        return {
            "dataset_id": dataset_id,
            "shape": result.shape,
            "columns": result.columns.tolist(),
            "index": result.index.tolist()[:10],  # First 10 genes
            "sample_data": result.head().to_dict(),
            "statistics": {
                "mean": result.mean().mean(),
                "std": result.std().mean(),
                "min": result.min().min(),
                "max": result.max().max()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/datasets/{dataset_id}/statistics", response_model=Dict[str, Any])
async def get_dataset_statistics(
    dataset_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a dataset"""
    try:
        from services.public_datasets_service import public_datasets_service
        
        result = await public_datasets_service.get_dataset_statistics(dataset_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/datasets/recommended", response_model=List[Dict[str, Any]])
async def get_recommended_datasets(
    analysis_type: str = "cancer",
    current_user: User = Depends(get_current_user)
):
    """Get recommended datasets for analysis type"""
    try:
        from services.public_datasets_service import public_datasets_service
        
        result = await public_datasets_service.get_recommended_datasets(analysis_type)
        return [dataset.__dict__ for dataset in result]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )