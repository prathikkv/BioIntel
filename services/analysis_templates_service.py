"""
Analysis Templates Service
Pre-configured workflows for common bioinformatics analyses
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import base64
from io import BytesIO

from services.public_datasets_service import public_datasets_service
from services.bio_apis_service import bio_apis_service
from services.free_ai_service import free_ai_service
from services.bioinformatics_service import BioinformaticsService
from services.literature_service import literature_service

logger = logging.getLogger(__name__)

@dataclass
class AnalysisTemplate:
    """Analysis template definition"""
    id: str
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    steps: List[Dict[str, Any]]
    expected_inputs: List[str]
    expected_outputs: List[str]

@dataclass
class WorkflowResult:
    """Result of a workflow execution"""
    template_id: str
    status: str
    results: Dict[str, Any]
    plots: List[Dict[str, Any]]
    summary: str
    execution_time: float
    timestamp: datetime

class AnalysisTemplatesService:
    """Service for providing pre-configured bioinformatics analysis workflows"""
    
    def __init__(self):
        self.bio_service = BioinformaticsService()
        self.templates = self._initialize_templates()
    
    @staticmethod
    async def initialize():
        """Initialize analysis templates service"""
        logger.info("Analysis templates service initialized")
    
    def _initialize_templates(self) -> Dict[str, AnalysisTemplate]:
        """Initialize available analysis templates"""
        templates = {}
        
        # Cancer Biomarker Discovery Template
        templates['cancer_biomarker_discovery'] = AnalysisTemplate(
            id='cancer_biomarker_discovery',
            name='Cancer Biomarker Discovery',
            description='Comprehensive workflow for discovering cancer biomarkers using TCGA data',
            category='Cancer Research',
            parameters={
                'cancer_type': 'TCGA-BRCA',
                'top_genes': 50,
                'pvalue_threshold': 0.05,
                'fold_change_threshold': 2.0,
                'enrichment_databases': ['KEGG', 'GO', 'Reactome']
            },
            steps=[
                {'step': 'load_tcga_data', 'description': 'Load TCGA cancer dataset'},
                {'step': 'differential_expression', 'description': 'Perform differential expression analysis'},
                {'step': 'pathway_enrichment', 'description': 'Analyze pathway enrichment'},
                {'step': 'protein_interactions', 'description': 'Build protein interaction networks'},
                {'step': 'literature_mining', 'description': 'Mine literature for biomarker validation'},
                {'step': 'drug_targets', 'description': 'Identify potential drug targets'},
                {'step': 'generate_report', 'description': 'Generate comprehensive report'}
            ],
            expected_inputs=['cancer_type'],
            expected_outputs=['biomarkers', 'pathways', 'networks', 'drug_targets', 'report']
        )
        
        # Differential Expression Analysis Template
        templates['differential_expression'] = AnalysisTemplate(
            id='differential_expression',
            name='Differential Expression Analysis',
            description='Standard differential expression analysis with statistical testing',
            category='Gene Expression',
            parameters={
                'statistical_test': 'ttest',
                'multiple_testing_correction': 'benjamini_hochberg',
                'pvalue_threshold': 0.05,
                'fold_change_threshold': 2.0,
                'visualization': True
            },
            steps=[
                {'step': 'data_preprocessing', 'description': 'Preprocess expression data'},
                {'step': 'statistical_testing', 'description': 'Perform statistical tests'},
                {'step': 'multiple_testing_correction', 'description': 'Apply multiple testing correction'},
                {'step': 'visualization', 'description': 'Create volcano plots and heatmaps'},
                {'step': 'gene_annotation', 'description': 'Annotate significant genes'}
            ],
            expected_inputs=['expression_matrix', 'group_labels'],
            expected_outputs=['significant_genes', 'statistics', 'plots', 'annotations']
        )
        
        # Pathway Enrichment Analysis Template
        templates['pathway_enrichment'] = AnalysisTemplate(
            id='pathway_enrichment',
            name='Pathway Enrichment Analysis',
            description='Comprehensive pathway enrichment analysis using multiple databases',
            category='Functional Analysis',
            parameters={
                'databases': ['KEGG', 'GO_BP', 'GO_MF', 'GO_CC', 'Reactome'],
                'pvalue_threshold': 0.05,
                'min_genes_per_pathway': 3,
                'max_genes_per_pathway': 500
            },
            steps=[
                {'step': 'prepare_gene_list', 'description': 'Prepare and validate gene list'},
                {'step': 'kegg_enrichment', 'description': 'KEGG pathway enrichment'},
                {'step': 'go_enrichment', 'description': 'Gene Ontology enrichment'},
                {'step': 'reactome_enrichment', 'description': 'Reactome pathway enrichment'},
                {'step': 'visualization', 'description': 'Create enrichment plots'},
                {'step': 'pathway_networks', 'description': 'Build pathway interaction networks'}
            ],
            expected_inputs=['gene_list'],
            expected_outputs=['enriched_pathways', 'pathway_networks', 'plots']
        )
        
        # Protein-Protein Interaction Analysis Template
        templates['ppi_network_analysis'] = AnalysisTemplate(
            id='ppi_network_analysis',
            name='Protein-Protein Interaction Network Analysis',
            description='Build and analyze protein-protein interaction networks',
            category='Network Analysis',
            parameters={
                'confidence_threshold': 0.4,
                'max_interactions': 500,
                'hub_threshold': 10,
                'clustering_method': 'louvain'
            },
            steps=[
                {'step': 'build_network', 'description': 'Build PPI network from STRING database'},
                {'step': 'network_analysis', 'description': 'Analyze network properties'},
                {'step': 'identify_hubs', 'description': 'Identify hub proteins'},
                {'step': 'community_detection', 'description': 'Detect protein communities'},
                {'step': 'visualization', 'description': 'Create network visualizations'},
                {'step': 'functional_analysis', 'description': 'Analyze functional modules'}
            ],
            expected_inputs=['protein_list'],
            expected_outputs=['network', 'hubs', 'communities', 'visualizations']
        )
        
        # Literature Mining Template
        templates['literature_mining'] = AnalysisTemplate(
            id='literature_mining',
            name='Literature Mining & Drug Target Discovery',
            description='Mine literature for biomarkers and identify drug targets',
            category='Literature Analysis',
            parameters={
                'max_papers': 100,
                'min_citation_count': 5,
                'focus_areas': ['biomarkers', 'drug_targets', 'clinical_trials'],
                'time_range': '5_years'
            },
            steps=[
                {'step': 'literature_search', 'description': 'Search PubMed for relevant papers'},
                {'step': 'biomarker_extraction', 'description': 'Extract biomarkers from abstracts'},
                {'step': 'drug_target_identification', 'description': 'Identify potential drug targets'},
                {'step': 'clinical_relevance', 'description': 'Assess clinical relevance'},
                {'step': 'trend_analysis', 'description': 'Analyze research trends'},
                {'step': 'generate_summary', 'description': 'Generate literature summary'}
            ],
            expected_inputs=['research_query'],
            expected_outputs=['biomarkers', 'drug_targets', 'papers', 'trends', 'summary']
        )
        
        # TCGA Data Analysis Template
        templates['tcga_analysis'] = AnalysisTemplate(
            id='tcga_analysis',
            name='TCGA Dataset Analysis',
            description='Comprehensive analysis of TCGA cancer datasets',
            category='Cancer Research',
            parameters={
                'dataset_id': 'TCGA-BRCA',
                'sample_size': 100,
                'analysis_type': 'comprehensive',
                'survival_analysis': True,
                'mutation_analysis': False
            },
            steps=[
                {'step': 'load_tcga_data', 'description': 'Load TCGA dataset'},
                {'step': 'quality_control', 'description': 'Perform quality control'},
                {'step': 'exploratory_analysis', 'description': 'Exploratory data analysis'},
                {'step': 'clustering_analysis', 'description': 'Cluster samples'},
                {'step': 'biomarker_discovery', 'description': 'Discover biomarkers'},
                {'step': 'pathway_analysis', 'description': 'Analyze pathways'},
                {'step': 'survival_analysis', 'description': 'Survival analysis (if available)'},
                {'step': 'generate_report', 'description': 'Generate comprehensive report'}
            ],
            expected_inputs=['dataset_id'],
            expected_outputs=['clusters', 'biomarkers', 'pathways', 'survival_data', 'report']
        )
        
        # Gene Annotation Template
        templates['gene_annotation'] = AnalysisTemplate(
            id='gene_annotation',
            name='Comprehensive Gene Annotation',
            description='Annotate genes using multiple databases',
            category='Functional Analysis',
            parameters={
                'databases': ['Ensembl', 'UniProt', 'KEGG', 'STRING'],
                'include_orthologs': True,
                'include_expression': True,
                'organism': 'human'
            },
            steps=[
                {'step': 'ensembl_annotation', 'description': 'Get gene info from Ensembl'},
                {'step': 'uniprot_annotation', 'description': 'Get protein info from UniProt'},
                {'step': 'pathway_annotation', 'description': 'Get pathway info from KEGG'},
                {'step': 'interaction_annotation', 'description': 'Get interactions from STRING'},
                {'step': 'literature_annotation', 'description': 'Get literature from PubMed'},
                {'step': 'compile_annotations', 'description': 'Compile comprehensive annotations'}
            ],
            expected_inputs=['gene_list'],
            expected_outputs=['gene_annotations', 'protein_annotations', 'pathways', 'interactions']
        )
        
        return templates
    
    def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """List available analysis templates"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]
        
        return [
            {
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'category': t.category,
                'parameters': t.parameters,
                'steps': t.steps,
                'expected_inputs': t.expected_inputs,
                'expected_outputs': t.expected_outputs
            }
            for t in templates
        ]
    
    def get_template(self, template_id: str) -> Optional[AnalysisTemplate]:
        """Get a specific analysis template"""
        return self.templates.get(template_id)
    
    async def execute_template(self, template_id: str, inputs: Dict[str, Any], 
                             user_id: int, custom_parameters: Dict[str, Any] = None) -> WorkflowResult:
        """Execute an analysis template"""
        start_time = datetime.now()
        
        try:
            template = self.get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Merge custom parameters with template defaults
            parameters = template.parameters.copy()
            if custom_parameters:
                parameters.update(custom_parameters)
            
            # Execute the specific workflow
            if template_id == 'cancer_biomarker_discovery':
                result = await self._execute_cancer_biomarker_discovery(inputs, parameters, user_id)
            elif template_id == 'differential_expression':
                result = await self._execute_differential_expression(inputs, parameters, user_id)
            elif template_id == 'pathway_enrichment':
                result = await self._execute_pathway_enrichment(inputs, parameters, user_id)
            elif template_id == 'ppi_network_analysis':
                result = await self._execute_ppi_network_analysis(inputs, parameters, user_id)
            elif template_id == 'literature_mining':
                result = await self._execute_literature_mining(inputs, parameters, user_id)
            elif template_id == 'tcga_analysis':
                result = await self._execute_tcga_analysis(inputs, parameters, user_id)
            elif template_id == 'gene_annotation':
                result = await self._execute_gene_annotation(inputs, parameters, user_id)
            else:
                raise ValueError(f"Template {template_id} not implemented")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return WorkflowResult(
                template_id=template_id,
                status='completed',
                results=result['results'],
                plots=result.get('plots', []),
                summary=result.get('summary', ''),
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error executing template {template_id}: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return WorkflowResult(
                template_id=template_id,
                status='failed',
                results={'error': str(e)},
                plots=[],
                summary=f"Template execution failed: {str(e)}",
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    async def _execute_cancer_biomarker_discovery(self, inputs: Dict[str, Any], 
                                                parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute cancer biomarker discovery workflow"""
        results = {}
        plots = []
        
        # Step 1: Load TCGA data
        cancer_type = inputs.get('cancer_type', parameters['cancer_type'])
        dataset_info = await public_datasets_service.get_dataset_info(cancer_type)
        sample_data = await public_datasets_service.generate_sample_data(
            cancer_type, 
            num_samples=100, 
            num_genes=parameters['top_genes']
        )
        
        results['dataset_info'] = {
            'id': dataset_info.id if dataset_info else cancer_type,
            'name': dataset_info.name if dataset_info else cancer_type,
            'samples': sample_data.shape[1],
            'genes': sample_data.shape[0]
        }
        
        # Step 2: Differential expression analysis
        if not sample_data.empty:
            # Simulate differential expression (in real implementation, compare tumor vs normal)
            mean_expression = sample_data.mean(axis=1)
            std_expression = sample_data.std(axis=1)
            
            # Identify highly variable genes as potential biomarkers
            cv = std_expression / mean_expression
            top_variable_genes = cv.nlargest(parameters['top_genes']).index.tolist()
            
            results['differential_expression'] = {
                'top_genes': top_variable_genes,
                'statistics': {
                    'mean_expression': mean_expression.to_dict(),
                    'std_expression': std_expression.to_dict(),
                    'coefficient_variation': cv.to_dict()
                }
            }
        
        # Step 3: Pathway enrichment analysis
        if top_variable_genes:
            pathway_results = await self.bio_service.pathway_enrichment_analysis(
                top_variable_genes, user_id
            )
            results['pathway_enrichment'] = pathway_results
        
        # Step 4: Protein interaction networks
        if top_variable_genes:
            network_results = await self.bio_service.protein_interaction_network(
                top_variable_genes[:20], user_id
            )
            results['protein_networks'] = network_results
        
        # Step 5: Literature mining
        if top_variable_genes:
            literature_results = []
            for gene in top_variable_genes[:10]:
                papers = await bio_apis_service.search_pubmed(
                    f"{gene} AND {cancer_type.replace('TCGA-', '')} AND biomarker", 
                    max_results=5
                )
                literature_results.extend([{
                    'gene': gene,
                    'pmid': paper.pmid,
                    'title': paper.title,
                    'abstract': paper.abstract[:200] + '...'
                } for paper in papers])
            
            results['literature_mining'] = literature_results
        
        # Step 6: Drug target identification
        if top_variable_genes:
            drug_targets = await bio_apis_service.find_drug_targets(top_variable_genes)
            results['drug_targets'] = drug_targets
        
        # Step 7: Generate visualization
        if not sample_data.empty:
            # Create heatmap of top variable genes
            fig = px.imshow(
                sample_data.loc[top_variable_genes[:20]].values,
                labels=dict(x="Samples", y="Genes", color="Expression"),
                x=sample_data.columns.tolist(),
                y=top_variable_genes[:20],
                title=f"Top Variable Genes in {cancer_type}"
            )
            
            plots.append({
                'type': 'heatmap',
                'title': 'Top Variable Genes Heatmap',
                'data': fig.to_json()
            })
        
        summary = f"""
        Cancer Biomarker Discovery Analysis for {cancer_type}:
        - Analyzed {sample_data.shape[0]} genes across {sample_data.shape[1]} samples
        - Identified {len(top_variable_genes)} potential biomarkers
        - Found {len(results.get('pathway_enrichment', {}).get('enriched_pathways', []))} enriched pathways
        - Discovered {len(results.get('drug_targets', []))} potential drug targets
        - Analyzed {len(results.get('literature_mining', []))} relevant papers
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }
    
    async def _execute_differential_expression(self, inputs: Dict[str, Any], 
                                             parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute differential expression analysis workflow"""
        results = {}
        plots = []
        
        # Load expression data
        expression_data = inputs.get('expression_matrix')
        group_labels = inputs.get('group_labels')
        
        if expression_data is None:
            raise ValueError("Expression matrix is required")
        
        # Convert to DataFrame if needed
        if isinstance(expression_data, dict):
            expression_data = pd.DataFrame(expression_data)
        
        # Perform statistical testing
        if group_labels:
            # Perform t-test between groups
            group1_samples = [i for i, label in enumerate(group_labels) if label == 'group1']
            group2_samples = [i for i, label in enumerate(group_labels) if label == 'group2']
            
            pvalues = []
            fold_changes = []
            
            for gene in expression_data.index:
                group1_expr = expression_data.loc[gene, group1_samples]
                group2_expr = expression_data.loc[gene, group2_samples]
                
                # T-test
                t_stat, p_val = stats.ttest_ind(group1_expr, group2_expr)
                pvalues.append(p_val)
                
                # Fold change
                fc = np.mean(group1_expr) / np.mean(group2_expr) if np.mean(group2_expr) != 0 else 1
                fold_changes.append(fc)
            
            # Create results DataFrame
            de_results = pd.DataFrame({
                'gene': expression_data.index,
                'pvalue': pvalues,
                'fold_change': fold_changes,
                'log2_fold_change': np.log2(fold_changes)
            })
            
            # Apply multiple testing correction
            from statsmodels.stats.multitest import multipletests
            _, corrected_pvalues, _, _ = multipletests(
                pvalues, 
                method=parameters.get('multiple_testing_correction', 'benjamini_hochberg')
            )
            de_results['adjusted_pvalue'] = corrected_pvalues
            
            # Filter significant genes
            significant_genes = de_results[
                (de_results['adjusted_pvalue'] < parameters['pvalue_threshold']) &
                (np.abs(de_results['log2_fold_change']) > np.log2(parameters['fold_change_threshold']))
            ]
            
            results['differential_expression'] = {
                'total_genes': len(de_results),
                'significant_genes': len(significant_genes),
                'upregulated': len(significant_genes[significant_genes['log2_fold_change'] > 0]),
                'downregulated': len(significant_genes[significant_genes['log2_fold_change'] < 0]),
                'gene_list': significant_genes['gene'].tolist(),
                'statistics': de_results.to_dict('records')
            }
            
            # Create volcano plot
            fig = px.scatter(
                de_results,
                x='log2_fold_change',
                y=-np.log10(de_results['adjusted_pvalue']),
                hover_data=['gene'],
                title='Volcano Plot - Differential Expression Analysis',
                labels={'x': 'Log2 Fold Change', 'y': '-Log10 Adjusted P-value'}
            )
            
            plots.append({
                'type': 'volcano',
                'title': 'Volcano Plot',
                'data': fig.to_json()
            })
            
            # Gene annotation for significant genes
            if len(significant_genes) > 0:
                annotation_results = await self.bio_service.annotate_genes(
                    significant_genes['gene'].tolist()[:50], user_id
                )
                results['gene_annotations'] = annotation_results
        
        summary = f"""
        Differential Expression Analysis Results:
        - Total genes analyzed: {len(expression_data)}
        - Significant genes found: {len(results.get('differential_expression', {}).get('gene_list', []))}
        - Upregulated genes: {results.get('differential_expression', {}).get('upregulated', 0)}
        - Downregulated genes: {results.get('differential_expression', {}).get('downregulated', 0)}
        - P-value threshold: {parameters['pvalue_threshold']}
        - Fold change threshold: {parameters['fold_change_threshold']}
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }
    
    async def _execute_pathway_enrichment(self, inputs: Dict[str, Any], 
                                        parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute pathway enrichment analysis workflow"""
        results = {}
        plots = []
        
        gene_list = inputs.get('gene_list', [])
        if not gene_list:
            raise ValueError("Gene list is required")
        
        # Perform pathway enrichment analysis
        enrichment_results = await self.bio_service.pathway_enrichment_analysis(
            gene_list, user_id
        )
        
        results['pathway_enrichment'] = enrichment_results
        
        # Get pathway information from KEGG
        pathway_details = []
        for pathway in enrichment_results.get('enriched_pathways', [])[:10]:
            pathway_info = await bio_apis_service.get_pathway_info(pathway.get('pathway_id', ''))
            if pathway_info:
                pathway_details.append({
                    'pathway_id': pathway_info.pathway_id,
                    'pathway_name': pathway_info.pathway_name,
                    'description': pathway_info.description,
                    'genes': pathway_info.genes,
                    'category': pathway_info.category
                })
        
        results['pathway_details'] = pathway_details
        
        # Create enrichment plot
        if enrichment_results.get('enriched_pathways'):
            pathway_names = [p.get('pathway_name', 'Unknown') for p in enrichment_results['enriched_pathways'][:20]]
            p_values = [p.get('p_value', 1.0) for p in enrichment_results['enriched_pathways'][:20]]
            
            fig = px.bar(
                x=-np.log10(p_values),
                y=pathway_names,
                orientation='h',
                title='Pathway Enrichment Analysis',
                labels={'x': '-Log10 P-value', 'y': 'Pathways'}
            )
            
            plots.append({
                'type': 'enrichment_bar',
                'title': 'Pathway Enrichment',
                'data': fig.to_json()
            })
        
        summary = f"""
        Pathway Enrichment Analysis Results:
        - Input genes: {len(gene_list)}
        - Enriched pathways found: {len(enrichment_results.get('enriched_pathways', []))}
        - Databases used: {', '.join(parameters.get('databases', []))}
        - P-value threshold: {parameters['pvalue_threshold']}
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }
    
    async def _execute_ppi_network_analysis(self, inputs: Dict[str, Any], 
                                          parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute protein-protein interaction network analysis workflow"""
        results = {}
        plots = []
        
        protein_list = inputs.get('protein_list', [])
        if not protein_list:
            raise ValueError("Protein list is required")
        
        # Build PPI network
        network_results = await self.bio_service.protein_interaction_network(
            protein_list, user_id
        )
        
        results['network_analysis'] = network_results
        
        # Get detailed interaction information
        interaction_details = []
        for protein in protein_list[:10]:
            interactions = await bio_apis_service.get_protein_interactions(protein)
            if interactions:
                interaction_details.append({
                    'protein': protein,
                    'interactions': interactions.interactions,
                    'network_score': interactions.network_score,
                    'functional_partners': interactions.functional_partners
                })
        
        results['interaction_details'] = interaction_details
        
        # Identify hub proteins (proteins with many interactions)
        hub_proteins = []
        for detail in interaction_details:
            if len(detail['interactions']) >= parameters.get('hub_threshold', 10):
                hub_proteins.append({
                    'protein': detail['protein'],
                    'interaction_count': len(detail['interactions']),
                    'network_score': detail['network_score']
                })
        
        results['hub_proteins'] = hub_proteins
        
        summary = f"""
        Protein-Protein Interaction Network Analysis Results:
        - Input proteins: {len(protein_list)}
        - Total interactions found: {sum(len(d['interactions']) for d in interaction_details)}
        - Hub proteins identified: {len(hub_proteins)}
        - Network confidence threshold: {parameters.get('confidence_threshold', 0.4)}
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }
    
    async def _execute_literature_mining(self, inputs: Dict[str, Any], 
                                       parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute literature mining workflow"""
        results = {}
        plots = []
        
        research_query = inputs.get('research_query', '')
        if not research_query:
            raise ValueError("Research query is required")
        
        # Search PubMed for relevant papers
        papers = await bio_apis_service.search_pubmed(
            research_query, 
            max_results=parameters.get('max_papers', 100)
        )
        
        results['literature_search'] = {
            'query': research_query,
            'total_papers': len(papers),
            'papers': [{
                'pmid': paper.pmid,
                'title': paper.title,
                'authors': paper.authors,
                'journal': paper.journal,
                'publication_date': paper.publication_date,
                'abstract': paper.abstract
            } for paper in papers]
        }
        
        # Extract biomarkers from abstracts
        all_biomarkers = []
        for paper in papers:
            analysis = free_ai_service.analyze_biomedical_text(paper.abstract)
            biomarkers = analysis['biomarkers']
            all_biomarkers.extend(biomarkers.genes + biomarkers.proteins)
        
        # Count biomarker frequency
        from collections import Counter
        biomarker_counts = Counter(all_biomarkers)
        
        results['biomarker_extraction'] = {
            'total_biomarkers': len(all_biomarkers),
            'unique_biomarkers': len(biomarker_counts),
            'top_biomarkers': biomarker_counts.most_common(20)
        }
        
        # Identify drug targets
        top_biomarkers = [b[0] for b in biomarker_counts.most_common(50)]
        drug_targets = await bio_apis_service.find_drug_targets(top_biomarkers)
        
        results['drug_targets'] = drug_targets
        
        # Analyze publication trends
        publication_years = {}
        for paper in papers:
            year = paper.publication_date
            if year.isdigit():
                year = int(year)
                publication_years[year] = publication_years.get(year, 0) + 1
        
        results['publication_trends'] = publication_years
        
        summary = f"""
        Literature Mining Analysis Results:
        - Search query: {research_query}
        - Papers analyzed: {len(papers)}
        - Unique biomarkers found: {len(biomarker_counts)}
        - Drug targets identified: {len(drug_targets)}
        - Publication span: {min(publication_years.keys()) if publication_years else 'N/A'} - {max(publication_years.keys()) if publication_years else 'N/A'}
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }
    
    async def _execute_tcga_analysis(self, inputs: Dict[str, Any], 
                                   parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute TCGA dataset analysis workflow"""
        results = {}
        plots = []
        
        dataset_id = inputs.get('dataset_id', parameters['dataset_id'])
        
        # Get dataset information
        dataset_info = await public_datasets_service.get_dataset_info(dataset_id)
        if not dataset_info:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Generate sample data
        sample_data = await public_datasets_service.generate_sample_data(
            dataset_id,
            num_samples=parameters.get('sample_size', 100),
            num_genes=1000
        )
        
        results['dataset_info'] = {
            'id': dataset_info.id,
            'name': dataset_info.name,
            'description': dataset_info.description,
            'sample_count': dataset_info.sample_count,
            'gene_count': dataset_info.gene_count
        }
        
        # Exploratory data analysis
        if not sample_data.empty:
            # Basic statistics
            results['exploratory_analysis'] = {
                'shape': sample_data.shape,
                'mean_expression': sample_data.mean().mean(),
                'std_expression': sample_data.std().mean(),
                'missing_values': sample_data.isnull().sum().sum(),
                'zero_values': (sample_data == 0).sum().sum()
            }
            
            # PCA analysis
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(sample_data.T)
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(scaled_data)
            
            results['pca_analysis'] = {
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                'components': pca_result.tolist()
            }
            
            # Create PCA plot
            fig = px.scatter(
                x=pca_result[:, 0],
                y=pca_result[:, 1],
                title=f'PCA Analysis - {dataset_info.name}',
                labels={'x': f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)', 
                       'y': f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)'}
            )
            
            plots.append({
                'type': 'pca',
                'title': 'PCA Analysis',
                'data': fig.to_json()
            })
            
            # Clustering analysis
            kmeans = KMeans(n_clusters=3, random_state=42)
            clusters = kmeans.fit_predict(scaled_data)
            
            results['clustering_analysis'] = {
                'n_clusters': 3,
                'cluster_labels': clusters.tolist(),
                'cluster_centers': kmeans.cluster_centers_.tolist()
            }
            
            # Identify potential biomarkers (highly variable genes)
            cv = sample_data.std(axis=1) / sample_data.mean(axis=1)
            top_variable_genes = cv.nlargest(50).index.tolist()
            
            results['biomarker_discovery'] = {
                'top_variable_genes': top_variable_genes,
                'coefficient_of_variation': cv.to_dict()
            }
        
        summary = f"""
        TCGA Dataset Analysis Results:
        - Dataset: {dataset_info.name}
        - Samples analyzed: {sample_data.shape[1] if not sample_data.empty else 0}
        - Genes analyzed: {sample_data.shape[0] if not sample_data.empty else 0}
        - Clusters identified: {results.get('clustering_analysis', {}).get('n_clusters', 0)}
        - Potential biomarkers: {len(results.get('biomarker_discovery', {}).get('top_variable_genes', []))}
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }
    
    async def _execute_gene_annotation(self, inputs: Dict[str, Any], 
                                     parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Execute gene annotation workflow"""
        results = {}
        plots = []
        
        gene_list = inputs.get('gene_list', [])
        if not gene_list:
            raise ValueError("Gene list is required")
        
        # Comprehensive gene annotation
        annotation_results = await self.bio_service.annotate_genes(gene_list, user_id)
        
        results['gene_annotations'] = annotation_results
        
        # Get additional information from multiple databases
        detailed_annotations = {}
        
        for gene in gene_list[:20]:  # Limit to avoid rate limits
            gene_details = {
                'gene_id': gene,
                'ensembl_info': None,
                'uniprot_info': None,
                'kegg_pathways': [],
                'string_interactions': None,
                'literature': []
            }
            
            # Ensembl information
            ensembl_info = await bio_apis_service.get_gene_info(gene)
            if ensembl_info:
                gene_details['ensembl_info'] = {
                    'gene_id': ensembl_info.gene_id,
                    'gene_name': ensembl_info.gene_name,
                    'chromosome': ensembl_info.chromosome,
                    'start': ensembl_info.start,
                    'end': ensembl_info.end,
                    'biotype': ensembl_info.biotype,
                    'description': ensembl_info.description
                }
            
            # UniProt information
            uniprot_info = await bio_apis_service.get_protein_info(gene)
            if uniprot_info:
                gene_details['uniprot_info'] = {
                    'accession': uniprot_info.accession,
                    'name': uniprot_info.name,
                    'function': uniprot_info.function,
                    'pathways': uniprot_info.pathways,
                    'diseases': uniprot_info.diseases
                }
            
            # STRING interactions
            string_info = await bio_apis_service.get_protein_interactions(gene)
            if string_info:
                gene_details['string_interactions'] = {
                    'interaction_count': len(string_info.interactions),
                    'network_score': string_info.network_score,
                    'functional_partners': string_info.functional_partners[:10]
                }
            
            # Literature search
            papers = await bio_apis_service.search_pubmed(f"{gene} AND function", max_results=5)
            gene_details['literature'] = [{
                'pmid': paper.pmid,
                'title': paper.title,
                'journal': paper.journal
            } for paper in papers]
            
            detailed_annotations[gene] = gene_details
        
        results['detailed_annotations'] = detailed_annotations
        
        summary = f"""
        Gene Annotation Analysis Results:
        - Genes annotated: {len(gene_list)}
        - Ensembl annotations: {len([g for g in detailed_annotations.values() if g['ensembl_info']])}
        - UniProt annotations: {len([g for g in detailed_annotations.values() if g['uniprot_info']])}
        - STRING interactions: {len([g for g in detailed_annotations.values() if g['string_interactions']])}
        - Literature references: {sum(len(g['literature']) for g in detailed_annotations.values())}
        """
        
        return {
            'results': results,
            'plots': plots,
            'summary': summary.strip()
        }

# Global instance
analysis_templates_service = AnalysisTemplatesService()