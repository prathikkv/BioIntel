"""
Unit tests for Bioinformatics API
"""

import pytest
import json
import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from api.main import app
from models.bioinformatics import Dataset, AnalysisJob

class TestBioinformaticsAPI:
    """Test cases for Bioinformatics API endpoints"""
    
    def test_upload_dataset_success(self, client, mock_bioinformatics_service, auth_headers, sample_csv_data):
        """Test successful dataset upload"""
        files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
        metadata = {
            "name": "Test Dataset",
            "description": "Test gene expression dataset",
            "organism": "Homo sapiens",
            "tissue_type": "Breast tissue",
            "experiment_type": "RNA-seq"
        }
        data = {"metadata": json.dumps(metadata)}
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.post("/api/bio/upload", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["message"] == "Dataset uploaded successfully"
        assert "dataset" in result
    
    def test_upload_dataset_no_file(self, client, auth_headers):
        """Test dataset upload without file"""
        metadata = {
            "name": "Test Dataset",
            "description": "Test gene expression dataset"
        }
        data = {"metadata": json.dumps(metadata)}
        
        response = client.post("/api/bio/upload", data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_upload_dataset_invalid_metadata(self, client, auth_headers, sample_csv_data):
        """Test dataset upload with invalid metadata"""
        files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
        data = {"metadata": "invalid-json"}
        
        response = client.post("/api/bio/upload", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid metadata format" in response.json()["detail"]
    
    def test_upload_dataset_empty_file(self, client, auth_headers):
        """Test dataset upload with empty file"""
        files = {"file": ("empty.csv", b"", "text/csv")}
        metadata = {"name": "Test Dataset"}
        data = {"metadata": json.dumps(metadata)}
        
        response = client.post("/api/bio/upload", files=files, data=data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Empty file" in response.json()["detail"]
    
    def test_upload_dataset_unauthorized(self, client, sample_csv_data):
        """Test dataset upload without authentication"""
        files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
        metadata = {"name": "Test Dataset"}
        data = {"metadata": json.dumps(metadata)}
        
        response = client.post("/api/bio/upload", files=files, data=data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_datasets_success(self, client, mock_bioinformatics_service, auth_headers):
        """Test successful dataset listing"""
        mock_datasets = [
            {
                "id": 1,
                "name": "Test Dataset 1",
                "num_genes": 100,
                "num_samples": 10,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Test Dataset 2",
                "num_genes": 200,
                "num_samples": 20,
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        mock_bioinformatics_service.list_datasets.return_value = {
            "datasets": mock_datasets,
            "total": 2,
            "skip": 0,
            "limit": 20
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.get("/api/bio/datasets", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "datasets" in data
        assert len(data["datasets"]) == 2
        assert data["total"] == 2
    
    def test_list_datasets_with_pagination(self, client, mock_bioinformatics_service, auth_headers):
        """Test dataset listing with pagination"""
        mock_bioinformatics_service.list_datasets.return_value = {
            "datasets": [],
            "total": 0,
            "skip": 10,
            "limit": 5
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.get("/api/bio/datasets?skip=10&limit=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 5
    
    def test_list_datasets_unauthorized(self, client):
        """Test dataset listing without authentication"""
        response = client.get("/api/bio/datasets")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_dataset_success(self, client, auth_headers, test_dataset):
        """Test successful dataset retrieval"""
        dataset_id = test_dataset.id
        
        with patch('models.bioinformatics.Dataset') as mock_dataset_model:
            mock_dataset_model.query.filter.return_value.first.return_value = test_dataset
            
            response = client.get(f"/api/bio/datasets/{dataset_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == dataset_id
        assert data["name"] == test_dataset.name
    
    def test_get_dataset_not_found(self, client, auth_headers):
        """Test dataset retrieval with non-existent ID"""
        dataset_id = 999
        
        with patch('models.bioinformatics.Dataset') as mock_dataset_model:
            mock_dataset_model.query.filter.return_value.first.return_value = None
            
            response = client.get(f"/api/bio/datasets/{dataset_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_dataset_unauthorized(self, client):
        """Test dataset retrieval without authentication"""
        dataset_id = 1
        
        response = client.get(f"/api/bio/datasets/{dataset_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_perform_eda_success(self, client, mock_bioinformatics_service, auth_headers):
        """Test successful EDA performance"""
        dataset_id = 1
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.post(f"/api/bio/eda/{dataset_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dataset_id"] == dataset_id
        assert "statistics" in data
        assert "plots" in data
    
    def test_perform_eda_unauthorized(self, client):
        """Test EDA performance without authentication"""
        dataset_id = 1
        
        response = client.post(f"/api/bio/eda/{dataset_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_perform_pca_success(self, client, mock_bioinformatics_service, auth_headers):
        """Test successful PCA analysis"""
        pca_request = {
            "dataset_id": 1,
            "n_components": 2
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.post("/api/bio/pca", json=pca_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["analysis_job_id"] == 1
        assert "pca_scores" in data
        assert "explained_variance" in data
    
    def test_perform_pca_invalid_components(self, client, auth_headers):
        """Test PCA with invalid number of components"""
        pca_request = {
            "dataset_id": 1,
            "n_components": 1  # Too few components
        }
        
        response = client.post("/api/bio/pca", json=pca_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_perform_pca_unauthorized(self, client):
        """Test PCA analysis without authentication"""
        pca_request = {
            "dataset_id": 1,
            "n_components": 2
        }
        
        response = client.post("/api/bio/pca", json=pca_request)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_perform_clustering_success(self, client, mock_bioinformatics_service, auth_headers):
        """Test successful clustering analysis"""
        clustering_request = {
            "dataset_id": 1,
            "method": "kmeans",
            "n_clusters": 3
        }
        
        mock_bioinformatics_service.perform_clustering.return_value = {
            "analysis_job_id": 1,
            "cluster_assignments": {"Sample1": 0, "Sample2": 1, "Sample3": 2},
            "method": "kmeans",
            "n_clusters": 3
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.post("/api/bio/clustering", json=clustering_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["analysis_job_id"] == 1
        assert "cluster_assignments" in data
        assert data["method"] == "kmeans"
        assert data["n_clusters"] == 3
    
    def test_perform_clustering_invalid_method(self, client, auth_headers):
        """Test clustering with invalid method"""
        clustering_request = {
            "dataset_id": 1,
            "method": "invalid_method",
            "n_clusters": 3
        }
        
        response = client.post("/api/bio/clustering", json=clustering_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_perform_clustering_invalid_clusters(self, client, auth_headers):
        """Test clustering with invalid number of clusters"""
        clustering_request = {
            "dataset_id": 1,
            "method": "kmeans",
            "n_clusters": 1  # Too few clusters
        }
        
        response = client.post("/api/bio/clustering", json=clustering_request, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_perform_clustering_unauthorized(self, client):
        """Test clustering analysis without authentication"""
        clustering_request = {
            "dataset_id": 1,
            "method": "kmeans",
            "n_clusters": 3
        }
        
        response = client.post("/api/bio/clustering", json=clustering_request)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_analysis_jobs_success(self, client, mock_bioinformatics_service, auth_headers):
        """Test successful analysis jobs listing"""
        mock_jobs = [
            {
                "id": 1,
                "job_type": "pca",
                "job_name": "PCA Analysis",
                "status": "completed",
                "progress": 100.0,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "job_type": "clustering",
                "job_name": "K-means Clustering",
                "status": "running",
                "progress": 50.0,
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        mock_bioinformatics_service.list_analysis_jobs.return_value = {
            "analysis_jobs": mock_jobs,
            "total": 2,
            "skip": 0,
            "limit": 20
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.get("/api/bio/analysis-jobs", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "analysis_jobs" in data
        assert len(data["analysis_jobs"]) == 2
        assert data["total"] == 2
    
    def test_list_analysis_jobs_with_filter(self, client, mock_bioinformatics_service, auth_headers):
        """Test analysis jobs listing with dataset filter"""
        mock_bioinformatics_service.list_analysis_jobs.return_value = {
            "analysis_jobs": [],
            "total": 0,
            "skip": 0,
            "limit": 20
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.get("/api/bio/analysis-jobs?dataset_id=1", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        mock_bioinformatics_service.list_analysis_jobs.assert_called_once()
    
    def test_list_analysis_jobs_unauthorized(self, client):
        """Test analysis jobs listing without authentication"""
        response = client.get("/api/bio/analysis-jobs")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_analysis_job_success(self, client, mock_bioinformatics_service, auth_headers):
        """Test successful analysis job retrieval"""
        job_id = 1
        
        mock_bioinformatics_service.get_analysis_results.return_value = {
            "id": job_id,
            "job_type": "pca",
            "job_name": "PCA Analysis",
            "status": "completed",
            "progress": 100.0,
            "results": {"explained_variance": [0.6, 0.3]}
        }
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.get(f"/api/bio/analysis-jobs/{job_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == job_id
        assert data["job_type"] == "pca"
        assert "results" in data
    
    def test_get_analysis_job_not_found(self, client, mock_bioinformatics_service, auth_headers):
        """Test analysis job retrieval with non-existent ID"""
        job_id = 999
        
        mock_bioinformatics_service.get_analysis_results.side_effect = Exception("Analysis job not found")
        
        with patch('services.bioinformatics_service.bioinformatics_service', mock_bioinformatics_service):
            response = client.get(f"/api/bio/analysis-jobs/{job_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_get_analysis_job_unauthorized(self, client):
        """Test analysis job retrieval without authentication"""
        job_id = 1
        
        response = client.get(f"/api/bio/analysis-jobs/{job_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_delete_dataset_success(self, client, auth_headers, test_dataset):
        """Test successful dataset deletion"""
        dataset_id = test_dataset.id
        
        with patch('models.bioinformatics.Dataset') as mock_dataset_model:
            mock_dataset_model.query.filter.return_value.first.return_value = test_dataset
            
            response = client.delete(f"/api/bio/datasets/{dataset_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Dataset deleted successfully"
    
    def test_delete_dataset_not_found(self, client, auth_headers):
        """Test dataset deletion with non-existent ID"""
        dataset_id = 999
        
        with patch('models.bioinformatics.Dataset') as mock_dataset_model:
            mock_dataset_model.query.filter.return_value.first.return_value = None
            
            response = client.delete(f"/api/bio/datasets/{dataset_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_dataset_unauthorized(self, client):
        """Test dataset deletion without authentication"""
        dataset_id = 1
        
        response = client.delete(f"/api/bio/datasets/{dataset_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_validate_dataset_success(self, client, auth_headers, test_dataset):
        """Test successful dataset validation"""
        dataset_id = test_dataset.id
        
        with patch('models.bioinformatics.Dataset') as mock_dataset_model:
            mock_dataset_model.query.filter.return_value.first.return_value = test_dataset
            
            with patch('services.bioinformatics_service.bioinformatics_service') as mock_service:
                mock_service._load_expression_data.return_value = MagicMock()
                mock_service._validate_expression_data.return_value = {"is_valid": True, "errors": []}
                mock_service._calculate_quality_metrics.return_value = {"quality_score": 85.5}
                
                response = client.post(f"/api/bio/datasets/{dataset_id}/validate", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["dataset_id"] == dataset_id
        assert "validation_result" in data
        assert "quality_metrics" in data
    
    def test_validate_dataset_not_found(self, client, auth_headers):
        """Test dataset validation with non-existent ID"""
        dataset_id = 999
        
        with patch('models.bioinformatics.Dataset') as mock_dataset_model:
            mock_dataset_model.query.filter.return_value.first.return_value = None
            
            response = client.post(f"/api/bio/datasets/{dataset_id}/validate", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_validate_dataset_unauthorized(self, client):
        """Test dataset validation without authentication"""
        dataset_id = 1
        
        response = client.post(f"/api/bio/datasets/{dataset_id}/validate")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_gene_info_success(self, client, auth_headers):
        """Test successful gene information retrieval"""
        gene_id = "BRCA1"
        
        mock_gene_annotation = MagicMock()
        mock_gene_annotation.to_dict.return_value = {
            "gene_id": gene_id,
            "gene_name": "BRCA1",
            "description": "Breast cancer 1 gene",
            "chromosome": "17"
        }
        
        with patch('models.bioinformatics.GeneAnnotation') as mock_gene_model:
            mock_gene_model.query.filter.return_value.first.return_value = mock_gene_annotation
            
            response = client.get(f"/api/bio/gene-info/{gene_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["gene_id"] == gene_id
        assert data["gene_name"] == "BRCA1"
    
    def test_get_gene_info_not_found(self, client, auth_headers):
        """Test gene information retrieval with non-existent gene"""
        gene_id = "NONEXISTENT"
        
        with patch('models.bioinformatics.GeneAnnotation') as mock_gene_model:
            mock_gene_model.query.filter.return_value.first.return_value = None
            
            response = client.get(f"/api/bio/gene-info/{gene_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["gene_id"] == gene_id
        assert data["available"] == False
    
    def test_get_gene_info_unauthorized(self, client):
        """Test gene information retrieval without authentication"""
        gene_id = "BRCA1"
        
        response = client.get(f"/api/bio/gene-info/{gene_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_bioinformatics_health_check(self, client):
        """Test bioinformatics service health check"""
        response = client.get("/api/bio/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "bioinformatics"
        assert data["status"] == "healthy"
        assert "timestamp" in data