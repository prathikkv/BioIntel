from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import io
import os
import tempfile
from pathlib import Path
import time

from services.reports_service import reports_service
from api.auth import get_current_user
from models.user import User
from models.literature import Report
from models.database import get_db
from utils.logging import get_logger
from utils.security import security_utils

logger = get_logger(__name__)
router = APIRouter()

# Pydantic models
class ReportRequest(BaseModel):
    report_type: str = Field(..., pattern="^(analysis|literature|combined)$")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    format_type: str = Field(default="html", pattern="^(html|pdf|docx)$")
    
    # Data source IDs
    dataset_ids: Optional[List[int]] = None
    analysis_job_ids: Optional[List[int]] = None
    literature_summary_ids: Optional[List[int]] = None
    
    # Template and styling options
    template_name: Optional[str] = "default"
    include_plots: bool = True
    include_statistics: bool = True
    include_methodology: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "analysis",
                "title": "Gene Expression Analysis Report",
                "description": "Comprehensive analysis of breast cancer RNA-seq data",
                "format_type": "pdf",
                "dataset_ids": [1, 2],
                "analysis_job_ids": [1, 2, 3],
                "template_name": "analysis_template",
                "include_plots": True,
                "include_statistics": True,
                "include_methodology": True
            }
        }

class ReportResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    report_type: str
    format_type: str
    file_size: Optional[int]
    generation_time: Optional[float]
    created_at: Optional[datetime]
    download_url: str

class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    skip: int
    limit: int

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    report_request: ReportRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a new report"""
    try:
        logger.info(f"Generating report for user {current_user.id}: {report_request.title}")
        
        # Validate data access permissions
        await _validate_data_access(report_request, current_user.id)
        
        # Generate report
        report = await reports_service.generate_report(
            user_id=current_user.id,
            report_request=report_request.dict()
        )
        
        logger.info(f"Report generated successfully: {report['id']}")
        
        return ReportResponse(
            id=report["id"],
            title=report["title"],
            description=report["description"],
            report_type=report["report_type"],
            format_type=report["format_type"],
            file_size=report["file_size"],
            generation_time=report["generation_time"],
            created_at=report["created_at"],
            download_url=f"/api/reports/{report['id']}/download"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during report generation"
        )

@router.get("/", response_model=ReportListResponse)
async def list_reports(
    skip: int = 0,
    limit: int = 20,
    report_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List user's reports"""
    try:
        db = next(get_db())
        
        # Build query
        query = db.query(Report).filter(Report.user_id == current_user.id)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        # Get total count
        total = query.count()
        
        # Get reports with pagination
        reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to response format
        report_responses = []
        for report in reports:
            report_responses.append(ReportResponse(
                id=report.id,
                title=report.title,
                description=report.description,
                report_type=report.report_type,
                format_type=report.format_type,
                file_size=report.file_size,
                generation_time=report.generation_time,
                created_at=report.created_at,
                download_url=f"/api/reports/{report.id}/download"
            ))
        
        return ReportListResponse(
            reports=report_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{report_id}")
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get report details"""
    try:
        db = next(get_db())
        
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return report.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    """Download report file"""
    try:
        db = next(get_db())
        
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Check if file exists
        if not report.file_path or not os.path.exists(report.file_path):
            # Generate file on-demand if not exists
            file_path = await reports_service.generate_report_file(report_id)
        else:
            file_path = report.file_path
        
        # Determine content type
        content_types = {
            "html": "text/html",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        
        content_type = content_types.get(report.format_type, "application/octet-stream")
        
        # Create filename
        filename = f"{report.title.replace(' ', '_')}_{report.id}.{report.format_type}"
        
        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{report_id}/preview")
async def preview_report(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    """Preview report content"""
    try:
        db = next(get_db())
        
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Return HTML preview
        if report.format_type == "html":
            return Response(
                content=report.content,
                media_type="text/html"
            )
        else:
            # For PDF/DOCX, return a simple HTML preview
            preview_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .info {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{report.title}</h1>
                    <p>Report Type: {report.report_type.title()}</p>
                    <p>Format: {report.format_type.upper()}</p>
                    <p>Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S') if report.created_at else 'N/A'}</p>
                </div>
                <div class="info">
                    <p><strong>Description:</strong> {report.description or 'No description available'}</p>
                    <p><strong>File Size:</strong> {report.file_size or 'N/A'} bytes</p>
                    <p><strong>Generation Time:</strong> {report.generation_time or 'N/A'} seconds</p>
                </div>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/api/reports/{report.id}/download" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Report</a>
                </div>
            </body>
            </html>
            """
            
            return Response(
                content=preview_content,
                media_type="text/html"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete report"""
    try:
        db = next(get_db())
        
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Delete file if exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except Exception as e:
                logger.warning(f"Could not delete report file: {str(e)}")
        
        # Delete database record
        db.delete(report)
        db.commit()
        
        logger.info(f"Report deleted: {report_id}")
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{report_id}/metadata")
async def get_report_metadata(
    report_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get report metadata and statistics"""
    try:
        db = next(get_db())
        
        report = db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == current_user.id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get additional metadata
        metadata = {
            "basic_info": report.to_dict(),
            "data_sources": {
                "datasets": len(report.dataset_ids or []),
                "analysis_jobs": len(report.analysis_job_ids or []),
                "literature_summaries": len(report.literature_summary_ids or [])
            },
            "file_info": {
                "exists": bool(report.file_path and os.path.exists(report.file_path)),
                "size_mb": round(report.file_size / (1024 * 1024), 2) if report.file_size else None
            }
        }
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/templates/")
async def list_report_templates():
    """List available report templates"""
    try:
        templates = await reports_service.list_templates()
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def reports_health_check():
    """Health check for reports service"""
    return {
        "service": "reports",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Helper functions
async def _validate_data_access(report_request: ReportRequest, user_id: int):
    """Validate that user has access to requested data"""
    db = next(get_db())
    
    # Check dataset access
    if report_request.dataset_ids:
        from models.bioinformatics import Dataset
        for dataset_id in report_request.dataset_ids:
            dataset = db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.user_id == user_id
            ).first()
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to dataset {dataset_id}"
                )
    
    # Check analysis job access
    if report_request.analysis_job_ids:
        from models.bioinformatics import AnalysisJob
        for job_id in report_request.analysis_job_ids:
            job = db.query(AnalysisJob).filter(
                AnalysisJob.id == job_id,
                AnalysisJob.user_id == user_id
            ).first()
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to analysis job {job_id}"
                )
    
    # Check literature summary access
    if report_request.literature_summary_ids:
        from models.literature import LiteratureSummary
        for summary_id in report_request.literature_summary_ids:
            summary = db.query(LiteratureSummary).filter(
                LiteratureSummary.id == summary_id,
                LiteratureSummary.user_id == user_id
            ).first()
            if not summary:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to literature summary {summary_id}"
                )