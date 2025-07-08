from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from services.bioinformatics_service import bioinformatics_service
from api.auth import get_current_user
from models.user import User
from utils.logging import get_logger
from utils.security import security_utils

logger = get_logger(__name__)
router = APIRouter()

# Pydantic models
class DatasetMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    organism: Optional[str] = None
    tissue_type: Optional[str] = None
    experiment_type: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Breast Cancer RNA-seq",
                "description": "RNA-seq data from breast cancer patients",
                "organism": "Homo sapiens",
                "tissue_type": "Breast tissue",
                "experiment_type": "RNA-seq"
            }
        }

class PCARequest(BaseModel):
    dataset_id: int
    n_components: int = Field(default=2, ge=2, le=10)
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_id": 1,
                "n_components": 2
            }
        }

class ClusteringRequest(BaseModel):
    dataset_id: int
    method: str = Field(default="kmeans", regex="^(kmeans|hierarchical)$")
    n_clusters: int = Field(default=3, ge=2, le=20)
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_id": 1,
                "method": "kmeans",
                "n_clusters": 3
            }
        }

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    file_name: str
    file_size: int
    num_genes: Optional[int]
    num_samples: Optional[int]
    organism: Optional[str]
    tissue_type: Optional[str]
    experiment_type: Optional[str]
    processing_status: str
    data_quality_score: Optional[float]
    created_at: Optional[datetime]

class AnalysisJobResponse(BaseModel):
    id: int
    job_type: str
    job_name: str
    status: str
    progress: float
    results: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload gene expression dataset"""
    try:
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
            dataset_metadata = DatasetMetadata(**metadata_dict)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata format"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metadata validation error: {str(e)}"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Upload dataset
        result = await bioinformatics_service.upload_dataset(
            user_id=current_user.id,
            file_data=file_content,
            file_name=file.filename,
            metadata=dataset_metadata.dict()
        )
        
        logger.info(f"Dataset uploaded by user {current_user.id}: {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during dataset upload"
        )

@router.get("/datasets", response_model=Dict[str, Any])
async def list_datasets(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """List user's datasets"""
    try:
        result = await bioinformatics_service.list_datasets(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get dataset details"""
    try:
        from models.database import get_db
        from models.bioinformatics import Dataset
        
        db = next(get_db())
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        return dataset.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/eda/{dataset_id}")
async def perform_eda(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """Perform exploratory data analysis"""
    try:
        result = await bioinformatics_service.perform_eda(
            dataset_id=dataset_id,
            user_id=current_user.id
        )
        
        logger.info(f"EDA performed by user {current_user.id} on dataset {dataset_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing EDA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during EDA"
        )

@router.post("/pca")
async def perform_pca(
    pca_request: PCARequest,
    current_user: User = Depends(get_current_user)
):
    """Perform Principal Component Analysis"""
    try:
        result = await bioinformatics_service.perform_pca(
            dataset_id=pca_request.dataset_id,
            user_id=current_user.id,
            n_components=pca_request.n_components
        )
        
        logger.info(f"PCA performed by user {current_user.id} on dataset {pca_request.dataset_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing PCA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during PCA"
        )

@router.post("/clustering")
async def perform_clustering(
    clustering_request: ClusteringRequest,
    current_user: User = Depends(get_current_user)
):
    """Perform clustering analysis"""
    try:
        result = await bioinformatics_service.perform_clustering(
            dataset_id=clustering_request.dataset_id,
            user_id=current_user.id,
            method=clustering_request.method,
            n_clusters=clustering_request.n_clusters
        )
        
        logger.info(f"Clustering performed by user {current_user.id} on dataset {clustering_request.dataset_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing clustering: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during clustering"
        )

@router.get("/analysis-jobs")
async def list_analysis_jobs(
    dataset_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """List user's analysis jobs"""
    try:
        result = await bioinformatics_service.list_analysis_jobs(
            user_id=current_user.id,
            dataset_id=dataset_id,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing analysis jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/analysis-jobs/{job_id}")
async def get_analysis_job(
    job_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get analysis job details"""
    try:
        result = await bioinformatics_service.get_analysis_results(
            analysis_job_id=job_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete dataset"""
    try:
        from models.database import get_db
        from models.bioinformatics import Dataset, AnalysisJob, ExpressionData
        
        db = next(get_db())
        
        # Check if dataset exists and belongs to user
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Delete related data
        db.query(ExpressionData).filter(ExpressionData.dataset_id == dataset_id).delete()
        db.query(AnalysisJob).filter(AnalysisJob.dataset_id == dataset_id).delete()
        db.query(Dataset).filter(Dataset.id == dataset_id).delete()
        
        db.commit()
        
        logger.info(f"Dataset {dataset_id} deleted by user {current_user.id}")
        
        return {"message": "Dataset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/datasets/{dataset_id}/validate")
async def validate_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """Validate dataset structure and quality"""
    try:
        from models.database import get_db
        from models.bioinformatics import Dataset
        
        db = next(get_db())
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Load and validate data
        df = await bioinformatics_service._load_expression_data(dataset_id)
        validation_result = bioinformatics_service._validate_expression_data(df)
        quality_metrics = bioinformatics_service._calculate_quality_metrics(df)
        
        # Update dataset with new metrics
        dataset.data_quality_score = quality_metrics["quality_score"]
        dataset.missing_values_count = quality_metrics["missing_values"]
        db.commit()
        
        return {
            "dataset_id": dataset_id,
            "validation_result": validation_result,
            "quality_metrics": quality_metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/gene-info/{gene_id}")
async def get_gene_info(
    gene_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get gene annotation information"""
    try:
        from models.database import get_db
        from models.bioinformatics import GeneAnnotation
        
        db = next(get_db())
        gene_annotation = db.query(GeneAnnotation).filter(
            GeneAnnotation.gene_id == gene_id
        ).first()
        
        if not gene_annotation:
            # Return basic information if not found in database
            return {
                "gene_id": gene_id,
                "message": "Gene annotation not found in database",
                "available": False
            }
        
        return gene_annotation.to_dict()
        
    except Exception as e:
        logger.error(f"Error getting gene info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def bioinformatics_health_check():
    """Health check for bioinformatics service"""
    return {
        "service": "bioinformatics",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }