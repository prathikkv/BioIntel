# Conditional imports for data analysis libraries
try:
    import pandas as pd
    import numpy as np
    DATA_ANALYSIS_AVAILABLE = True
except ImportError:
    DATA_ANALYSIS_AVAILABLE = False
    print("⚠️  pandas and numpy not available - data analysis features disabled")

import json
import io
import base64
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import asyncio
from datetime import datetime

# Optional ML libraries for advanced analysis
try:
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import pdist
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn not available - advanced ML features disabled")

# Optional visualization libraries
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.utils import PlotlyJSONEncoder
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("⚠️  Plotting libraries not available - visualizations disabled")

from models.database import get_db
from models.bioinformatics import Dataset, AnalysisJob, AnalysisResult, ExpressionData, GeneAnnotation
from models.user import User
from utils.logging import get_logger
from utils.config import get_settings
from utils.security import security_utils
from services.bio_apis_service import bio_apis_service
from services.free_ai_service import free_ai_service

settings = get_settings()
logger = get_logger(__name__)

class BioinformaticsService:
    """Service for bioinformatics data processing and analysis with FREE APIs"""
    
    def __init__(self):
        self.db = next(get_db())
        self.bio_apis = bio_apis_service
        self.free_ai = free_ai_service
        
    @staticmethod
    async def initialize():
        """Initialize bioinformatics service"""
        logger.info("Bioinformatics service initialized")
    
    async def annotate_genes(self, gene_list: List[str], user_id: int) -> Dict[str, Any]:
        """
        Annotate genes using free APIs (Ensembl, UniProt, KEGG)
        """
        try:
            logger.info(f"Annotating {len(gene_list)} genes using free APIs")
            
            # Use comprehensive analysis from bio_apis_service
            analysis_result = await self.bio_apis.analyze_gene_list(gene_list)
            
            # Process results for storage
            annotations = []
            for gene_info in analysis_result.get('genes', []):
                annotations.append({
                    'gene_id': gene_info.gene_id,
                    'gene_name': gene_info.gene_name,
                    'chromosome': gene_info.chromosome,
                    'start': gene_info.start,
                    'end': gene_info.end,
                    'biotype': gene_info.biotype,
                    'description': gene_info.description,
                    'synonyms': gene_info.synonyms
                })
            
            # Create analysis job record
            analysis_job = AnalysisJob(
                user_id=user_id,
                dataset_id=None,  # This is a standalone gene annotation
                analysis_type="gene_annotation",
                parameters={"genes": gene_list},
                status="completed",
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_job)
            self.db.commit()
            self.db.refresh(analysis_job)
            
            # Store results
            analysis_result_record = AnalysisResult(
                analysis_job_id=analysis_job.id,
                result_type="gene_annotation",
                result_data={
                    "annotations": annotations,
                    "proteins": [
                        {
                            "accession": p.accession,
                            "name": p.name,
                            "function": p.function,
                            "pathways": p.pathways,
                            "diseases": p.diseases
                        }
                        for p in analysis_result.get('proteins', [])
                    ],
                    "pathways": [
                        {
                            "pathway_id": pw.pathway_id,
                            "pathway_name": pw.pathway_name,
                            "genes": pw.genes,
                            "category": pw.category
                        }
                        for pw in analysis_result.get('pathways', [])
                    ],
                    "interactions": [
                        {
                            "protein_id": inter.protein_id,
                            "partners": inter.functional_partners,
                            "network_score": inter.network_score
                        }
                        for inter in analysis_result.get('interactions', [])
                    ]
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_result_record)
            self.db.commit()
            
            logger.info(f"Gene annotation completed for job {analysis_job.id}")
            
            return {
                "message": "Gene annotation completed successfully",
                "analysis_job_id": analysis_job.id,
                "annotations": annotations,
                "protein_info": analysis_result_record.result_data.get("proteins", []),
                "pathway_info": analysis_result_record.result_data.get("pathways", []),
                "interaction_networks": analysis_result_record.result_data.get("interactions", []),
                "literature_references": analysis_result.get('literature', [])
            }
            
        except Exception as e:
            logger.error(f"Error in gene annotation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gene annotation failed: {str(e)}"
            )
    
    async def pathway_enrichment_analysis(self, gene_list: List[str], user_id: int) -> Dict[str, Any]:
        """
        Perform pathway enrichment analysis using KEGG and other free APIs
        """
        try:
            logger.info(f"Performing pathway enrichment for {len(gene_list)} genes")
            
            # Search for pathways related to the genes
            pathway_results = []
            
            # Use the first few genes to search for pathways
            for gene in gene_list[:5]:  # Limit to avoid rate limits
                try:
                    pathways = await self.bio_apis.search_kegg_pathways(gene)
                    pathway_results.extend(pathways)
                except Exception as e:
                    logger.warning(f"Failed to search pathways for {gene}: {e}")
            
            # Remove duplicates and analyze
            unique_pathways = {}
            for pathway in pathway_results:
                if pathway.pathway_id not in unique_pathways:
                    unique_pathways[pathway.pathway_id] = pathway
            
            # Calculate enrichment scores (simplified)
            enrichment_results = []
            for pathway_id, pathway in unique_pathways.items():
                # Count overlap between input genes and pathway genes
                pathway_genes = set(pathway.genes)
                input_genes = set(gene_list)
                overlap = pathway_genes.intersection(input_genes)
                
                if overlap:
                    enrichment_score = len(overlap) / len(input_genes)
                    enrichment_results.append({
                        'pathway_id': pathway_id,
                        'pathway_name': pathway.pathway_name,
                        'category': pathway.category,
                        'genes_in_pathway': len(pathway.genes),
                        'genes_overlap': len(overlap),
                        'enrichment_score': enrichment_score,
                        'overlapping_genes': list(overlap),
                        'p_value': self._calculate_enrichment_p_value(
                            len(overlap), len(input_genes), len(pathway.genes)
                        )
                    })
            
            # Sort by enrichment score
            enrichment_results.sort(key=lambda x: x['enrichment_score'], reverse=True)
            
            # Create analysis job record
            analysis_job = AnalysisJob(
                user_id=user_id,
                dataset_id=None,
                analysis_type="pathway_enrichment",
                parameters={"genes": gene_list},
                status="completed",
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_job)
            self.db.commit()
            self.db.refresh(analysis_job)
            
            # Store results
            analysis_result_record = AnalysisResult(
                analysis_job_id=analysis_job.id,
                result_type="pathway_enrichment",
                result_data={
                    "enrichment_results": enrichment_results,
                    "input_genes": gene_list,
                    "total_pathways_analyzed": len(unique_pathways)
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_result_record)
            self.db.commit()
            
            logger.info(f"Pathway enrichment analysis completed for job {analysis_job.id}")
            
            return {
                "message": "Pathway enrichment analysis completed successfully",
                "analysis_job_id": analysis_job.id,
                "enrichment_results": enrichment_results[:20],  # Return top 20
                "total_pathways_analyzed": len(unique_pathways),
                "significant_pathways": len([r for r in enrichment_results if r['p_value'] < 0.05])
            }
            
        except Exception as e:
            logger.error(f"Error in pathway enrichment analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pathway enrichment analysis failed: {str(e)}"
            )
    
    def _calculate_enrichment_p_value(self, overlap: int, input_size: int, pathway_size: int) -> float:
        """
        Calculate enrichment p-value using hypergeometric test (simplified)
        """
        try:
            from scipy.stats import hypergeom
            
            # Simplified hypergeometric test
            # Parameters: total genes (~20000), pathway genes, input genes, overlap
            total_genes = 20000
            p_value = hypergeom.sf(overlap-1, total_genes, pathway_size, input_size)
            return float(p_value)
            
        except ImportError:
            # Fallback to simple calculation if scipy not available
            return 1.0 - (overlap / input_size)
        except Exception:
            return 1.0
    
    async def protein_interaction_network(self, gene_list: List[str], user_id: int) -> Dict[str, Any]:
        """
        Build protein-protein interaction network using STRING database
        """
        try:
            logger.info(f"Building PPI network for {len(gene_list)} genes")
            
            # Get interactions for each gene
            all_interactions = []
            nodes = set()
            edges = []
            
            for gene in gene_list[:10]:  # Limit to avoid rate limits
                try:
                    interactions = await self.bio_apis.get_protein_interactions(gene)
                    if interactions:
                        all_interactions.append(interactions)
                        nodes.add(gene)
                        
                        # Add edges for network visualization
                        for interaction in interactions.interactions:
                            partner = interaction['partner']
                            score = interaction['score']
                            
                            if score > 400:  # Only high-confidence interactions
                                nodes.add(partner)
                                edges.append({
                                    'source': gene,
                                    'target': partner,
                                    'weight': score,
                                    'evidence': interaction.get('evidence', 0)
                                })
                                
                except Exception as e:
                    logger.warning(f"Failed to get interactions for {gene}: {e}")
            
            # Create network statistics
            network_stats = {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'average_degree': len(edges) * 2 / len(nodes) if nodes else 0,
                'high_confidence_edges': len([e for e in edges if e['weight'] > 700])
            }
            
            # Identify hub genes (genes with many connections)
            node_degrees = {}
            for edge in edges:
                node_degrees[edge['source']] = node_degrees.get(edge['source'], 0) + 1
                node_degrees[edge['target']] = node_degrees.get(edge['target'], 0) + 1
            
            hub_genes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Create analysis job record
            analysis_job = AnalysisJob(
                user_id=user_id,
                dataset_id=None,
                analysis_type="protein_interaction_network",
                parameters={"genes": gene_list},
                status="completed",
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_job)
            self.db.commit()
            self.db.refresh(analysis_job)
            
            # Store results
            analysis_result_record = AnalysisResult(
                analysis_job_id=analysis_job.id,
                result_type="protein_interaction_network",
                result_data={
                    "nodes": list(nodes),
                    "edges": edges,
                    "network_stats": network_stats,
                    "hub_genes": hub_genes,
                    "interactions": [
                        {
                            "protein_id": inter.protein_id,
                            "partners": inter.functional_partners,
                            "network_score": inter.network_score
                        }
                        for inter in all_interactions
                    ]
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_result_record)
            self.db.commit()
            
            logger.info(f"PPI network analysis completed for job {analysis_job.id}")
            
            return {
                "message": "Protein interaction network analysis completed successfully",
                "analysis_job_id": analysis_job.id,
                "network_stats": network_stats,
                "hub_genes": hub_genes,
                "network_data": {
                    "nodes": [{"id": node, "degree": node_degrees.get(node, 0)} for node in nodes],
                    "edges": edges
                }
            }
            
        except Exception as e:
            logger.error(f"Error in PPI network analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PPI network analysis failed: {str(e)}"
            )
    
    async def find_drug_targets(self, gene_list: List[str], user_id: int) -> Dict[str, Any]:
        """
        Find potential drug targets from gene list using free APIs
        """
        try:
            logger.info(f"Finding drug targets for {len(gene_list)} genes")
            
            # Use bio_apis_service to find drug targets
            drug_targets = await self.bio_apis.find_drug_targets(gene_list)
            
            # Enhance with additional analysis
            enhanced_targets = []
            for target in drug_targets:
                # Get protein information for the target
                protein_info = await self.bio_apis.get_protein_info(target['gene'])
                
                enhanced_target = {
                    'gene': target['gene'],
                    'therapeutic_class': target['therapeutic_class'],
                    'example_drugs': target['example_drugs'],
                    'evidence': target['evidence'],
                    'protein_info': {
                        'name': protein_info.name if protein_info else "Unknown",
                        'function': protein_info.function if protein_info else "Unknown",
                        'diseases': protein_info.diseases if protein_info else []
                    },
                    'druggability_score': self._calculate_druggability_score(target)
                }
                enhanced_targets.append(enhanced_target)
            
            # Create analysis job record
            analysis_job = AnalysisJob(
                user_id=user_id,
                dataset_id=None,
                analysis_type="drug_target_analysis",
                parameters={"genes": gene_list},
                status="completed",
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_job)
            self.db.commit()
            self.db.refresh(analysis_job)
            
            # Store results
            analysis_result_record = AnalysisResult(
                analysis_job_id=analysis_job.id,
                result_type="drug_target_analysis",
                result_data={
                    "drug_targets": enhanced_targets,
                    "input_genes": gene_list,
                    "total_targets_found": len(enhanced_targets)
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(analysis_result_record)
            self.db.commit()
            
            logger.info(f"Drug target analysis completed for job {analysis_job.id}")
            
            return {
                "message": "Drug target analysis completed successfully",
                "analysis_job_id": analysis_job.id,
                "drug_targets": enhanced_targets,
                "total_targets_found": len(enhanced_targets),
                "high_confidence_targets": len([t for t in enhanced_targets if t['druggability_score'] > 0.7])
            }
            
        except Exception as e:
            logger.error(f"Error in drug target analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Drug target analysis failed: {str(e)}"
            )
    
    def _calculate_druggability_score(self, target: Dict[str, Any]) -> float:
        """
        Calculate druggability score based on various factors
        """
        score = 0.5  # Base score
        
        # Higher score for known drug classes
        if 'inhibitor' in target['therapeutic_class'].lower():
            score += 0.2
        
        # Higher score if there are existing drugs
        if target['example_drugs']:
            score += 0.3
        
        # Literature-based evidence
        if target['evidence'] == 'Literature-based':
            score += 0.1
        
        return min(score, 1.0)
    
    async def upload_dataset(self, user_id: int, file_data: bytes, file_name: str, 
                           metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload and validate gene expression dataset"""
        if not DATA_ANALYSIS_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Data analysis libraries not available. Please use the full version for dataset upload."
            )
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
        if not DATA_ANALYSIS_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Data analysis libraries not available. Please use the full version for exploratory data analysis."
            )
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
        if not DATA_ANALYSIS_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Data analysis libraries not available. Please use the full version for PCA analysis."
            )
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
        if not DATA_ANALYSIS_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Data analysis libraries not available. Please use the full version for clustering analysis."
            )
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