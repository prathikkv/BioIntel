"""
Free Bioinformatics APIs Service
Integrates with free public databases: PubMed, UniProt, Ensembl, STRING, KEGG
"""

import logging
import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus, urljoin
from functools import lru_cache
import re

logger = logging.getLogger(__name__)

@dataclass
class PubMedResult:
    """PubMed search result"""
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    publication_date: str
    doi: Optional[str] = None
    keywords: List[str] = None

@dataclass
class UniProtResult:
    """UniProt protein information"""
    accession: str
    name: str
    gene_names: List[str]
    organism: str
    function: str
    keywords: List[str]
    pathways: List[str]
    diseases: List[str]
    go_terms: List[str]

@dataclass
class EnsemblResult:
    """Ensembl gene information"""
    gene_id: str
    gene_name: str
    chromosome: str
    start: int
    end: int
    strand: int
    biotype: str
    description: str
    synonyms: List[str]

@dataclass
class STRINGResult:
    """STRING protein interaction result"""
    protein_id: str
    interactions: List[Dict[str, Any]]
    network_score: float
    functional_partners: List[str]

@dataclass
class KEGGResult:
    """KEGG pathway information"""
    pathway_id: str
    pathway_name: str
    genes: List[str]
    compounds: List[str]
    description: str
    category: str

