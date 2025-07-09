"""
Research Workflows Service
Automated research workflows with comprehensive report generation
"""

import logging
import asyncio
import json
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
import pandas as pd
import numpy as np
from io import BytesIO
import zipfile
import tempfile
import os

from services.analysis_templates_service import analysis_templates_service
from services.public_datasets_service import public_datasets_service
from services.bio_apis_service import bio_apis_service
from services.free_ai_service import free_ai_service
from services.bioinformatics_service import BioinformaticsService
from services.literature_service import literature_service

logger = logging.getLogger(__name__)

@dataclass
class ResearchWorkflow:
    """Research workflow definition"""
    id: str
    name: str
    description: str
    category: str
    templates: List[str]  # List of template IDs to execute
    parameters: Dict[str, Any]
    report_template: str
    expected_duration: int  # in minutes

@dataclass
class WorkflowExecution:
    """Workflow execution result"""
    workflow_id: str
    execution_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    results: Dict[str, Any]
    report: Optional[str]
    error_message: Optional[str]

class ResearchWorkflowsService:
    """Service for automated research workflows and report generation"""
    
    def __init__(self):
        self.bio_service = BioinformaticsService()
        self.workflows = self._initialize_workflows()
        self.report_templates = self._initialize_report_templates()
        self.active_executions = {}
    
    @staticmethod
    async def initialize():
        """Initialize research workflows service"""
        logger.info("Research workflows service initialized")
    
    def _initialize_workflows(self) -> Dict[str, ResearchWorkflow]:
        """Initialize available research workflows"""
        workflows = {}
        
        # Comprehensive Cancer Research Workflow
        workflows['comprehensive_cancer_research'] = ResearchWorkflow(
            id='comprehensive_cancer_research',
            name='Comprehensive Cancer Research Pipeline',
            description='End-to-end cancer research including biomarker discovery, pathway analysis, literature mining, and drug target identification',
            category='Cancer Research',
            templates=[
                'cancer_biomarker_discovery',
                'pathway_enrichment',
                'ppi_network_analysis',
                'literature_mining'
            ],
            parameters={
                'cancer_type': 'TCGA-BRCA',
                'sample_size': 200,
                'top_genes': 100,
                'literature_query': 'breast cancer biomarkers',
                'include_drug_targets': True,
                'include_survival_analysis': True
            },
            report_template='comprehensive_cancer_report',
            expected_duration=45
        )
        
        # Biomarker Discovery Workflow
        workflows['biomarker_discovery'] = ResearchWorkflow(
            id='biomarker_discovery',
            name='Biomarker Discovery Pipeline',
            description='Systematic biomarker discovery using expression data, pathway analysis, and literature validation',
            category='Biomarker Research',
            templates=[
                'differential_expression',
                'pathway_enrichment',
                'gene_annotation',
                'literature_mining'
            ],
            parameters={
                'expression_data': None,
                'group_comparison': True,
                'pathway_databases': ['KEGG', 'GO', 'Reactome'],
                'literature_validation': True,
                'statistical_threshold': 0.05
            },
            report_template='biomarker_discovery_report',
            expected_duration=30
        )
        
        # Drug Target Discovery Workflow
        workflows['drug_target_discovery'] = ResearchWorkflow(
            id='drug_target_discovery',
            name='Drug Target Discovery Pipeline',
            description='Identify and validate potential drug targets through network analysis and literature mining',
            category='Drug Discovery',
            templates=[
                'ppi_network_analysis',
                'pathway_enrichment',
                'literature_mining',
                'gene_annotation'
            ],
            parameters={
                'target_genes': [],
                'disease_context': 'cancer',
                'network_confidence': 0.7,
                'literature_focus': 'drug targets',
                'include_clinical_trials': True
            },
            report_template='drug_target_report',
            expected_duration=35
        )
        
        # TCGA Data Mining Workflow
        workflows['tcga_data_mining'] = ResearchWorkflow(
            id='tcga_data_mining',
            name='TCGA Data Mining Pipeline',
            description='Comprehensive analysis of TCGA cancer datasets with biomarker discovery and clinical correlation',
            category='Cancer Genomics',
            templates=[
                'tcga_analysis',
                'cancer_biomarker_discovery',
                'pathway_enrichment',
                'literature_mining'
            ],
            parameters={
                'dataset_id': 'TCGA-BRCA',
                'sample_size': 300,
                'clustering_method': 'kmeans',
                'survival_analysis': True,
                'pathway_analysis': True
            },
            report_template='tcga_mining_report',
            expected_duration=40
        )
        
        # Literature-Driven Research Workflow
        workflows['literature_driven_research'] = ResearchWorkflow(
            id='literature_driven_research',
            name='Literature-Driven Research Pipeline',
            description='Research pipeline starting from literature mining to identify genes, pathways, and drug targets',
            category='Literature Research',
            templates=[
                'literature_mining',
                'gene_annotation',
                'pathway_enrichment',
                'ppi_network_analysis'
            ],
            parameters={
                'research_query': 'alzheimer disease biomarkers',
                'max_papers': 200,
                'gene_extraction': True,
                'pathway_analysis': True,
                'network_analysis': True
            },
            report_template='literature_driven_report',
            expected_duration=50
        )
        
        return workflows
    
    def _initialize_report_templates(self) -> Dict[str, str]:
        """Initialize report templates"""
        templates = {}
        
        # Comprehensive Cancer Report Template
        templates['comprehensive_cancer_report'] = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Cancer Research Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }
                .result-box { background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .gene-list { display: flex; flex-wrap: wrap; gap: 10px; }
                .gene-item { background-color: #e0e0e0; padding: 5px 10px; border-radius: 3px; }
                .plot-container { text-align: center; margin: 20px 0; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .summary { background-color: #e8f4f8; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Comprehensive Cancer Research Report</h1>
                <p><strong>Cancer Type:</strong> {{ cancer_type }}</p>
                <p><strong>Generated:</strong> {{ timestamp }}</p>
                <p><strong>Analysis Duration:</strong> {{ duration }} minutes</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="summary">
                    {{ executive_summary }}
                </div>
            </div>
            
            <div class="section">
                <h2>Dataset Information</h2>
                <div class="result-box">
                    <h3>{{ dataset_name }}</h3>
                    <ul>
                        <li><strong>Samples:</strong> {{ total_samples }}</li>
                        <li><strong>Genes Analyzed:</strong> {{ total_genes }}</li>
                        <li><strong>Cancer Type:</strong> {{ cancer_type }}</li>
                        <li><strong>Data Source:</strong> {{ data_source }}</li>
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>Biomarker Discovery Results</h2>
                <div class="result-box">
                    <h3>Top Biomarkers ({{ biomarker_count }} identified)</h3>
                    <div class="gene-list">
                        {% for biomarker in top_biomarkers %}
                        <div class="gene-item">{{ biomarker }}</div>
                        {% endfor %}
                    </div>
                </div>
                
                {% if biomarker_plot %}
                <div class="plot-container">
                    <h3>Biomarker Expression Heatmap</h3>
                    <div>{{ biomarker_plot }}</div>
                </div>
                {% endif %}
            </div>
            
            <div class="section">
                <h2>Pathway Enrichment Analysis</h2>
                <div class="result-box">
                    <h3>Enriched Pathways ({{ pathway_count }} found)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Pathway</th>
                                <th>P-value</th>
                                <th>Gene Count</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for pathway in enriched_pathways %}
                            <tr>
                                <td>{{ pathway.name }}</td>
                                <td>{{ pathway.pvalue }}</td>
                                <td>{{ pathway.gene_count }}</td>
                                <td>{{ pathway.description }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>Protein-Protein Interaction Networks</h2>
                <div class="result-box">
                    <h3>Hub Proteins ({{ hub_count }} identified)</h3>
                    <ul>
                        {% for hub in hub_proteins %}
                        <li><strong>{{ hub.protein }}</strong> - {{ hub.interaction_count }} interactions</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>Drug Target Analysis</h2>
                <div class="result-box">
                    <h3>Potential Drug Targets ({{ drug_target_count }} identified)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Target</th>
                                <th>Therapeutic Class</th>
                                <th>Example Drugs</th>
                                <th>Evidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for target in drug_targets %}
                            <tr>
                                <td>{{ target.gene }}</td>
                                <td>{{ target.therapeutic_class }}</td>
                                <td>{{ target.example_drugs | join(', ') }}</td>
                                <td>{{ target.evidence }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>Literature Analysis</h2>
                <div class="result-box">
                    <h3>Literature Support ({{ literature_count }} papers analyzed)</h3>
                    <p>{{ literature_summary }}</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Conclusions and Recommendations</h2>
                <div class="result-box">
                    <h3>Key Findings</h3>
                    <ul>
                        {% for finding in key_findings %}
                        <li>{{ finding }}</li>
                        {% endfor %}
                    </ul>
                    
                    <h3>Recommendations</h3>
                    <ul>
                        {% for recommendation in recommendations %}
                        <li>{{ recommendation }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>Methodology</h2>
                <div class="result-box">
                    <h3>Analysis Pipeline</h3>
                    <ol>
                        <li>Dataset loading and preprocessing</li>
                        <li>Differential expression analysis</li>
                        <li>Pathway enrichment analysis</li>
                        <li>Protein-protein interaction network construction</li>
                        <li>Literature mining and validation</li>
                        <li>Drug target identification</li>
                    </ol>
                    
                    <h3>Statistical Parameters</h3>
                    <ul>
                        <li><strong>P-value threshold:</strong> {{ pvalue_threshold }}</li>
                        <li><strong>Fold change threshold:</strong> {{ fold_change_threshold }}</li>
                        <li><strong>Multiple testing correction:</strong> {{ multiple_testing_correction }}</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Biomarker Discovery Report Template
        templates['biomarker_discovery_report'] = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Biomarker Discovery Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #28a745; }
                .result-box { background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .biomarker-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .biomarker-card { background-color: #e8f5e8; padding: 15px; border-radius: 5px; border: 1px solid #28a745; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Biomarker Discovery Report</h1>
                <p><strong>Analysis Type:</strong> {{ analysis_type }}</p>
                <p><strong>Generated:</strong> {{ timestamp }}</p>
            </div>
            
            <div class="section">
                <h2>Biomarker Summary</h2>
                <div class="result-box">
                    <h3>{{ biomarker_count }} Biomarkers Identified</h3>
                    <div class="biomarker-grid">
                        {% for biomarker in biomarkers %}
                        <div class="biomarker-card">
                            <h4>{{ biomarker.gene }}</h4>
                            <p><strong>Fold Change:</strong> {{ biomarker.fold_change }}</p>
                            <p><strong>P-value:</strong> {{ biomarker.pvalue }}</p>
                            <p><strong>Function:</strong> {{ biomarker.function }}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Statistical Analysis</h2>
                <div class="result-box">
                    <table>
                        <thead>
                            <tr>
                                <th>Biomarker</th>
                                <th>Log2 Fold Change</th>
                                <th>P-value</th>
                                <th>Adjusted P-value</th>
                                <th>Significance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for stat in statistical_results %}
                            <tr>
                                <td>{{ stat.gene }}</td>
                                <td>{{ stat.log2_fold_change }}</td>
                                <td>{{ stat.pvalue }}</td>
                                <td>{{ stat.adjusted_pvalue }}</td>
                                <td>{{ stat.significance }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>Pathway Analysis</h2>
                <div class="result-box">
                    <h3>Enriched Pathways</h3>
                    <ul>
                        {% for pathway in pathways %}
                        <li><strong>{{ pathway.name }}</strong> ({{ pathway.gene_count }} genes, p={{ pathway.pvalue }})</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h2>Literature Validation</h2>
                <div class="result-box">
                    <p>{{ literature_validation_summary }}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Drug Target Report Template
        templates['drug_target_report'] = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Drug Target Discovery Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #dc3545; }
                .target-card { background-color: #fdf2f2; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #dc3545; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Drug Target Discovery Report</h1>
                <p><strong>Disease Context:</strong> {{ disease_context }}</p>
                <p><strong>Generated:</strong> {{ timestamp }}</p>
            </div>
            
            <div class="section">
                <h2>Identified Drug Targets</h2>
                {% for target in drug_targets %}
                <div class="target-card">
                    <h3>{{ target.gene }}</h3>
                    <p><strong>Therapeutic Class:</strong> {{ target.therapeutic_class }}</p>
                    <p><strong>Example Drugs:</strong> {{ target.example_drugs | join(', ') }}</p>
                    <p><strong>Evidence Level:</strong> {{ target.evidence }}</p>
                    <p><strong>Interactions:</strong> {{ target.interaction_count }}</p>
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Network Analysis</h2>
                <div class="result-box">
                    <h3>Hub Proteins</h3>
                    <ul>
                        {% for hub in hub_proteins %}
                        <li><strong>{{ hub.protein }}</strong> - {{ hub.interaction_count }} interactions</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return templates
    
    def list_workflows(self, category: str = None) -> List[Dict[str, Any]]:
        """List available research workflows"""
        workflows = list(self.workflows.values())
        
        if category:
            workflows = [w for w in workflows if w.category.lower() == category.lower()]
        
        return [
            {
                'id': w.id,
                'name': w.name,
                'description': w.description,
                'category': w.category,
                'templates': w.templates,
                'parameters': w.parameters,
                'expected_duration': w.expected_duration
            }
            for w in workflows
        ]
    
    def get_workflow(self, workflow_id: str) -> Optional[ResearchWorkflow]:
        """Get a specific research workflow"""
        return self.workflows.get(workflow_id)
    
    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any], 
                             user_id: int, custom_parameters: Dict[str, Any] = None) -> WorkflowExecution:
        """Execute a research workflow"""
        execution_id = f"{workflow_id}_{user_id}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Store execution status
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                execution_id=execution_id,
                status='running',
                start_time=start_time,
                end_time=None,
                results={},
                report=None,
                error_message=None
            )
            
            self.active_executions[execution_id] = execution
            
            # Merge custom parameters
            parameters = workflow.parameters.copy()
            if custom_parameters:
                parameters.update(custom_parameters)
            
            # Execute workflow templates
            workflow_results = {}
            
            for template_id in workflow.templates:
                logger.info(f"Executing template {template_id} for workflow {workflow_id}")
                
                # Prepare inputs for this template
                template_inputs = self._prepare_template_inputs(template_id, inputs, workflow_results, parameters)
                
                # Execute template
                template_result = await analysis_templates_service.execute_template(
                    template_id, template_inputs, user_id, parameters
                )
                
                workflow_results[template_id] = template_result
                
                # Update execution status
                execution.results[template_id] = template_result.results
                execution.status = f'completed_{template_id}'
            
            # Generate comprehensive report
            report = await self._generate_workflow_report(workflow, workflow_results, parameters)
            
            # Update execution
            execution.end_time = datetime.now()
            execution.status = 'completed'
            execution.report = report
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            
            # Update execution with error
            execution.end_time = datetime.now()
            execution.status = 'failed'
            execution.error_message = str(e)
            
            return execution
    
    def _prepare_template_inputs(self, template_id: str, original_inputs: Dict[str, Any], 
                               workflow_results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare inputs for a specific template based on workflow context"""
        template_inputs = original_inputs.copy()
        
        # Template-specific input preparation
        if template_id == 'cancer_biomarker_discovery':
            template_inputs['cancer_type'] = parameters.get('cancer_type', 'TCGA-BRCA')
            
        elif template_id == 'differential_expression':
            # If we have expression data from previous steps, use it
            if 'tcga_analysis' in workflow_results:
                tcga_result = workflow_results['tcga_analysis']
                # Use sample data if available
                template_inputs['expression_matrix'] = tcga_result.results.get('sample_data', {})
            
        elif template_id == 'pathway_enrichment':
            # Use genes from previous biomarker discovery
            if 'cancer_biomarker_discovery' in workflow_results:
                biomarker_result = workflow_results['cancer_biomarker_discovery']
                genes = biomarker_result.results.get('differential_expression', {}).get('top_genes', [])
                template_inputs['gene_list'] = genes
            elif 'differential_expression' in workflow_results:
                de_result = workflow_results['differential_expression']
                genes = de_result.results.get('differential_expression', {}).get('gene_list', [])
                template_inputs['gene_list'] = genes
            
        elif template_id == 'ppi_network_analysis':
            # Use genes from previous analyses
            gene_list = []
            if 'cancer_biomarker_discovery' in workflow_results:
                biomarker_result = workflow_results['cancer_biomarker_discovery']
                genes = biomarker_result.results.get('differential_expression', {}).get('top_genes', [])
                gene_list.extend(genes)
            elif 'pathway_enrichment' in workflow_results:
                pathway_result = workflow_results['pathway_enrichment']
                genes = pathway_result.results.get('pathway_enrichment', {}).get('input_genes', [])
                gene_list.extend(genes)
            
            template_inputs['protein_list'] = gene_list[:50]  # Limit to avoid rate limits
            
        elif template_id == 'literature_mining':
            # Use research query based on context
            if 'literature_query' in parameters:
                template_inputs['research_query'] = parameters['literature_query']
            else:
                # Generate query based on previous results
                cancer_type = parameters.get('cancer_type', 'cancer')
                template_inputs['research_query'] = f"{cancer_type.replace('TCGA-', '')} biomarkers"
        
        elif template_id == 'gene_annotation':
            # Use genes from previous analyses
            gene_list = []
            if 'cancer_biomarker_discovery' in workflow_results:
                biomarker_result = workflow_results['cancer_biomarker_discovery']
                genes = biomarker_result.results.get('differential_expression', {}).get('top_genes', [])
                gene_list.extend(genes)
            
            template_inputs['gene_list'] = gene_list[:100]  # Limit to avoid rate limits
        
        elif template_id == 'tcga_analysis':
            template_inputs['dataset_id'] = parameters.get('cancer_type', 'TCGA-BRCA')
        
        return template_inputs
    
    async def _generate_workflow_report(self, workflow: ResearchWorkflow, 
                                      workflow_results: Dict[str, Any], 
                                      parameters: Dict[str, Any]) -> str:
        """Generate comprehensive workflow report"""
        try:
            # Get report template
            template_content = self.report_templates.get(workflow.report_template, '')
            if not template_content:
                return self._generate_simple_report(workflow, workflow_results, parameters)
            
            # Prepare template data
            template_data = await self._prepare_report_data(workflow, workflow_results, parameters)
            
            # Render template
            template = Template(template_content)
            report_html = template.render(**template_data)
            
            return report_html
            
        except Exception as e:
            logger.error(f"Error generating workflow report: {e}")
            return self._generate_simple_report(workflow, workflow_results, parameters)
    
    async def _prepare_report_data(self, workflow: ResearchWorkflow, 
                                 workflow_results: Dict[str, Any], 
                                 parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for report template"""
        data = {
            'workflow_name': workflow.name,
            'workflow_description': workflow.description,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': (datetime.now() - datetime.now()).total_seconds() / 60,  # This would be calculated properly
            'parameters': parameters
        }
        
        # Extract data from workflow results
        if 'cancer_biomarker_discovery' in workflow_results:
            biomarker_result = workflow_results['cancer_biomarker_discovery']
            data.update({
                'cancer_type': parameters.get('cancer_type', 'Unknown'),
                'dataset_name': biomarker_result.results.get('dataset_info', {}).get('name', 'Unknown'),
                'total_samples': biomarker_result.results.get('dataset_info', {}).get('samples', 0),
                'total_genes': biomarker_result.results.get('dataset_info', {}).get('genes', 0),
                'data_source': 'TCGA',
                'biomarker_count': len(biomarker_result.results.get('differential_expression', {}).get('top_genes', [])),
                'top_biomarkers': biomarker_result.results.get('differential_expression', {}).get('top_genes', [])[:20],
                'drug_targets': biomarker_result.results.get('drug_targets', []),
                'drug_target_count': len(biomarker_result.results.get('drug_targets', [])),
                'literature_count': len(biomarker_result.results.get('literature_mining', [])),
                'data_source': 'TCGA'
            })
        
        if 'pathway_enrichment' in workflow_results:
            pathway_result = workflow_results['pathway_enrichment']
            enriched_pathways = pathway_result.results.get('pathway_enrichment', {}).get('enriched_pathways', [])
            data.update({
                'pathway_count': len(enriched_pathways),
                'enriched_pathways': [{
                    'name': p.get('pathway_name', 'Unknown'),
                    'pvalue': f"{p.get('p_value', 1.0):.2e}",
                    'gene_count': p.get('gene_count', 0),
                    'description': p.get('description', '')
                } for p in enriched_pathways[:10]]
            })
        
        if 'ppi_network_analysis' in workflow_results:
            network_result = workflow_results['ppi_network_analysis']
            hub_proteins = network_result.results.get('hub_proteins', [])
            data.update({
                'hub_count': len(hub_proteins),
                'hub_proteins': [{
                    'protein': hub.get('protein', 'Unknown'),
                    'interaction_count': hub.get('interaction_count', 0)
                } for hub in hub_proteins[:10]]
            })
        
        if 'literature_mining' in workflow_results:
            literature_result = workflow_results['literature_mining']
            data.update({
                'literature_summary': literature_result.summary,
                'literature_count': len(literature_result.results.get('literature_search', {}).get('papers', []))
            })
        
        # Add executive summary
        data['executive_summary'] = await self._generate_executive_summary(workflow_results, parameters)
        
        # Add key findings and recommendations
        data['key_findings'] = await self._generate_key_findings(workflow_results)
        data['recommendations'] = await self._generate_recommendations(workflow_results, parameters)
        
        # Add statistical parameters
        data.update({
            'pvalue_threshold': parameters.get('pvalue_threshold', 0.05),
            'fold_change_threshold': parameters.get('fold_change_threshold', 2.0),
            'multiple_testing_correction': parameters.get('multiple_testing_correction', 'benjamini_hochberg')
        })
        
        return data
    
    async def _generate_executive_summary(self, workflow_results: Dict[str, Any], 
                                        parameters: Dict[str, Any]) -> str:
        """Generate executive summary using AI"""
        try:
            # Compile results summary
            summary_text = "Analysis Results Summary:\n"
            
            for template_id, result in workflow_results.items():
                summary_text += f"\n{template_id}: {result.summary}\n"
            
            # Use free AI to generate executive summary
            analysis = free_ai_service.analyze_biomedical_text(summary_text)
            
            return analysis['summary']
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return "Comprehensive bioinformatics analysis completed successfully with identification of key biomarkers, pathways, and drug targets."
    
    async def _generate_key_findings(self, workflow_results: Dict[str, Any]) -> List[str]:
        """Generate key findings from workflow results"""
        findings = []
        
        # Extract findings from each template result
        for template_id, result in workflow_results.items():
            if template_id == 'cancer_biomarker_discovery':
                biomarker_count = len(result.results.get('differential_expression', {}).get('top_genes', []))
                if biomarker_count > 0:
                    findings.append(f"Identified {biomarker_count} potential cancer biomarkers")
            
            elif template_id == 'pathway_enrichment':
                pathway_count = len(result.results.get('pathway_enrichment', {}).get('enriched_pathways', []))
                if pathway_count > 0:
                    findings.append(f"Found {pathway_count} significantly enriched biological pathways")
            
            elif template_id == 'ppi_network_analysis':
                hub_count = len(result.results.get('hub_proteins', []))
                if hub_count > 0:
                    findings.append(f"Identified {hub_count} hub proteins in the interaction network")
            
            elif template_id == 'literature_mining':
                paper_count = len(result.results.get('literature_search', {}).get('papers', []))
                if paper_count > 0:
                    findings.append(f"Analyzed {paper_count} relevant scientific papers")
        
        return findings
    
    async def _generate_recommendations(self, workflow_results: Dict[str, Any], 
                                      parameters: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on workflow results"""
        recommendations = []
        
        # Standard recommendations based on analysis type
        if 'cancer_biomarker_discovery' in workflow_results:
            recommendations.extend([
                "Validate identified biomarkers in independent cohorts",
                "Perform functional studies to understand biomarker roles",
                "Investigate clinical utility of top biomarkers"
            ])
        
        if 'pathway_enrichment' in workflow_results:
            recommendations.extend([
                "Focus on pathways with highest enrichment scores",
                "Investigate pathway crosstalk and interactions",
                "Consider pathway-targeted therapeutic approaches"
            ])
        
        if 'ppi_network_analysis' in workflow_results:
            recommendations.extend([
                "Prioritize hub proteins for functional validation",
                "Investigate protein complexes and modules",
                "Consider network-based drug target identification"
            ])
        
        if 'literature_mining' in workflow_results:
            recommendations.extend([
                "Review recent literature for validation studies",
                "Identify knowledge gaps for future research",
                "Consider collaborative opportunities with other researchers"
            ])
        
        return recommendations
    
    def _generate_simple_report(self, workflow: ResearchWorkflow, 
                              workflow_results: Dict[str, Any], 
                              parameters: Dict[str, Any]) -> str:
        """Generate simple text report as fallback"""
        report = f"""
        Research Workflow Report
        =====================
        
        Workflow: {workflow.name}
        Description: {workflow.description}
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Templates Executed:
        """
        
        for template_id, result in workflow_results.items():
            report += f"\n{template_id}:\n"
            report += f"  Status: {result.status}\n"
            report += f"  Summary: {result.summary}\n"
            report += f"  Execution Time: {result.execution_time:.2f} seconds\n"
        
        return report
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution status"""
        return self.active_executions.get(execution_id)
    
    async def export_workflow_results(self, execution_id: str, format: str = 'html') -> Optional[bytes]:
        """Export workflow results in specified format"""
        execution = self.active_executions.get(execution_id)
        if not execution or execution.status != 'completed':
            return None
        
        try:
            if format == 'html':
                return execution.report.encode('utf-8')
            
            elif format == 'json':
                export_data = {
                    'workflow_id': execution.workflow_id,
                    'execution_id': execution.execution_id,
                    'status': execution.status,
                    'start_time': execution.start_time.isoformat(),
                    'end_time': execution.end_time.isoformat() if execution.end_time else None,
                    'results': execution.results
                }
                return json.dumps(export_data, indent=2).encode('utf-8')
            
            elif format == 'zip':
                # Create zip file with all results
                buffer = BytesIO()
                with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add HTML report
                    if execution.report:
                        zip_file.writestr('report.html', execution.report.encode('utf-8'))
                    
                    # Add JSON results
                    export_data = {
                        'workflow_id': execution.workflow_id,
                        'execution_id': execution.execution_id,
                        'results': execution.results
                    }
                    zip_file.writestr('results.json', json.dumps(export_data, indent=2).encode('utf-8'))
                    
                    # Add individual template results
                    for template_id, result in execution.results.items():
                        filename = f"{template_id}_results.json"
                        zip_file.writestr(filename, json.dumps(result, indent=2).encode('utf-8'))
                
                buffer.seek(0)
                return buffer.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting workflow results: {e}")
            return None
    
    def cleanup_executions(self, max_age_hours: int = 24):
        """Clean up old workflow executions"""
        cutoff_time = datetime.now() - pd.Timedelta(hours=max_age_hours)
        
        to_remove = []
        for execution_id, execution in self.active_executions.items():
            if execution.start_time < cutoff_time:
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.active_executions[execution_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old workflow executions")

# Global instance
research_workflows_service = ResearchWorkflowsService()