import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import io
import base64
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import asyncio
from datetime import datetime

from models.database import get_db
from models.bioinformatics import Dataset, AnalysisJob, AnalysisResult, ExpressionData, GeneAnnotation
from models.user import User
from utils.logging import get_logger
from utils.config import get_settings
from utils.security import security_utils

settings = get_settings()
logger = get_logger(__name__)

class BioinformaticsService:
    """Service for bioinformatics data processing and analysis"""
    
    def __init__(self):
        self.db = next(get_db())
        
    @staticmethod
    async def initialize():
        """Initialize bioinformatics service"""
        logger.info("Bioinformatics service initialized")
    
    async def upload_dataset(self, user_id: int, file_data: bytes, file_name: str, 
                           metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload and validate gene expression dataset"""
        try:
            # Validate file type
            if not security_utils.validate_file_type(file_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Supported types: CSV, XLSX, XLS"
                )
            
            # Validate file size
            if not security_utils.validate_file_size(len(file_data)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE/1024/1024:.1f}MB"
                )
            
            # Parse the file
            try:
                if file_name.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(file_data), index_col=0)
                elif file_name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(io.BytesIO(file_data), index_col=0)
                else:
                    raise ValueError("Unsupported file format")
                    
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error parsing file: {str(e)}"
                )
            
            # Validate data structure
            validation_result = self._validate_expression_data(df)
            if not validation_result["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Data validation failed: {validation_result['errors']}"
                )
            
            # Calculate data quality metrics
            quality_metrics = self._calculate_quality_metrics(df)
            
            # Create dataset record
            dataset = Dataset(
                user_id=user_id,
                name=metadata.get("name", file_name),
                description=metadata.get("description"),
                file_name=file_name,
                file_size=len(file_data),
                file_type=file_name.split('.')[-1].lower(),
                num_genes=len(df.index),
                num_samples=len(df.columns),
                organism=metadata.get("organism"),
                tissue_type=metadata.get("tissue_type"),
                experiment_type=metadata.get("experiment_type"),
                missing_values_count=quality_metrics["missing_values"],
                data_quality_score=quality_metrics["quality_score"],
                processing_status="uploaded",
                data_hash=security_utils.hash_data(str(df.values.tolist()))
            )
            
            self.db.add(dataset)
            self.db.commit()
            self.db.refresh(dataset)
            
            # Store expression data (for smaller datasets)
            if len(df.index) * len(df.columns) < 100000:  # Limit for direct storage
                await self._store_expression_data(dataset.id, df)
            
            logger.info(f"Dataset uploaded successfully: {dataset.id}")
            
            return {
                "message": "Dataset uploaded successfully",
                "dataset": dataset.to_dict(),
                "quality_metrics": quality_metrics,
                "validation_result": validation_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during dataset upload"
            )
    
    def _validate_expression_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate gene expression data structure"""
        errors = []
        
        # Check if dataframe is empty
        if df.empty:
            errors.append("Dataset is empty")
        
        # Check dimensions
        if len(df.index) == 0:
            errors.append("No genes found in dataset")
        elif len(df.index) > settings.MAX_GENES:
            errors.append(f"Too many genes ({len(df.index)}). Maximum allowed: {settings.MAX_GENES}")
        
        if len(df.columns) == 0:
            errors.append("No samples found in dataset")
        elif len(df.columns) > settings.MAX_SAMPLES:
            errors.append(f"Too many samples ({len(df.columns)}). Maximum allowed: {settings.MAX_SAMPLES}")
        
        # Check for numeric data
        non_numeric_columns = df.select_dtypes(exclude=[np.number]).columns.tolist()
        if non_numeric_columns:
            errors.append(f"Non-numeric values found in columns: {non_numeric_columns}")
        
        # Check for duplicate gene names
        if df.index.duplicated().any():
            errors.append("Duplicate gene names found")
        
        # Check for duplicate sample names
        if df.columns.duplicated().any():
            errors.append("Duplicate sample names found")
        
        # Check for excessive missing values
        missing_percentage = (df.isnull().sum().sum() / (len(df.index) * len(df.columns))) * 100
        if missing_percentage > 50:
            errors.append(f"Too many missing values ({missing_percentage:.1f}%)")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "missing_percentage": missing_percentage
        }
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data quality metrics"""
        # Missing values count
        missing_values = df.isnull().sum().sum()
        
        # Quality score calculation
        quality_score = 100.0
        
        # Penalize for missing values
        missing_percentage = (missing_values / (len(df.index) * len(df.columns))) * 100
        quality_score -= missing_percentage
        
        # Penalize for low variance genes
        gene_variances = df.var(axis=1)
        low_variance_genes = (gene_variances < 0.1).sum()
        quality_score -= (low_variance_genes / len(df.index)) * 20
        
        # Penalize for potential outliers
        z_scores = np.abs((df - df.mean()) / df.std())
        outlier_count = (z_scores > 3).sum().sum()
        quality_score -= (outlier_count / (len(df.index) * len(df.columns))) * 10
        
        quality_score = max(0, quality_score)
        
        return {
            "missing_values": int(missing_values),
            "quality_score": round(quality_score, 2),
            "missing_percentage": round(missing_percentage, 2),
            "low_variance_genes": int(low_variance_genes),
            "potential_outliers": int(outlier_count)
        }
    
    async def _store_expression_data(self, dataset_id: int, df: pd.DataFrame):
        """Store expression data in database"""
        try:
            expression_records = []
            
            for gene_id in df.index:
                for sample_id in df.columns:
                    value = df.loc[gene_id, sample_id]
                    
                    if pd.notna(value):
                        expression_records.append(
                            ExpressionData(
                                dataset_id=dataset_id,
                                gene_id=str(gene_id),
                                sample_id=str(sample_id),
                                expression_value=float(value)
                            )
                        )
            
            # Batch insert
            self.db.bulk_save_objects(expression_records)
            self.db.commit()
            
            logger.info(f"Stored {len(expression_records)} expression data records")
            
        except Exception as e:
            logger.error(f"Error storing expression data: {str(e)}")
            raise
    
    async def perform_eda(self, dataset_id: int, user_id: int) -> Dict[str, Any]:
        """Perform exploratory data analysis"""
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.user_id == user_id
            ).first()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found"
                )
            
            # Load expression data
            df = await self._load_expression_data(dataset_id)
            
            # Basic statistics
            stats = {
                "num_genes": len(df.index),
                "num_samples": len(df.columns),
                "total_values": len(df.index) * len(df.columns),
                "missing_values": df.isnull().sum().sum(),
                "mean_expression": df.mean().mean(),
                "median_expression": df.median().median(),
                "std_expression": df.std().mean()
            }
            
            # Top variable genes
            gene_variances = df.var(axis=1).sort_values(ascending=False)
            top_variable_genes = gene_variances.head(10).to_dict()
            
            # Sample correlations
            sample_correlations = df.corr()
            
            # Generate plots
            plots = await self._generate_eda_plots(df)
            
            logger.info(f"EDA completed for dataset {dataset_id}")
            
            return {
                "dataset_id": dataset_id,
                "statistics": stats,
                "top_variable_genes": top_variable_genes,
                "sample_correlation_matrix": sample_correlations.to_dict(),
                "plots": plots
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error performing EDA: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during EDA"
            )
    
    async def _load_expression_data(self, dataset_id: int) -> pd.DataFrame:
        """Load expression data from database"""
        try:
            # Get expression data
            expression_data = self.db.query(ExpressionData).filter(
                ExpressionData.dataset_id == dataset_id
            ).all()
            
            if not expression_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Expression data not found. Dataset may be too large for direct storage."
                )
            
            # Convert to DataFrame
            data_dict = {}
            for record in expression_data:
                if record.gene_id not in data_dict:
                    data_dict[record.gene_id] = {}
                data_dict[record.gene_id][record.sample_id] = record.expression_value
            
            df = pd.DataFrame(data_dict).T
            return df
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error loading expression data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error loading expression data"
            )
    
    async def _generate_eda_plots(self, df: pd.DataFrame) -> Dict[str, str]:
        """Generate EDA plots and return as base64 strings"""
        plots = {}
        
        try:
            # Distribution plot
            fig, ax = plt.subplots(figsize=(10, 6))
            df.values.flatten().hist(bins=50, ax=ax, alpha=0.7)
            ax.set_title('Expression Value Distribution')
            ax.set_xlabel('Expression Value')
            ax.set_ylabel('Frequency')
            plots["distribution"] = self._plot_to_base64(fig)
            plt.close(fig)
            
            # Heatmap of top variable genes
            gene_variances = df.var(axis=1).sort_values(ascending=False)
            top_genes = gene_variances.head(20).index
            
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(df.loc[top_genes], cmap='RdBu_r', center=0, ax=ax)
            ax.set_title('Top 20 Most Variable Genes')
            plots["heatmap"] = self._plot_to_base64(fig)
            plt.close(fig)
            
            # Sample correlation heatmap
            sample_corr = df.corr()
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(sample_corr, annot=True, cmap='coolwarm', center=0, ax=ax)
            ax.set_title('Sample Correlation Matrix')
            plots["correlation"] = self._plot_to_base64(fig)
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"Error generating plots: {str(e)}")
            plots["error"] = str(e)
        
        return plots
    
    def _plot_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        return f"data:image/png;base64,{image_base64}"
    
    async def perform_pca(self, dataset_id: int, user_id: int, n_components: int = 2) -> Dict[str, Any]:
        """Perform Principal Component Analysis"""
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.user_id == user_id
            ).first()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found"
                )
            
            # Load expression data
            df = await self._load_expression_data(dataset_id)
            
            # Standardize the data
            scaler = StandardScaler()
            df_scaled = pd.DataFrame(
                scaler.fit_transform(df.T),
                index=df.columns,
                columns=df.index
            )
            
            # Perform PCA
            pca = PCA(n_components=n_components)
            pca_result = pca.fit_transform(df_scaled)
            
            # Create PCA DataFrame
            pca_df = pd.DataFrame(
                pca_result,
                index=df.columns,
                columns=[f'PC{i+1}' for i in range(n_components)]
            )
            
            # Calculate explained variance
            explained_variance = pca.explained_variance_ratio_
            
            # Create analysis job record
            analysis_job = AnalysisJob(
                user_id=user_id,
                dataset_id=dataset_id,
                job_type="pca",
                job_name=f"PCA Analysis - {dataset.name}",
                parameters={"n_components": n_components},
                status="completed",
                progress=100.0,
                results={
                    "explained_variance": explained_variance.tolist(),
                    "cumulative_variance": np.cumsum(explained_variance).tolist(),
                    "pca_scores": pca_df.to_dict()
                },
                completed_at=datetime.utcnow()
            )
            
            self.db.add(analysis_job)
            self.db.commit()
            self.db.refresh(analysis_job)
            
            # Generate PCA plot
            pca_plot = await self._generate_pca_plot(pca_df, explained_variance)
            
            logger.info(f"PCA completed for dataset {dataset_id}")
            
            return {
                "analysis_job_id": analysis_job.id,
                "pca_scores": pca_df.to_dict(),
                "explained_variance": explained_variance.tolist(),
                "cumulative_variance": np.cumsum(explained_variance).tolist(),
                "plot": pca_plot
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error performing PCA: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during PCA"
            )
    
    async def _generate_pca_plot(self, pca_df: pd.DataFrame, explained_variance: np.ndarray) -> str:
        """Generate PCA plot"""
        try:
            fig = px.scatter(
                pca_df,
                x='PC1',
                y='PC2',
                title=f'PCA Plot (PC1: {explained_variance[0]:.1%}, PC2: {explained_variance[1]:.1%})',
                labels={'PC1': f'PC1 ({explained_variance[0]:.1%})', 
                       'PC2': f'PC2 ({explained_variance[1]:.1%})'}
            )
            
            # Convert to base64
            fig_json = fig.to_json()
            return fig_json
            
        except Exception as e:
            logger.error(f"Error generating PCA plot: {str(e)}")
            return None
    
    async def perform_clustering(self, dataset_id: int, user_id: int, 
                               method: str = "kmeans", n_clusters: int = 3) -> Dict[str, Any]:
        """Perform clustering analysis"""
        try:
            # Get dataset
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.user_id == user_id
            ).first()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found"
                )
            
            # Load expression data
            df = await self._load_expression_data(dataset_id)
            
            # Standardize the data
            scaler = StandardScaler()
            df_scaled = pd.DataFrame(
                scaler.fit_transform(df.T),
                index=df.columns,
                columns=df.index
            )
            
            # Perform clustering
            if method == "kmeans":
                clusterer = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = clusterer.fit_predict(df_scaled)
            elif method == "hierarchical":
                from scipy.cluster.hierarchy import fcluster
                linkage_matrix = linkage(df_scaled, method='ward')
                cluster_labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust') - 1
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported clustering method"
                )
            
            # Create cluster assignments
            cluster_assignments = pd.Series(cluster_labels, index=df.columns)
            
            # Perform PCA for visualization
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(df_scaled)
            
            # Create analysis job record
            analysis_job = AnalysisJob(
                user_id=user_id,
                dataset_id=dataset_id,
                job_type="clustering",
                job_name=f"{method.title()} Clustering - {dataset.name}",
                parameters={"method": method, "n_clusters": n_clusters},
                status="completed",
                progress=100.0,
                results={
                    "cluster_assignments": cluster_assignments.to_dict(),
                    "pca_coordinates": pca_result.tolist(),
                    "explained_variance": pca.explained_variance_ratio_.tolist()
                },
                completed_at=datetime.utcnow()
            )
            
            self.db.add(analysis_job)
            self.db.commit()
            self.db.refresh(analysis_job)
            
            # Generate clustering plot
            clustering_plot = await self._generate_clustering_plot(
                pca_result, cluster_labels, pca.explained_variance_ratio_, method
            )
            
            logger.info(f"Clustering completed for dataset {dataset_id}")
            
            return {
                "analysis_job_id": analysis_job.id,
                "cluster_assignments": cluster_assignments.to_dict(),
                "method": method,
                "n_clusters": n_clusters,
                "plot": clustering_plot
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error performing clustering: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during clustering"
            )
    
    async def _generate_clustering_plot(self, pca_result: np.ndarray, cluster_labels: np.ndarray,
                                      explained_variance: np.ndarray, method: str) -> str:
        """Generate clustering plot"""
        try:
            # Create DataFrame for plotting
            plot_df = pd.DataFrame({
                'PC1': pca_result[:, 0],
                'PC2': pca_result[:, 1],
                'Cluster': [f'Cluster {i}' for i in cluster_labels]
            })
            
            fig = px.scatter(
                plot_df,
                x='PC1',
                y='PC2',
                color='Cluster',
                title=f'{method.title()} Clustering Results',
                labels={'PC1': f'PC1 ({explained_variance[0]:.1%})', 
                       'PC2': f'PC2 ({explained_variance[1]:.1%})'}
            )
            
            return fig.to_json()
            
        except Exception as e:
            logger.error(f"Error generating clustering plot: {str(e)}")
            return None
    
    async def get_analysis_results(self, analysis_job_id: int, user_id: int) -> Dict[str, Any]:
        """Get analysis results"""
        try:
            analysis_job = self.db.query(AnalysisJob).filter(
                AnalysisJob.id == analysis_job_id,
                AnalysisJob.user_id == user_id
            ).first()
            
            if not analysis_job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis job not found"
                )
            
            return analysis_job.to_dict()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis results: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def list_datasets(self, user_id: int, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List user's datasets"""
        try:
            datasets = self.db.query(Dataset).filter(
                Dataset.user_id == user_id
            ).offset(skip).limit(limit).all()
            
            total = self.db.query(Dataset).filter(Dataset.user_id == user_id).count()
            
            return {
                "datasets": [dataset.to_dict() for dataset in datasets],
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error listing datasets: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def list_analysis_jobs(self, user_id: int, dataset_id: int = None, 
                               skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List user's analysis jobs"""
        try:
            query = self.db.query(AnalysisJob).filter(AnalysisJob.user_id == user_id)
            
            if dataset_id:
                query = query.filter(AnalysisJob.dataset_id == dataset_id)
            
            analysis_jobs = query.offset(skip).limit(limit).all()
            total = query.count()
            
            return {
                "analysis_jobs": [job.to_dict() for job in analysis_jobs],
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error listing analysis jobs: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

# Global bioinformatics service instance
bioinformatics_service = BioinformaticsService()