class BioinformaticsAPIsService:
    """Service for accessing free bioinformatics APIs"""
    
    def __init__(self):
        self.session = None
        self.rate_limits = {
            'pubmed': {'requests': 3, 'window': 1},  # 3 requests per second
            'uniprot': {'requests': 10, 'window': 1},  # 10 requests per second
            'ensembl': {'requests': 15, 'window': 1},  # 15 requests per second
            'string': {'requests': 5, 'window': 1},   # 5 requests per second
            'kegg': {'requests': 10, 'window': 1}     # 10 requests per second
        }
        self.last_request_time = {}
    
    @staticmethod
    async def initialize():
        """Initialize bioinformatics APIs service"""
        logger.info("Bioinformatics APIs service initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _rate_limit(self, api_name: str):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        last_time = self.last_request_time.get(api_name, 0)
        
        rate_limit = self.rate_limits.get(api_name, {'requests': 1, 'window': 1})
        min_interval = rate_limit['window'] / rate_limit['requests']
        
        time_since_last = current_time - last_time
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time[api_name] = time.time()
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    # PubMed API Methods
    async def search_pubmed(self, query: str, max_results: int = 20) -> List[PubMedResult]:
        """
        Search PubMed for articles
        """
        try:
            await self._rate_limit('pubmed')
            session = await self._get_session()
            
            # Search for PMIDs
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    logger.error(f"PubMed search failed: {response.status}")
                    return []
                
                search_data = await response.json()
                pmids = search_data.get('esearchresult', {}).get('idlist', [])
            
            if not pmids:
                return []
            
            # Fetch article details
            await self._rate_limit('pubmed')
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml'
            }
            
            async with session.get(fetch_url, params=fetch_params) as response:
                if response.status != 200:
                    logger.error(f"PubMed fetch failed: {response.status}")
                    return []
                
                xml_data = await response.text()
                return self._parse_pubmed_xml(xml_data)
                
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_data: str) -> List[PubMedResult]:
        """Parse PubMed XML response"""
        try:
            root = ET.fromstring(xml_data)
            results = []
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract PMID
                    pmid = article.find('.//PMID').text
                    
                    # Extract title
                    title_elem = article.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else "No title"
                    
                    # Extract abstract
                    abstract_elem = article.find('.//AbstractText')
                    abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
                    
                    # Extract authors
                    authors = []
                    for author in article.findall('.//Author'):
                        last_name = author.find('LastName')
                        first_name = author.find('ForeName')
                        if last_name is not None and first_name is not None:
                            authors.append(f"{first_name.text} {last_name.text}")
                    
                    # Extract journal
                    journal_elem = article.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                    
                    # Extract publication date
                    pub_date_elem = article.find('.//PubDate/Year')
                    pub_date = pub_date_elem.text if pub_date_elem is not None else "Unknown date"
                    
                    # Extract DOI
                    doi_elem = article.find('.//ArticleId[@IdType="doi"]')
                    doi = doi_elem.text if doi_elem is not None else None
                    
                    # Extract keywords
                    keywords = []
                    for keyword in article.findall('.//Keyword'):
                        if keyword.text:
                            keywords.append(keyword.text)
                    
                    results.append(PubMedResult(
                        pmid=pmid,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        journal=journal,
                        publication_date=pub_date,
                        doi=doi,
                        keywords=keywords
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing PubMed article: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing PubMed XML: {e}")
            return []
    
    # UniProt API Methods
    async def get_protein_info(self, protein_id: str) -> Optional[UniProtResult]:
        """
        Get protein information from UniProt
        """
        try:
            await self._rate_limit('uniprot')
            session = await self._get_session()
            
            url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.json"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"UniProt request failed: {response.status}")
                    return None
                
                data = await response.json()
                return self._parse_uniprot_response(data)
                
        except Exception as e:
            logger.error(f"Error getting UniProt info: {e}")
            return None
    
    def _parse_uniprot_response(self, data: Dict) -> UniProtResult:
        """Parse UniProt JSON response"""
        try:
            accession = data.get('primaryAccession', '')
            name = data.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', '')
            
            # Extract gene names
            gene_names = []
            genes = data.get('genes', [])
            for gene in genes:
                if 'geneName' in gene:
                    gene_names.append(gene['geneName'].get('value', ''))
            
            # Extract organism
            organism = data.get('organism', {}).get('scientificName', '')
            
            # Extract function
            function = ""
            comments = data.get('comments', [])
            for comment in comments:
                if comment.get('commentType') == 'FUNCTION':
                    function = comment.get('texts', [{}])[0].get('value', '')
                    break
            
            # Extract keywords
            keywords = []
            for keyword in data.get('keywords', []):
                keywords.append(keyword.get('name', ''))
            
            # Extract pathways
            pathways = []
            for comment in comments:
                if comment.get('commentType') == 'PATHWAY':
                    pathways.append(comment.get('texts', [{}])[0].get('value', ''))
            
            # Extract diseases
            diseases = []
            for comment in comments:
                if comment.get('commentType') == 'DISEASE':
                    diseases.append(comment.get('disease', {}).get('diseaseId', ''))
            
            # Extract GO terms
            go_terms = []
            for ref in data.get('dbReferences', []):
                if ref.get('type') == 'GO':
                    go_terms.append(ref.get('id', ''))
            
            return UniProtResult(
                accession=accession,
                name=name,
                gene_names=gene_names,
                organism=organism,
                function=function,
                keywords=keywords,
                pathways=pathways,
                diseases=diseases,
                go_terms=go_terms
            )
            
        except Exception as e:
            logger.error(f"Error parsing UniProt response: {e}")
            return None
    
    # Ensembl API Methods
    async def get_gene_info(self, gene_id: str, species: str = "homo_sapiens") -> Optional[EnsemblResult]:
        """
        Get gene information from Ensembl
        """
        try:
            await self._rate_limit('ensembl')
            session = await self._get_session()
            
            url = f"https://rest.ensembl.org/lookup/id/{gene_id}"
            params = {'species': species}
            headers = {'Content-Type': 'application/json'}
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Ensembl request failed: {response.status}")
                    return None
                
                data = await response.json()
                return self._parse_ensembl_response(data)
                
        except Exception as e:
            logger.error(f"Error getting Ensembl info: {e}")
            return None
    
    def _parse_ensembl_response(self, data: Dict) -> EnsemblResult:
        """Parse Ensembl JSON response"""
        try:
            return EnsemblResult(
                gene_id=data.get('id', ''),
                gene_name=data.get('display_name', ''),
                chromosome=data.get('seq_region_name', ''),
                start=data.get('start', 0),
                end=data.get('end', 0),
                strand=data.get('strand', 0),
                biotype=data.get('biotype', ''),
                description=data.get('description', ''),
                synonyms=data.get('synonyms', [])
            )
            
        except Exception as e:
            logger.error(f"Error parsing Ensembl response: {e}")
            return None
    
    # STRING API Methods
    async def get_protein_interactions(self, protein_id: str, species: str = "9606") -> Optional[STRINGResult]:
        """
        Get protein-protein interactions from STRING database
        """
        try:
            await self._rate_limit('string')
            session = await self._get_session()
            
            url = "https://string-db.org/api/json/network"
            params = {
                'identifiers': protein_id,
                'species': species,
                'required_score': 400,
                'limit': 50
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"STRING request failed: {response.status}")
                    return None
                
                data = await response.json()
                return self._parse_string_response(data, protein_id)
                
        except Exception as e:
            logger.error(f"Error getting STRING interactions: {e}")
            return None
    
    def _parse_string_response(self, data: List[Dict], protein_id: str) -> STRINGResult:
        """Parse STRING JSON response"""
        try:
            interactions = []
            partners = set()
            total_score = 0
            
            for interaction in data:
                partner_a = interaction.get('preferredName_A', '')
                partner_b = interaction.get('preferredName_B', '')
                score = interaction.get('score', 0)
                
                # Determine the partner
                partner = partner_b if partner_a.upper() == protein_id.upper() else partner_a
                partners.add(partner)
                
                interactions.append({
                    'partner': partner,
                    'score': score,
                    'evidence': interaction.get('nscore', 0)
                })
                
                total_score += score
            
            avg_score = total_score / len(interactions) if interactions else 0
            
            return STRINGResult(
                protein_id=protein_id,
                interactions=interactions,
                network_score=avg_score,
                functional_partners=list(partners)
            )
            
        except Exception as e:
            logger.error(f"Error parsing STRING response: {e}")
            return None
    
    # KEGG API Methods
    async def get_pathway_info(self, pathway_id: str) -> Optional[KEGGResult]:
        """
        Get pathway information from KEGG
        """
        try:
            await self._rate_limit('kegg')
            session = await self._get_session()
            
            url = f"https://rest.kegg.jp/get/{pathway_id}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"KEGG request failed: {response.status}")
                    return None
                
                data = await response.text()
                return self._parse_kegg_response(data, pathway_id)
                
        except Exception as e:
            logger.error(f"Error getting KEGG pathway: {e}")
            return None
    
    def _parse_kegg_response(self, data: str, pathway_id: str) -> KEGGResult:
        """Parse KEGG text response"""
        try:
            lines = data.strip().split('\n')
            pathway_name = ""
            genes = []
            compounds = []
            description = ""
            category = ""
            
            current_section = None
            
            for line in lines:
                if line.startswith('NAME'):
                    pathway_name = line.replace('NAME', '').strip()
                elif line.startswith('DESCRIPTION'):
                    description = line.replace('DESCRIPTION', '').strip()
                elif line.startswith('CLASS'):
                    category = line.replace('CLASS', '').strip()
                elif line.startswith('GENE'):
                    current_section = 'genes'
                    gene_info = line.replace('GENE', '').strip()
                    if gene_info:
                        genes.append(gene_info.split()[0])
                elif line.startswith('COMPOUND'):
                    current_section = 'compounds'
                    compound_info = line.replace('COMPOUND', '').strip()
                    if compound_info:
                        compounds.append(compound_info.split()[0])
                elif current_section == 'genes' and line.startswith('            '):
                    gene_info = line.strip()
                    if gene_info:
                        genes.append(gene_info.split()[0])
                elif current_section == 'compounds' and line.startswith('            '):
                    compound_info = line.strip()
                    if compound_info:
                        compounds.append(compound_info.split()[0])
            
            return KEGGResult(
                pathway_id=pathway_id,
                pathway_name=pathway_name,
                genes=genes,
                compounds=compounds,
                description=description,
                category=category
            )
            
        except Exception as e:
            logger.error(f"Error parsing KEGG response: {e}")
            return None
    
    async def search_kegg_pathways(self, query: str) -> List[KEGGResult]:
        """
        Search KEGG pathways
        """
        try:
            await self._rate_limit('kegg')
            session = await self._get_session()
            
            url = f"https://rest.kegg.jp/find/pathway/{query}"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"KEGG search failed: {response.status}")
                    return []
                
                data = await response.text()
                pathway_ids = []
                
                for line in data.strip().split('\n'):
                    if line:
                        pathway_id = line.split('\t')[0]
                        pathway_ids.append(pathway_id)
                
                # Get details for each pathway
                results = []
                for pathway_id in pathway_ids[:10]:  # Limit to 10 results
                    pathway_info = await self.get_pathway_info(pathway_id)
                    if pathway_info:
                        results.append(pathway_info)
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching KEGG pathways: {e}")
            return []
    
    # Comprehensive analysis methods
    async def analyze_gene_list(self, gene_list: List[str]) -> Dict[str, Any]:
        """
        Comprehensive analysis of a gene list using multiple APIs
        """
        results = {
            'genes': [],
            'proteins': [],
            'pathways': [],
            'interactions': [],
            'literature': []
        }
        
        try:
            # Process each gene
            for gene in gene_list[:10]:  # Limit to 10 genes to avoid rate limits
                # Get gene info from Ensembl
                gene_info = await self.get_gene_info(gene)
                if gene_info:
                    results['genes'].append(gene_info)
                
                # Get protein info from UniProt
                protein_info = await self.get_protein_info(gene)
                if protein_info:
                    results['proteins'].append(protein_info)
                
                # Get protein interactions from STRING
                interactions = await self.get_protein_interactions(gene)
                if interactions:
                    results['interactions'].append(interactions)
                
                # Search related literature
                literature = await self.search_pubmed(f"{gene} AND cancer", max_results=5)
                results['literature'].extend(literature)
            
            # Search for relevant pathways
            pathway_query = " OR ".join(gene_list[:5])  # Use first 5 genes for pathway search
            pathways = await self.search_kegg_pathways(pathway_query)
            results['pathways'] = pathways
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive gene analysis: {e}")
            return results
    
    async def get_disease_genes(self, disease: str) -> List[str]:
        """
        Get genes associated with a disease from literature
        """
        try:
            papers = await self.search_pubmed(f"{disease} AND genes", max_results=50)
            
            # Extract genes from abstracts
            all_genes = set()
            gene_pattern = r'\b[A-Z][A-Z0-9]*[0-9]+[A-Z]*\b'
            
            for paper in papers:
                genes = re.findall(gene_pattern, paper.abstract)
                all_genes.update(genes)
            
            # Filter common genes (very basic filtering)
            common_genes = {
                'BRCA1', 'BRCA2', 'TP53', 'EGFR', 'KRAS', 'PIK3CA', 'APC', 'PTEN',
                'RB1', 'VHL', 'MLH1', 'MSH2', 'MSH6', 'PMS2', 'ATM', 'CHEK2'
            }
            
            disease_genes = list(all_genes & common_genes)
            return disease_genes[:20]  # Return top 20 genes
            
        except Exception as e:
            logger.error(f"Error getting disease genes: {e}")
            return []
    
    async def find_drug_targets(self, genes: List[str]) -> List[Dict[str, Any]]:
        """
        Find potential drug targets from gene list
        """
        targets = []
        
        # Known druggable genes and their drug classes
        druggable_genes = {
            'EGFR': {'class': 'Tyrosine kinase inhibitor', 'drugs': ['erlotinib', 'gefitinib']},
            'BRAF': {'class': 'BRAF inhibitor', 'drugs': ['vemurafenib', 'dabrafenib']},
            'PIK3CA': {'class': 'PI3K inhibitor', 'drugs': ['alpelisib', 'copanlisib']},
            'PTEN': {'class': 'PI3K/AKT pathway', 'drugs': ['capivasertib', 'ipatasertib']},
            'TP53': {'class': 'p53 activator', 'drugs': ['APR-246', 'nutlin-3']},
            'KRAS': {'class': 'RAS inhibitor', 'drugs': ['sotorasib', 'adagrasib']},
            'HER2': {'class': 'HER2 inhibitor', 'drugs': ['trastuzumab', 'pertuzumab']},
            'VEGF': {'class': 'Anti-angiogenic', 'drugs': ['bevacizumab', 'sunitinib']}
        }
        
        for gene in genes:
            if gene.upper() in druggable_genes:
                target_info = druggable_genes[gene.upper()]
                targets.append({
                    'gene': gene,
                    'therapeutic_class': target_info['class'],
                    'example_drugs': target_info['drugs'],
                    'evidence': 'Literature-based'
                })
        
        return targets

# Global instance
bio_apis_service = BioinformaticsAPIsService()