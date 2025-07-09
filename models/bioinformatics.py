from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
from datetime import datetime
from typing import Dict, Any, List
import json

class Dataset(Base):
    """Dataset model for storing gene expression data"""
    
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    
    # Dataset metadata
    num_genes = Column(Integer, nullable=True)
    num_samples = Column(Integer, nullable=True)
    organism = Column(String(100), nullable=True)
    tissue_type = Column(String(100), nullable=True)
    experiment_type = Column(String(100), nullable=True)
    
    # Data quality metrics
    missing_values_count = Column(Integer, default=0)
    data_quality_score = Column(Float, nullable=True)
    
    # Processing status
    processing_status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    processing_log = Column(Text, nullable=True)
    
    # Data storage
    data_hash = Column(String(255), nullable=True)  # Hash of the data for integrity
    storage_path = Column(String(500), nullable=True)  # Path to stored data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="datasets")
    analysis_jobs = relationship("AnalysisJob", back_populates="dataset")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataset to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "num_genes": self.num_genes,
            "num_samples": self.num_samples,
            "organism": self.organism,
            "tissue_type": self.tissue_type,
            "experiment_type": self.experiment_type,
            "missing_values_count": self.missing_values_count,
            "data_quality_score": self.data_quality_score,
            "processing_status": self.processing_status,
            "data_hash": self.data_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Dataset(name='{self.name}', user_id={self.user_id})>"

class AnalysisJob(Base):
    """Analysis job model for tracking bioinformatics analyses"""
    
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # pca, clustering, differential_expression, etc.
    job_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Job parameters
    parameters = Column(JSON, nullable=True)
    
    # Job status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0-100
    
    # Results
    results = Column(JSON, nullable=True)
    output_files = Column(JSON, nullable=True)  # List of output file paths
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Performance metrics
    cpu_time = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analysis_jobs")
    dataset = relationship("Dataset", back_populates="analysis_jobs")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis job to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "dataset_id": self.dataset_id,
            "job_type": self.job_type,
            "job_name": self.job_name,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status,
            "progress": self.progress,
            "results": self.results,
            "output_files": self.output_files,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "cpu_time": self.cpu_time,
            "memory_usage": self.memory_usage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f"<AnalysisJob(job_name='{self.job_name}', status='{self.status}')>"

class GeneAnnotation(Base):
    """Gene annotation model for storing gene information"""
    
    __tablename__ = "gene_annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    gene_id = Column(String(50), unique=True, index=True, nullable=False)
    gene_symbol = Column(String(50), index=True, nullable=True)
    gene_name = Column(String(255), nullable=True)
    chromosome = Column(String(10), nullable=True)
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    strand = Column(String(1), nullable=True)  # + or -
    biotype = Column(String(50), nullable=True)
    organism = Column(String(100), nullable=True)
    
    # External identifiers
    ensembl_id = Column(String(50), nullable=True)
    entrez_id = Column(String(50), nullable=True)
    uniprot_id = Column(String(50), nullable=True)
    
    # Functional annotations
    go_terms = Column(JSON, nullable=True)
    pathways = Column(JSON, nullable=True)
    protein_domains = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert gene annotation to dictionary"""
        return {
            "id": self.id,
            "gene_id": self.gene_id,
            "gene_symbol": self.gene_symbol,
            "gene_name": self.gene_name,
            "chromosome": self.chromosome,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "strand": self.strand,
            "biotype": self.biotype,
            "organism": self.organism,
            "ensembl_id": self.ensembl_id,
            "entrez_id": self.entrez_id,
            "uniprot_id": self.uniprot_id,
            "go_terms": self.go_terms,
            "pathways": self.pathways,
            "protein_domains": self.protein_domains,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<GeneAnnotation(gene_id='{self.gene_id}', gene_symbol='{self.gene_symbol}')>"

class ExpressionData(Base):
    """Expression data model for storing gene expression values"""
    
    __tablename__ = "expression_data"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    gene_id = Column(String(50), index=True, nullable=False)
    sample_id = Column(String(100), index=True, nullable=False)
    expression_value = Column(Float, nullable=False)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    is_outlier = Column(Boolean, default=False)
    
    # Processing metadata
    normalization_method = Column(String(50), nullable=True)
    batch_info = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("Dataset")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert expression data to dictionary"""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "gene_id": self.gene_id,
            "sample_id": self.sample_id,
            "expression_value": self.expression_value,
            "quality_score": self.quality_score,
            "is_outlier": self.is_outlier,
            "normalization_method": self.normalization_method,
            "batch_info": self.batch_info,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<ExpressionData(gene_id='{self.gene_id}', sample_id='{self.sample_id}')>"

class AnalysisResult(Base):
    """Analysis result model for storing detailed analysis results"""
    
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    result_type = Column(String(50), nullable=False)  # pca_scores, cluster_assignments, etc.
    result_name = Column(String(255), nullable=False)
    
    # Result data
    result_data = Column(JSON, nullable=True)
    result_file_path = Column(String(500), nullable=True)
    
    # Analysis metadata
    analysis_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis_job = relationship("AnalysisJob")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary"""
        return {
            "id": self.id,
            "analysis_job_id": self.analysis_job_id,
            "result_type": self.result_type,
            "result_name": self.result_name,
            "result_data": self.result_data,
            "result_file_path": self.result_file_path,
            "analysis_metadata": self.analysis_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<AnalysisResult(result_name='{self.result_name}', result_type='{self.result_type}')>"