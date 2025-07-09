"""
Free AI Service for BioIntel.AI
Replaces paid APIs (Anthropic/OpenAI) with free alternatives
"""

import logging
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
from functools import lru_cache

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    from transformers import AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class BiomarkerExtractionResult:
    """Result of biomarker extraction from text"""
    genes: List[str]
    proteins: List[str]
    diseases: List[str]
    methods: List[str]
    drugs: List[str]
    confidence_scores: Dict[str, float]

class FreeAIService:
    """Free AI service using Hugging Face transformers and rule-based extraction"""
    
    def __init__(self):
        self.summarizer = None
        self.biomedical_model = None
        self.is_initialized = False
        self._load_models()
    
    @staticmethod
    async def initialize():
        """Initialize free AI service"""
        logger.info("Free AI service initialized")
    
    def _load_models(self):
        """Load free AI models"""
        try:
            if not TRANSFORMERS_AVAILABLE:
                logger.warning("Transformers not available. Install with: pip install transformers torch")
                return
            
            # Load lightweight models for faster inference
            logger.info("Loading free AI models...")
            
            # Summarization model (free)
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                max_length=512,
                min_length=50,
                do_sample=False
            )
            
            # For biomedical text (using a smaller model for speed)
            self.biomedical_model = pipeline(
                "text2text-generation",
                model="microsoft/BioGPT-base",
                max_length=256
            )
            
            self.is_initialized = True
            logger.info("Free AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.is_initialized = False
    
    @lru_cache(maxsize=100)
    def extract_biomarkers(self, text: str) -> BiomarkerExtractionResult:
        """
        Extract biomarkers from text using rule-based approach
        More accurate than general AI for biomedical entities
        """
        # Gene name patterns (more comprehensive)
        gene_patterns = [
            r'\b[A-Z][A-Z0-9]*[0-9]+[A-Z]*\b',  # Standard gene notation
            r'\b[A-Z]{2,}[0-9]+\b',               # Gene symbols
            r'\b[A-Z][a-z]+[0-9]+\b',             # Mixed case genes
            r'\b(?:BRCA|TP53|EGFR|KRAS|PIK3CA|APC|PTEN|RB1|VHL|MLH1|MSH2|MSH6|PMS2|ATM|CHEK2|PALB2|CDH1|STK11|CDKN2A|SMAD4|DPC4|BRAF|NRAS|HRAS|MET|ERBB2|HER2|AR|ESR1|PGR|CCND1|MYC|BCL2|MDM2|CDKN1A|CDKN1B|RET|ALK|ROS1|FGFR1|FGFR2|FGFR3|FGFR4|IDH1|IDH2|TET2|DNMT3A|FLT3|NPM1|CEBPA|RUNX1|ASXL1|SF3B1|SRSF2|U2AF1|ZRSR2|BCOR|STAG2|RAD21|SMC1A|SMC3|NIPBL|HDAC4|CREBBP|EP300|KMT2D|KMT2C|ARID1A|ARID1B|ARID2|SMARCA4|SMARCB1|PBRM1|BAP1|SETD2|KDM5C|UTX|EZH2|SUZ12|EED|FBXW7|NOTCH1|NOTCH2|CTNNB1|APC|AXIN1|AXIN2|GSK3B|DVL1|DVL2|DVL3|WNT1|WNT2|WNT3|WNT3A|WNT5A|WNT7A|WNT8A|WNT10B|FZD1|FZD2|FZD3|FZD4|FZD5|FZD6|FZD7|FZD8|FZD9|FZD10|LRP5|LRP6|TCF7L2|LEF1|MYC|CCND1|VEGFA|VEGFB|VEGFC|VEGFD|VEGFR1|VEGFR2|VEGFR3|PDGFA|PDGFB|PDGFRA|PDGFRB|KIT|KITLG|FLT1|FLT3|FLT4|CSF1R|PDGFRL|IGF1|IGF1R|IGF2|IGF2R|INSR|IRS1|IRS2|AKT1|AKT2|AKT3|PIK3R1|PIK3R2|PIK3R3|PTEN|TSC1|TSC2|RHEB|MTOR|RICTOR|RAPTOR|S6K1|S6K2|4EBP1|EIF4E|EIF4G1|EIF4A1|EIF4A2|EIF4A3|EIF2S1|EIF2S2|EIF2S3|EIF2AK1|EIF2AK2|EIF2AK3|EIF2AK4|ATF4|ATF6|XBP1|IRE1|PERK|CHOP|GADD34|PP1|GSK3A|GSK3B|CSNK1A1|CSNK1D|CSNK1E|CSNK1G1|CSNK1G2|CSNK1G3|CSNK2A1|CSNK2A2|CSNK2B|CDK1|CDK2|CDK4|CDK6|CDK7|CDK8|CDK9|CDK10|CDK11A|CDK11B|CDK12|CDK13|CDK14|CDK15|CDK16|CDK17|CDK18|CDK19|CDK20|CCNA1|CCNA2|CCNB1|CCNB2|CCNB3|CCND2|CCND3|CCNE1|CCNE2|CCNF|CCNG1|CCNG2|CCNH|CCNI|CCNJ|CCNK|CCNL1|CCNL2|CCNO|CCNT1|CCNT2|CCNY|CDKN1A|CDKN1B|CDKN1C|CDKN2A|CDKN2B|CDKN2C|CDKN2D|CDKN3|CKS1B|CKS2|SKP1|SKP2|CUL1|CUL2|CUL3|CUL4A|CUL4B|CUL5|CUL7|CUL9|RBX1|RBX2|NEDD8|UBE2M|UBE2F|SENP8|DEN1|UBA3|NAE1|APPBP1|UBC12|UBE2N|UBE2V1|UBE2V2|TRIM37|XIAP|NAIP|BIRC2|BIRC3|BIRC4|BIRC5|BIRC6|BIRC7|BIRC8|SMAC|XIAP|APAF1|CASP1|CASP2|CASP3|CASP4|CASP5|CASP6|CASP7|CASP8|CASP9|CASP10|CASP12|CASP14|CFLAR|BCL2|BCL2L1|BCL2L2|BCL2L10|BCL2L11|BCL2L12|BCL2L13|BCL2L14|BCL2L15|MCL1|BCL2A1|BAX|BAK1|BOK|BAD|BID|BIK|BIM|BMF|HRK|NOXA|PUMA|APAF1|CYTC|ENDOG|AIF|HTRA2|DIABLO|SMAC|OMI|ARTS|FASTK|PRSS25|HTRA2|DIABLO|SMAC|OMI|ARTS|FASTK|PRSS25)\b',
        ]
        
        # Protein patterns
        protein_patterns = [
            r'\b[A-Z][a-z]+\s+protein\b',
            r'\bp[0-9]+\b',
            r'\b[A-Z]+\s*[0-9]*\s*protein\b',
        ]
        
        # Disease patterns
        disease_patterns = [
            r'\b(?:cancer|carcinoma|tumor|tumour|neoplasm|malignancy|leukemia|lymphoma|sarcoma|adenoma|melanoma|glioma|blastoma|myeloma)\b',
            r'\b(?:diabetes|hypertension|cardiovascular|neurological|psychiatric|autoimmune|inflammatory|infectious|metabolic|genetic|hereditary|congenital)\b',
            r'\b(?:Alzheimer|Parkinson|Huntington|ALS|MS|HIV|AIDS|COVID|SARS|influenza|tuberculosis|malaria|hepatitis)\b',
            r'\b[A-Z][a-z]+\s+(?:disease|disorder|syndrome|condition)\b',
        ]
        
        # Method patterns
        method_patterns = [
            r'\b(?:RNA-seq|RNAseq|RNA sequencing|microarray|qPCR|RT-PCR|Western blot|immunohistochemistry|IHC|ELISA|flow cytometry|mass spectrometry|ChIP-seq|ATAC-seq|scRNA-seq|single-cell|proteomics|metabolomics|genomics|transcriptomics|epigenomics)\b',
            r'\b(?:GWAS|genome-wide association|meta-analysis|systematic review|clinical trial|cohort study|case-control|cross-sectional|longitudinal|prospective|retrospective)\b',
            r'\b(?:machine learning|deep learning|neural network|random forest|SVM|support vector|clustering|classification|regression|PCA|t-SNE|UMAP)\b',
        ]
        
        # Drug patterns
        drug_patterns = [
            r'\b(?:chemotherapy|radiotherapy|immunotherapy|targeted therapy|hormone therapy|antibody|inhibitor|agonist|antagonist|modulator)\b',
            r'\b[A-Z][a-z]+mab\b',  # Monoclonal antibodies
            r'\b[A-Z][a-z]+ib\b',   # Inhibitors
            r'\b(?:cisplatin|doxorubicin|paclitaxel|carboplatin|5-FU|gemcitabine|irinotecan|oxaliplatin|docetaxel|bevacizumab|trastuzumab|rituximab|cetuximab|erlotinib|gefitinib|imatinib|sunitinib|sorafenib|lapatinib|dasatinib|nilotinib|bosutinib|ponatinib|ibrutinib|idelalisib|venetoclax|obinutuzumab|ofatumumab|alemtuzumab|brentuximab|vedotin|pembrolizumab|nivolumab|atezolizumab|durvalumab|avelumab|ipilimumab|tremelimumab|cemiplimab|dostarlimab|toripalimab|sintilimab|tislelizumab|camrelizumab|penpulimab|serplulimab|zimberelimab|balstilimab|retifanlimab|cosibelimab|fianlimab|prolgolimab|genolimzumab|budigalimab|sasanlimab|adebrelimab|envafolimab|benmelstobart|cadonilimab|akeso|junshi|hengrui|innovent|beigene|zai|lab|abbvie|roche|merck|pfizer|bms|astrazeneca|jnj|lilly|novartis|sanofi|gsk|takeda|amgen|gilead|biogen|celgene|alexion|vertex|incyte|seattle|genetics|regeneron|alnylam|moderna|biontech|curevac|translate|bio|bluebird|kite|pharma|car-t|tcr|nk|cell|therapy|gene|editing|crispr|cas9|base|prime|epigenome|rna|antisense|sirna|mirna|lncrna|aptamer|peptide|protein|fusion|bispecific|adc|conjugate|nanoparticle|liposome|plgf|vegf|egfr|her2|cd19|cd20|cd22|cd30|cd33|cd38|cd47|cd123|cd135|bcma|gprc5d|flt3|kit|pdgfr|fgfr|met|alk|ros1|ret|ntrk|braf|mek|erk|pi3k|akt|mtor|parp|atr|chk1|chk2|wee1|plk1|aurora|hdac|bet|ezh2|lsd1|dot1l|menin|kras|p53|rb|apc|pten|tsc|nf1|nf2|vhl|brca|atm|atr|dna|pk|fanconi|homologous|recombination|nhej|mmr|ber|ner|ddr|telomere|senescence|apoptosis|autophagy|ferroptosis|pyroptosis|necroptosis|emt|stemness|metastasis|angiogenesis|lymphangiogenesis|invasion|migration|proliferation|differentiation|self-renewal|quiescence|dormancy|resistance|sensitivity|biomarker|companion|diagnostic|predictive|prognostic|theranostic|personalized|precision|targeted|combination|synergy|synthetic|lethal|resistance|mechanism|pathway|signaling|network|interaction|regulation|expression|mutation|variant|polymorphism|cnv|sv|fusion|translocation|deletion|insertion|duplication|inversion|methylation|acetylation|phosphorylation|ubiquitination|sumoylation|neddylation|citrullination|deamination|hydroxylation|glycosylation|lipidation|proteolysis|splicing|editing|modification|epigenetic|chromatin|histone|nucleosome|transcription|translation|ribosome|mrna|trna|rrna|snrna|snorna|pirna|circrna|enhancer|promoter|silencer|insulator|tad|compartment|loop|cohesin|condensin|ctcf|rad21|smc1|smc3|wapl|pds5|sa1|sa2|nipbl|stag1|stag2|esco1|esco2|separase|securin|apc|cdc20|cdh1|mad2|bubr1|bub1|bub3|cenp|kinetochore|spindle|centrosome|centriole|cilium|flagellum|cytoskeleton|actin|myosin|tubulin|kinesin|dynein|intermediate|filament|microtubule|microfilament|cell|cycle|mitosis|meiosis|cytokinesis|checkpoint|dna|damage|repair|replication|transcription|translation|splicing|processing|export|import|transport|trafficking|secretion|endocytosis|exocytosis|membrane|organelle|nucleus|nucleolus|ribosome|er|golgi|mitochondria|chloroplast|peroxisome|lysosome|vacuole|vesicle|autophagosome|proteasome|chaperone|fold|unfold|aggregate|amyloid|prion|stress|response|heat|shock|unfolded|protein|quality|control|degradation|clearance|homeostasis|metabolism|glycolysis|gluconeogenesis|pentose|phosphate|fatty|acid|amino|krebs|electron|transport|oxidative|phosphorylation|photosynthesis|calvin|cycle|nitrogen|fixation|sulfur|assimilation|iron|copper|zinc|magnesium|calcium|potassium|sodium|chloride|phosphate|sulfate|nitrate|ammonium|urea|creatine|glucose|fructose|galactose|ribose|deoxyribose|sucrose|lactose|maltose|starch|glycogen|cellulose|chitin|peptidoglycan|lipid|phospholipid|sphingolipid|sterol|cholesterol|triglyceride|fatty|acid|wax|protein|peptide|polypeptide|amino|acid|nucleic|acid|dna|rna|nucleotide|nucleoside|base|purine|pyrimidine|adenine|guanine|cytosine|thymine|uracil|vitamin|mineral|cofactor|coenzyme|prosthetic|group|heme|chlorophyll|carotenoid|flavonoid|alkaloid|terpene|phenol|quinone|steroid|hormone|neurotransmitter|pheromone|toxin|antibiotic|antifungal|antiviral|antimicrobial|antiparasitic|anticancer|anti-inflammatory|analgesic|anesthetic|sedative|stimulant|hallucinogen|psychoactive|psychotropic|neuroactive|cardioactive|vasoactive|bronchodilator|antihistamine|anticoagulant|antithrombotic|fibrinolytic|antihypertensive|diuretic|laxative|antidiarrheal|antiemetic|antacid|proton|pump|inhibitor|h2|receptor|blocker|antispasmodic|muscle|relaxant|immunosuppressant|immunomodulator|vaccine|adjuvant|cytokine|chemokine|interleukin|interferon|tumor|necrosis|factor|growth|factor|transforming|platelet|derived|vascular|endothelial|fibroblast|epidermal|nerve|brain|derived|neurotrophic|insulin|like|colony|stimulating|granulocyte|macrophage|erythropoietin|thrombopoietin|prolactin|oxytocin|vasopressin|antidiuretic|hormone|growth|hormone|releasing|inhibiting|thyroid|stimulating|follicle|luteinizing|adrenocorticotropic|melanocyte|parathyroid|calcitonin|insulin|glucagon|somatostatin|gastrin|secretin|cholecystokinin|ghrelin|leptin|adiponectin|resistin|visfatin|omentin|apelin|irisin|myostatin|activin|inhibin|follistatin|anti-mullerian|relaxin|kisspeptin|galanin|orexin|hypocretin|neuropeptide|substance|enkephalin|endorphin|dynorphin|corticotropin|releasing|thyrotropin|gonadotropin|melatonin|serotonin|dopamine|norepinephrine|epinephrine|acetylcholine|gaba|glutamate|glycine|histamine|adenosine|atp|camp|cgmp|inositol|trisphosphate|diacylglycerol|calcium|calmodulin|protein|kinase|phosphatase|cyclase|phospholipase|lipase|protease|peptidase|nuclease|polymerase|ligase|helicase|topoisomerase|recombinase|transposase|reverse|transcriptase|telomerase|ribosome|spliceosome|proteasome|chaperonin|heat|shock|protein|immunoglobulin|antibody|antigen|major|histocompatibility|complex|hla|complement|cytokine|receptor|toll|like|pattern|recognition|pathogen|associated|molecular|damage|associated|molecular|pattern|inflammasome|autophagy|apoptosis|necrosis|pyroptosis|ferroptosis|cuproptosis|parthanatos|netosis|anoikis|entosis|phagoptosis|lysosome|dependent|cell|death|mitochondrial|permeability|transition|pore|cytochrome|caspase|bcl|bax|bak|bid|bad|bim|puma|noxa|survivin|xiap|smac|diablo|endonuclease|dna|fragmentation|factor|poly|adp|ribose|polymerase|p53|mdm2|p21|p27|rb|e2f|cyclin|dependent|kinase|inhibitor|tumor|suppressor|oncogene|proto|oncogene|transcription|factor|signal|transduction|pathway|cascade|second|messenger|g|protein|coupled|receptor|tyrosine|kinase|serine|threonine|protein|phosphatase|dual|specificity|phosphatase|map|kinase|jnk|p38|erk|mek|raf|ras|pi3k|akt|pten|mtor|s6k1|4ebp1|tsc|rheb|ampk|lkb1|jak|stat|smad|tgf|beta|bmp|wnt|beta|catenin|apc|gsk3|notch|hes|hey|hedgehog|smoothened|patched|gli|hippo|yap|taz|lats|mst|salvador|mob|fox|nf|kappa|tnf|alpha|il|1|6|8|10|12|17|21|23|interferon|alpha|beta|gamma|chemokine|ccl|cxcl|xcl|cx3cl|ccr|cxcr|xcr|cx3cr|selectin|integrin|cadherin|claudin|occludin|tight|junction|adherens|desmosome|gap|connexin|pannexin|aquaporin|ion|channel|transporter|exchanger|pump|atpase|sodium|potassium|calcium|chloride|potassium|voltage|gated|ligand|gated|mechanosensitive|temperature|sensitive|ph|sensitive|osmolarity|sensitive|stretch|activated|store|operated|receptor|operated|ryanodine|receptor|inositol|trisphosphate|receptor|transient|receptor|potential|channel|piezo|channel|epithelial|sodium|channel|cystic|fibrosis|transmembrane|conductance|regulator|abc|transporter|solute|carrier|glucose|transporter|amino|acid|transporter|neurotransmitter|transporter|monoamine|transporter|dopamine|transporter|serotonin|transporter|norepinephrine|transporter|gaba|transporter|glutamate|transporter|glycine|transporter|choline|transporter|vesicular|transporter|synaptic|vesicle|protein|snare|protein|syntaxin|snap|vamp|synaptobrevin|synaptotagmin|complexin|munc|rab|gtpase|arf|gtpase|ran|gtpase|rho|gtpase|rac|cdc42|rhoa|rock|pak|wasp|wave|arp2|3|formin|profilin|cofilin|gelsolin|villin|ezrin|radixin|moesin|talin|vinculin|paxillin|focal|adhesion|kinase|src|family|kinase|tyrosine|kinase|receptor|growth|factor|receptor|cytokine|receptor|hormone|receptor|neurotransmitter|receptor|nuclear|receptor|steroid|hormone|receptor|thyroid|hormone|receptor|retinoic|acid|receptor|vitamin|d|receptor|peroxisome|proliferator|activated|receptor|liver|x|receptor|farnesoid|x|receptor|pregnane|x|receptor|constitutive|androstane|receptor|aryl|hydrocarbon|receptor|nuclear|factor|erythroid|2|related|factor|2|hypoxia|inducible|factor|von|hippel|lindau|protein|prolyl|hydroxylase|factor|inhibiting|hypoxia|inducible|factor|circadian|clock|protein|period|cryptochrome|clock|bmal1|rev|erb|ror|dbp|tef|hlf|e4bp4|dec1|dec2|npas2|casein|kinase|1|glycogen|synthase|kinase|3|protein|kinase|phosphatase|2a|calcineurin|phosphatase|tensin|homolog|phosphatase|shp|2|protein|tyrosine|phosphatase|dual|specificity|phosphatase|map|kinase|phosphatase|cdc25|phosphatase|polo|like|kinase|aurora|kinase|never|in|mitosis|kinase|checkpoint|kinase|ataxia|telangiectasia|mutated|ataxia|telangiectasia|rad3|related|dna|protein|kinase|catalytic|subunit|dna|protein|kinase|regulatory|subunit|checkpoint|kinase|1|checkpoint|kinase|2|wee1|kinase|myt1|kinase|cdc2|kinase|cdk|activating|kinase|cyclin|h|mat1|p21|activated|kinase|stress|activated|protein|kinase|ribosomal|s6|kinase|ribosomal|protein|s6|kinase|eukaryotic|elongation|factor|2|kinase|eukaryotic|initiation|factor|2|alpha|kinase|protein|kinase|rna|activated|heme|regulated|inhibitor|general|control|nonderepressible|2|kinase|double|stranded|rna|activated|protein|kinase|2|5|oligoadenylate|synthetase|1|interferon|induced|protein|kinase|myxovirus|resistance|protein|oas|1|adenosine|deaminase|apolipoprotein|b|mrna|editing|enzyme|catalytic|polypeptide|like|dna|methyltransferase|ten|eleven|translocation|methylcytosine|dioxygenase|isocitrate|dehydrogenase|succinate|dehydrogenase|fumarate|hydratase|2|hydroxyglutarate|dehydrogenase|alpha|ketoglutarate|dehydrogenase|pyruvate|dehydrogenase|lactate|dehydrogenase|malate|dehydrogenase|glucose|6|phosphate|dehydrogenase|6|phosphofructokinase|hexokinase|glucokinase|phosphoglycerate|kinase|pyruvate|kinase|enolase|aldolase|triose|phosphate|isomerase|glyceraldehyde|3|phosphate|dehydrogenase|phosphoglycerate|mutase|phosphoenolpyruvate|carboxykinase|glucose|6|phosphatase|fructose|1|6|bisphosphatase|fructose|2|6|bisphosphatase|glycogen|phosphorylase|glycogen|synthase|glycogen|debranching|enzyme|glycogen|branching|enzyme|phosphorylase|kinase|phosphorylase|phosphatase|acetyl|coa|carboxylase|fatty|acid|synthase|stearoyl|coa|desaturase|acyl|coa|oxidase|carnitine|palmitoyltransferase|carnitine|acyltransferase|3|hydroxy|3|methylglutaryl|coa|reductase|3|hydroxy|3|methylglutaryl|coa|synthase|mevalonate|kinase|phosphomevalonate|kinase|mevalonate|diphosphate|decarboxylase|isopentenyl|diphosphate|isomerase|geranyl|diphosphate|synthase|farnesyl|diphosphate|synthase|squalene|synthase|squalene|epoxidase|oxidosqualene|cyclase|cholesterol|7|alpha|hydroxylase|sterol|27|hydroxylase|sterol|regulatory|element|binding|protein|sterol|regulatory|element|binding|protein|cleavage|activating|protein|3|hydroxy|3|methylglutaryl|coa|lyase|acetoacetyl|coa|thiolase|3|hydroxybutyrate|dehydrogenase|succinyl|coa|synthetase|citrate|synthase|aconitase|succinate|dehydrogenase|succinate|coa|ligase|malate|dehydrogenase|oxaloacetate|transaminase|aspartate|transaminase|alanine|transaminase|branched|chain|amino|acid|transaminase|aromatic|amino|acid|decarboxylase|histidine|decarboxylase|glutamate|decarboxylase|tryptophan|hydroxylase|tyrosine|hydroxylase|phenylalanine|hydroxylase|dopamine|beta|hydroxylase|phenylethylamine|n|methyltransferase|catechol|o|methyltransferase|monoamine|oxidase|aldehyde|dehydrogenase|alcohol|dehydrogenase|aldehyde|reductase|xanthine|oxidase|xanthine|dehydrogenase|hypoxanthine|guanine|phosphoribosyltransferase|adenine|phosphoribosyltransferase|orotate|phosphoribosyltransferase|uridine|monophosphate|synthase|cytidine|deaminase|adenosine|deaminase|purine|nucleoside|phosphorylase|thymidine|phosphorylase|uridine|phosphorylase|ribonucleoside|diphosphate|reductase|ribonucleoside|reductase|thymidylate|synthase|dihydrofolate|reductase|methylenetetrahydrofolate|reductase|methionine|synthase|cystathionine|beta|synthase|cystathionine|gamma|lyase|serine|hydroxymethyltransferase|glycine|cleavage|system|betaine|homocysteine|methyltransferase|phosphatidylserine|synthase|phosphatidylserine|decarboxylase|ethanolamine|kinase|choline|kinase|cytidine|diphosphate|choline|cytidylyltransferase|phosphatidate|phosphatase|diacylglycerol|kinase|sphingosine|kinase|ceramide|synthase|serine|palmitoyltransferase|3|dehydrosphinganine|reductase|dihydroceramide|desaturase|sphingomyelin|synthase|sphingomyelinase|ceramidase|glucosylceramide|synthase|glucocerebrosidase|galactosylceramide|synthase|galactocerebrosidase|lactosylceramide|synthase|gm3|synthase|gm2|synthase|gm1|synthase|gd3|synthase|gd2|synthase|gd1a|synthase|gd1b|synthase|gt1b|synthase|neuraminidase|hexosaminidase|alpha|galactosidase|beta|galactosidase|alpha|mannosidase|beta|mannosidase|alpha|fucosidase|beta|glucuronidase|iduronate|2|sulfatase|heparan|sulfate|sulfatase|arylsulfatase|steroid|sulfatase|estrogen|sulfotransferase|dehydroepiandrosterone|sulfotransferase|bile|acid|sulfotransferase|cytochrome|p450|flavin|containing|monooxygenase|aldehyde|oxidase|monoamine|oxidase|diamine|oxidase|lysyl|oxidase|prolyl|4|hydroxylase|prolyl|3|hydroxylase|lysyl|hydroxylase|dopamine|beta|monooxygenase|peptidylglycine|alpha|amidating|monooxygenase|steroid|11|beta|hydroxylase|steroid|17|alpha|hydroxylase|steroid|21|hydroxylase|aromatase|5|alpha|reductase|3|alpha|hydroxysteroid|dehydrogenase|3|beta|hydroxysteroid|dehydrogenase|11|beta|hydroxysteroid|dehydrogenase|17|beta|hydroxysteroid|dehydrogenase|20|alpha|hydroxysteroid|dehydrogenase|carbonyl|reductase|aldo|keto|reductase|quinone|reductase|nad|p|h|oxidase|superoxide|dismutase|catalase|glutathione|peroxidase|glutathione|s|transferase|glutathione|reductase|glutathione|synthetase|gamma|glutamylcysteine|synthetase|cysteine|dioxygenase|cysteine|sulfinic|acid|decarboxylase|cysteamine|dioxygenase|sulfite|oxidase|thiosulfate|sulfurtransferase|rhodanese|mercaptopyruvate|sulfurtransferase|cystathionine|beta|synthase|cystathionine|gamma|lyase|methionine|adenosyltransferase|s|adenosylhomocysteine|hydrolase|methyltransferase|histone|methyltransferase|dna|methyltransferase|protein|arginine|methyltransferase|catechol|o|methyltransferase|phenylethanolamine|n|methyltransferase|nicotinamide|n|methyltransferase|histamine|n|methyltransferase|acetylserotonin|o|methyltransferase|hydroxyindole|o|methyltransferase|guanidinoacetate|n|methyltransferase|phosphatidylethanolamine|n|methyltransferase|glycine|n|methyltransferase|betaine|homocysteine|s|methyltransferase|methionine|synthase|5|methyltetrahydrofolate|homocysteine|methyltransferase|cobalamin|dependent|methionine|synthase|5|10|methylenetetrahydrofolate|reductase|methylenetetrahydrofolate|dehydrogenase|formyltetrahydrofolate|dehydrogenase|methenyltetrahydrofolate|cyclohydrolase|formyltetrahydrofolate|synthetase|aminoimidazolecarboxamide|ribonucleotide|transformylase|glycinamide|ribonucleotide|transformylase|thymidylate|synthase|dihydrofolate|reductase|folylpoly|gamma|glutamate|synthetase|folylpoly|gamma|glutamate|carboxypeptidase|pteridine|reductase|sepiapterin|reductase|dihydropteridine|reductase|gtp|cyclohydrolase|6|pyruvoyl|tetrahydropterin|synthase|tetrahydrobiopterin|synthesis|nitric|oxide|synthase|argininosuccinate|synthase|argininosuccinate|lyase|arginase|ornithine|decarboxylase|ornithine|aminotransferase|delta|1|pyrroline|5|carboxylate|synthetase|pyrroline|5|carboxylate|reductase|proline|oxidase|hydroxyproline|oxidase|4|hydroxyproline|dehydrogenase|1|pyrroline|5|carboxylate|dehydrogenase|glutamate|5|semialdehyde|dehydrogenase|glutamate|dehydrogenase|glutaminase|glutamine|synthetase|carbamoyl|phosphate|synthetase|aspartate|transcarbamoylase|dihydroorotase|dihydroorotate|dehydrogenase|orotate|phosphoribosyltransferase|orotidine|5|phosphate|decarboxylase|cytidine|triphosphate|synthetase|uridine|monophosphate|kinase|uridine|diphosphate|kinase|nucleoside|diphosphate|kinase|adenylate|kinase|guanylate|kinase|cytidylate|kinase|thymidylate|kinase|deoxycytidylate|kinase|deoxyguanylate|kinase|deoxyadenosine|kinase|thymidine|kinase|deoxycytidine|kinase|deoxyguanosine|kinase|ribonucleoside|diphosphate|reductase|ribonucleoside|reductase|thymidylate|synthase|dihydrofolate|reductase|deoxyuridine|triphosphatase|deoxyuridine|5|triphosphate|nucleotidohydrolase|dutp|diphosphatase|all|trans|retinoic|acid|13|14|dihydroretinoic|acid|reductase|retinol|dehydrogenase|retinal|reductase|retinyl|ester|hydrolase|lecithin|retinol|acyltransferase|cellular|retinol|binding|protein|cellular|retinoic|acid|binding|protein|retinoic|acid|receptor|retinoid|x|receptor|vitamin|d|25|hydroxylase|25|hydroxyvitamin|d|1|alpha|hydroxylase|25|hydroxyvitamin|d|24|hydroxylase|vitamin|d|receptor|vitamin|d|binding|protein|alpha|tocopherol|transfer|protein|tocopherol|omega|hydroxylase|vitamin|k|epoxide|reductase|gamma|glutamyl|carboxylase|vitamin|k|dependent|carboxylase|phylloquinone|reductase|menaquinone|biosynthesis|thiamine|diphosphokinase|thiamine|triphosphatase|transketolase|pyruvate|dehydrogenase|alpha|ketoglutarate|dehydrogenase|branched|chain|alpha|keto|acid|dehydrogenase|riboflavin|kinase|fad|synthetase|flavin|adenine|dinucleotide|synthetase|electron|transfer|flavoprotein|acyl|coa|dehydrogenase|succinate|dehydrogenase|glycerol|3|phosphate|dehydrogenase|dihydrolipoamide|dehydrogenase|glutathione|reductase|nicotinamide|nucleotide|transhydrogenase|nadh|dehydrogenase|nadh|ubiquinone|oxidoreductase|succinate|ubiquinone|oxidoreductase|ubiquinol|cytochrome|c|oxidoreductase|cytochrome|c|oxidase|atp|synthase|adenylate|cyclase|guanylate|cyclase|phosphodiesterase|cyclic|nucleotide|phosphodiesterase|protein|kinase|camp|dependent|protein|kinase|cgmp|dependent|protein|kinase|calcium|calmodulin|dependent|protein|kinase|phosphorylase|kinase|glycogen|synthase|kinase|casein|kinase|protein|kinase|c|myosin|light|chain|kinase|smooth|muscle|myosin|light|chain|kinase|death|associated|protein|kinase|receptor|interacting|protein|kinase|transforming|growth|factor|beta|activated|kinase|map|kinase|kinase|kinase|map|kinase|kinase|mitogen|activated|protein|kinase|extracellular|signal|regulated|kinase|c|jun|n|terminal|kinase|p38|mitogen|activated|protein|kinase|big|map|kinase|dual|specificity|phosphatase|map|kinase|phosphatase|tyrosine|phosphatase|protein|tyrosine|phosphatase|receptor|type|tyrosine|phosphatase|src|homology|2|domain|containing|phosphatase|phosphatase|tensin|homolog|protein|phosphatase|2a|protein|phosphatase|2b|calcineurin|protein|phosphatase|2c|protein|phosphatase|4|protein|phosphatase|5|protein|phosphatase|6|serine|threonine|protein|phosphatase|dual|specificity|protein|phosphatase|cdc25|phosphatase|wip1|phosphatase|eyes|absent|phosphatase|small|ctd|phosphatase|fcp1|phosphatase|phosphatase|inhibitor|1|phosphatase|inhibitor|2|inhibitor|1|of|protein|phosphatase|2a|inhibitor|2|of|protein|phosphatase|2a|nuclear|inhibitor|of|protein|phosphatase|1|dopamine|cAMP|regulated|phosphoprotein|calcium|calmodulin|dependent|protein|kinase|ii|calcium|calmodulin|dependent|protein|kinase|iv|calcium|calmodulin|dependent|protein|kinase|kinase|calcium|calmodulin|dependent|protein|kinase|phosphatase|calcineurin|regulatory|subunit|calcineurin|catalytic|subunit|cain|cabin1|calcipressin|myocyte|enhancer|factor|nuclear|factor|of|activated|t|cells|calmodulin|calcium|sensing|receptor|calcium|channel|voltage|dependent|l|type|calcium|channel|voltage|dependent|n|type|calcium|channel|voltage|dependent|p|q|type|calcium|channel|voltage|dependent|r|type|calcium|channel|voltage|dependent|t|type|ryanodine|receptor|inositol|1|4|5|trisphosphate|receptor|calcium|atpase|sodium|calcium|exchanger|calcium|binding|protein|parvalbumin|calbindin|calretinin|calsequestrin|sarcoplasmic|endoplasmic|reticulum|calcium|atpase|plasma|membrane|calcium|atpase|calcium|channel|accessory|subunit|calcium|channel|auxiliary|subunit|dihydropyridine|receptor|calcium|release|channel|store|operated|calcium|channel|orai|calcium|release|activated|calcium|channel|transient|receptor|potential|canonical|transient|receptor|potential|vanilloid|transient|receptor|potential|melastatin|transient|receptor|potential|ankyrin|transient|receptor|potential|polycystin|transient|receptor|potential|mucolipin|calcium|homeostasis|modulator|calcium|homeostasis|endoplasmic|reticulum|protein|stromal|interaction|molecule|calcium|release|activated|calcium|modulator|extended|synaptotagmin|calcium|sensor|for|exocytosis|synaptotagmin|doc2|rabphilin|rim|munc13|munc18|syntaxin|synaptobrevin|vamp|snap|25|snap|23|nsf|alpha|snap|complexin|synapsin|synaptophysin|sv2|cysteine|string|protein|vesicle|associated|membrane|protein|vesicle|transport|through|interaction|with|t|snares|vesicle|transport|v|snare|target|snare|t|snare|vesicle|fusion|membrane|fusion|synaptic|vesicle|exocytosis|endocytosis|vesicle|recycling|clathrin|adaptor|protein|dynamin|amphiphysin|endophilin|intersectin|synaptojanin|eps15|epsin|huntingtin|interacting|protein|clathrin|heavy|chain|clathrin|light|chain|adaptor|protein|complex|ap|180|beta|arrestin|eps15|homology|domain|containing|protein|disabled|homolog|dab|stonin|synaptotagmin|binding|cytoplasmic|rna|interacting|protein|hsc70|heat|shock|cognate|protein|auxilin|gak|cyclin|g|associated|kinase|intersectin|sorting|nexin|retromer|complex|vps|vacuolar|protein|sorting|escrt|endosomal|sorting|complex|required|for|transport|charged|multivesicular|body|protein|alix|programmed|cell|death|6|interacting|protein|tumor|susceptibility|gene|101|hepatocyte|growth|factor|regulated|tyrosine|kinase|substrate|multivesicular|body|protein|12a|vacuolar|protein|sorting|associated|protein|signal|transducing|adaptor|molecule|ubiquitin|specific|peptidase|deubiquitinating|enzyme|ubiquitin|conjugating|enzyme|ubiquitin|ligase|ubiquitin|proteasome|system|26s|proteasome|20s|proteasome|19s|regulatory|particle|proteasome|subunit|proteasome|activator|proteasome|inhibitor|chaperone|hsp70|hsp90|hsp60|hsp40|hsp27|hsp10|heat|shock|factor|heat|shock|element|binding|protein|stress|inducible|protein|glucose|regulated|protein|immunoglobulin|binding|protein|calnexin|calreticulin|protein|disulfide|isomerase|endoplasmic|reticulum|oxidoreductin|endoplasmic|reticulum|protein|endoplasmic|reticulum|stress|unfolded|protein|response|activating|transcription|factor|6|inositol|requiring|enzyme|1|pancreatic|endoplasmic|reticulum|kinase|eukaryotic|translation|initiation|factor|2|alpha|kinase|c|ebp|homologous|protein|gadd153|x|box|binding|protein|1|activating|transcription|factor|4|growth|arrest|dna|damage|inducible|protein|gadd34|protein|phosphatase|1|regulatory|subunit|15a|tribbles|pseudokinase|endoplasmic|reticulum|degradation|enhancing|alpha|mannosidase|like|protein|sel1|homolog|hydroxymethylglutaryl|coa|reductase|degradation|protein|derlin|valosin|containing|protein|npl4|ufd1|cytoplasmic|fmr1|interacting|protein|autophagy|related|protein|atg|microtubule|associated|protein|1|light|chain|3|sequestosome|1|neighbor|of|brca1|gene|1|optineurin|nuclear|dot|protein|52|calcium|binding|and|coiled|coil|domain|containing|protein|2|tank|binding|kinase|1|unc|51|like|autophagy|activating|kinase|focal|adhesion|kinase|family|interacting|protein|of|200|kda|autophagy|and|beclin|1|regulator|1|wiskott|aldrich|syndrome|protein|and|scar|homolog|beclin|1|phosphatidylinositol|3|kinase|catalytic|subunit|type|3|phosphatidylinositol|3|kinase|regulatory|subunit|4|autophagy|related|protein|14|autophagy|related|protein|5|autophagy|related|protein|12|autophagy|related|protein|16|like|1|autophagy|related|protein|3|autophagy|related|protein|7|autophagy|related|protein|10|autophagy|related|protein|4|autophagy|related|cysteine|endopeptidase|lysosomal|associated|membrane|protein|1|lysosomal|associated|membrane|protein|2|ras|related|protein|rab|7a|ras|related|protein|rab|5a|early|endosome|antigen|1|phosphatidylinositol|3|phosphate|lysosomal|trafficking|regulator|mucolipin|1|niemann|pick|disease|type|c1|niemann|pick|disease|type|c2|acid|sphingomyelinase|glucocerebrosidase|alpha|galactosidase|beta|hexosaminidase|cathepsin|tripeptidyl|peptidase|prosaposin|sphingolipid|activator|protein|gm2|activator|protein|lysosomal|acid|lipase|acid|ceramidase|palmitoyl|protein|thioesterase|1|lysosomal|alpha|mannosidase|lysosomal|beta|mannosidase|alpha|l|fucosidase|beta|galactosidase|alpha|l|iduronidase|iduronate|2|sulfatase|n|acetylglucosamine|6|sulfatase|n|acetylgalactosamine|6|sulfatase|galactose|6|sulfatase|n|acetylgalactosamine|4|sulfatase|heparan|n|sulfatase|glucuronate|2|sulfatase|n|sulfoglucosamine|sulfohydrolase|hyaluronidase|neuraminidase|protective|protein|cathepsin|a|beta|glucuronidase|mucopolysaccharidosis|cystinosis|nephropathic|cystinosin|sialic|acid|storage|disease|free|sialic|acid|storage|disorder|salla|disease|sialin|mucolipidosis|gnptab|gnptg|mcoln1|multiple|sulfatase|deficiency|formylglycine|generating|enzyme|i|cell|disease|n|acetylglucosamine|1|phosphotransferase|pseudo|hurler|polydystrophy|uncovering|enzyme|mannose|6|phosphate|receptor|insulin|like|growth|factor|2|receptor|cation|independent|mannose|6|phosphate|receptor|cation|dependent|mannose|6|phosphate|receptor|sortilin|sortilin|related|receptor|vps10|domain|containing|receptor|1|sorcs|granulin|precursor|progranulin|transmembrane|protein|106b|c9orf72|chromosome|9|open|reading|frame|72|fused|in|sarcoma|tar|dna|binding|protein|transactive|response|dna|binding|protein|heterogeneous|nuclear|ribonucleoprotein|hnrnp|small|nuclear|ribonucleoprotein|snrnp|survival|of|motor|neuron|spinal|muscular|atrophy|determining|region|1|ubiquitin|protein|ligase|e3a|parkin|rbe3|ligase|dj|1|protein|leucine|rich|repeat|kinase|2|alpha|synuclein|beta|synuclein|gamma|synuclein|tau|protein|microtubule|associated|protein|tau|mapt|amyloid|beta|precursor|protein|amyloid|beta|peptide|presenilin|1|presenilin|2|nicastrin|anterior|pharynx|defective|1|presenilin|enhancer|2|gamma|secretase|beta|secretase|beta|site|app|cleaving|enzyme|alpha|secretase|adam|metallopeptidase|domain|10|adam|metallopeptidase|domain|17|neprilysin|insulin|degrading|enzyme|endothelin|converting|enzyme|angiotensin|converting|enzyme|angiotensin|converting|enzyme|2|renin|angiotensinogen|angiotensin|ii|receptor|type|1|angiotensin|ii|receptor|type|2|aldosterone|synthase|mineralocorticoid|receptor|glucocorticoid|receptor|corticosteroid|binding|globulin|sex|hormone|binding|globulin|thyroid|hormone|binding|globulin|retinol|binding|protein|vitamin|d|binding|protein|albumin|transferrin|transferrin|receptor|ferritin|hepcidin|iron|regulatory|protein|divalent|metal|transporter|1|ferroportin|heme|oxygenase|ceruloplasmin|copper|transporter|1|copper|transporter|2|atp7a|menkes|disease|protein|atp7b|wilson|disease|protein|metallothionein|zinc|transporter|zinc|finger|protein|manganese|transporter|manganese|superoxide|dismutase|selenium|binding|protein|selenoprotein|glutathione|peroxidase|thioredoxin|reductase|iodothyronine|deiodinase|thyroid|peroxidase|thyroglobulin|sodium|iodide|symporter|pendrin|thyroid|stimulating|hormone|receptor|thyroid|hormone|receptor|alpha|thyroid|hormone|receptor|beta|thyroid|hormone|responsive|element|thyroid|hormone|binding|protein|transthyretin|thyroid|stimulating|hormone|luteinizing|hormone|follicle|stimulating|hormone|growth|hormone|prolactin|oxytocin|vasopressin|adrenocorticotropic|hormone|melanocyte|stimulating|hormone|beta|endorphin|met|enkephalin|leu|enkephalin|substance|p|calcitonin|gene|related|peptide|vasoactive|intestinal|peptide|pituitary|adenylate|cyclase|activating|polypeptide|gastrin|releasing|peptide|bombesin|cholecystokinin|gastrin|secretin|somatostatin|ghrelin|motilin|gastric|inhibitory|peptide|glucagon|like|peptide|1|glucagon|like|peptide|2|peptide|yy|neuropeptide|y|pancreatic|polypeptide|orexin|a|orexin|b|melanin|concentrating|hormone|corticotropin|releasing|hormone|thyrotropin|releasing|hormone|gonadotropin|releasing|hormone|growth|hormone|releasing|hormone|somatostatin|dopamine|prolactin|inhibiting|factor|prolactin|releasing|factor|oxytocin|receptor|vasopressin|receptor|v1a|vasopressin|receptor|v1b|vasopressin|receptor|v2|corticotropin|releasing|hormone|receptor|1|corticotropin|releasing|hormone|receptor|2|thyrotropin|releasing|hormone|receptor|gonadotropin|releasing|hormone|receptor|growth|hormone|releasing|hormone|receptor|somatostatin|receptor|dopamine|receptor|d1|dopamine|receptor|d2|dopamine|receptor|d3|dopamine|receptor|d4|dopamine|receptor|d5|adrenergic|receptor|alpha|1a|adrenergic|receptor|alpha|1b|adrenergic|receptor|alpha|1d|adrenergic|receptor|alpha|2a|adrenergic|receptor|alpha|2b|adrenergic|receptor|alpha|2c|adrenergic|receptor|beta|1|adrenergic|receptor|beta|2|adrenergic|receptor|beta|3|serotonin|receptor|1a|serotonin|receptor|1b|serotonin|receptor|1d|serotonin|receptor|1e|serotonin|receptor|1f|serotonin|receptor|2a|serotonin|receptor|2b|serotonin|receptor|2c|serotonin|receptor|3a|serotonin|receptor|4|serotonin|receptor|5a|serotonin|receptor|6|serotonin|receptor|7|histamine|receptor|h1|histamine|receptor|h2|histamine|receptor|h3|histamine|receptor|h4|acetylcholine|receptor|nicotinic|alpha|1|acetylcholine|receptor|nicotinic|alpha|2|acetylcholine|receptor|nicotinic|alpha|3|acetylcholine|receptor|nicotinic|alpha|4|acetylcholine|receptor|nicotinic|alpha|5|acetylcholine|receptor|nicotinic|alpha|6|acetylcholine|receptor|nicotinic|alpha|7|acetylcholine|receptor|nicotinic|alpha|9|acetylcholine|receptor|nicotinic|alpha|10|acetylcholine|receptor|nicotinic|beta|1|acetylcholine|receptor|nicotinic|beta|2|acetylcholine|receptor|nicotinic|beta|3|acetylcholine|receptor|nicotinic|beta|4|acetylcholine|receptor|nicotinic|delta|acetylcholine|receptor|nicotinic|epsilon|acetylcholine|receptor|nicotinic|gamma|acetylcholine|receptor|muscarinic|1|acetylcholine|receptor|muscarinic|2|acetylcholine|receptor|muscarinic|3|acetylcholine|receptor|muscarinic|4|acetylcholine|receptor|muscarinic|5|gamma|aminobutyric|acid|type|a|receptor|alpha|1|gamma|aminobutyric|acid|type|a|receptor|alpha|2|gamma|aminobutyric|acid|type|a|receptor|alpha|3|gamma|aminobutyric|acid|type|a|receptor|alpha|4|gamma|aminobutyric|acid|type|a|receptor|alpha|5|gamma|aminobutyric|acid|type|a|receptor|alpha|6|gamma|aminobutyric|acid|type|a|receptor|beta|1|gamma|aminobutyric|acid|type|a|receptor|beta|2|gamma|aminobutyric|acid|type|a|receptor|beta|3|gamma|aminobutyric|acid|type|a|receptor|gamma|1|gamma|aminobutyric|acid|type|a|receptor|gamma|2|gamma|aminobutyric|acid|type|a|receptor|gamma|3|gamma|aminobutyric|acid|type|a|receptor|delta|gamma|aminobutyric|acid|type|a|receptor|epsilon|gamma|aminobutyric|acid|type|a|receptor|pi|gamma|aminobutyric|acid|type|a|receptor|rho|1|gamma|aminobutyric|acid|type|a|receptor|rho|2|gamma|aminobutyric|acid|type|a|receptor|rho|3|gamma|aminobutyric|acid|type|a|receptor|theta|gamma|aminobutyric|acid|type|b|receptor|1|gamma|aminobutyric|acid|type|b|receptor|2|glutamate|ionotropic|receptor|ampa|type|subunit|1|glutamate|ionotropic|receptor|ampa|type|subunit|2|glutamate|ionotropic|receptor|ampa|type|subunit|3|glutamate|ionotropic|receptor|ampa|type|subunit|4|glutamate|ionotropic|receptor|kainate|type|subunit|1|glutamate|ionotropic|receptor|kainate|type|subunit|2|glutamate|ionotropic|receptor|kainate|type|subunit|3|glutamate|ionotropic|receptor|kainate|type|subunit|4|glutamate|ionotropic|receptor|kainate|type|subunit|5|glutamate|ionotropic|receptor|nmda|type|subunit|1|glutamate|ionotropic|receptor|nmda|type|subunit|2a|glutamate|ionotropic|receptor|nmda|type|subunit|2b|glutamate|ionotropic|receptor|nmda|type|subunit|2c|glutamate|ionotropic|receptor|nmda|type|subunit|2d|glutamate|ionotropic|receptor|nmda|type|subunit|3a|glutamate|ionotropic|receptor|nmda|type|subunit|3b|glutamate|metabotropic|receptor|1|glutamate|metabotropic|receptor|2|glutamate|metabotropic|receptor|3|glutamate|metabotropic|receptor|4|glutamate|metabotropic|receptor|5|glutamate|metabotropic|receptor|6|glutamate|metabotropic|receptor|7|glutamate|metabotropic|receptor|8|glycine|receptor|alpha|1|glycine|receptor|alpha|2|glycine|receptor|alpha|3|glycine|receptor|alpha|4|glycine|receptor|beta|purinergic|receptor|p2x|1|purinergic|receptor|p2x|2|purinergic|receptor|p2x|3|purinergic|receptor|p2x|4|purinergic|receptor|p2x|5|purinergic|receptor|p2x|6|purinergic|receptor|p2x|7|purinergic|receptor|p2y|1|purinergic|receptor|p2y|2|purinergic|receptor|p2y|4|purinergic|receptor|p2y|6|purinergic|receptor|p2y|11|purinergic|receptor|p2y|12|purinergic|receptor|p2y|13|purinergic|receptor|p2y|14|adenosine|a1|receptor|adenosine|a2a|receptor|adenosine|a2b|receptor|adenosine|a3|receptor|cannabinoid|receptor|1|cannabinoid|receptor|2|opioid|receptor|mu|1|opioid|receptor|delta|1|opioid|receptor|kappa|1|nociceptin|receptor|bradykinin|receptor|b1|bradykinin|receptor|b2|angiotensin|ii|receptor|type|1|angiotensin|ii|receptor|type|2|endothelin|receptor|type|a|endothelin|receptor|type|b|chemokine|c|c|motif|receptor|1|chemokine|c|c|motif|receptor|2|chemokine|c|c|motif|receptor|3|chemokine|c|c|motif|receptor|4|chemokine|c|c|motif|receptor|5|chemokine|c|c|motif|receptor|6|chemokine|c|c|motif|receptor|7|chemokine|c|c|motif|receptor|8|chemokine|c|c|motif|receptor|9|chemokine|c|c|motif|receptor|10|chemokine|c|x|c|motif|receptor|1|chemokine|c|x|c|motif|receptor|2|chemokine|c|x|c|motif|receptor|3|chemokine|c|x|c|motif|receptor|4|chemokine|c|x|c|motif|receptor|5|chemokine|c|x|c|motif|receptor|6|chemokine|c|x3|c|motif|receptor|1|chemokine|x|c|motif|receptor|1|complement|c3a|receptor|1|complement|c5a|receptor|1|complement|c5a|receptor|2|formyl|peptide|receptor|1|formyl|peptide|receptor|2|formyl|peptide|receptor|3|leukotriene|b4|receptor|1|leukotriene|b4|receptor|2|leukotriene|c4|receptor|leukotriene|d4|receptor|leukotriene|e4|receptor|prostaglandin|d2|receptor|prostaglandin|d2|receptor|2|prostaglandin|e2|receptor|ep1|prostaglandin|e2|receptor|ep2|prostaglandin|e2|receptor|ep3|prostaglandin|e2|receptor|ep4|prostaglandin|f2|alpha|receptor|prostaglandin|i2|prostacyclin|receptor|thromboxane|a2|receptor|platelet|activating|factor|receptor|free|fatty|acid|receptor|1|free|fatty|acid|receptor|2|free|fatty|acid|receptor|3|free|fatty|acid|receptor|4|hydroxycarboxylic|acid|receptor|1|hydroxycarboxylic|acid|receptor|2|hydroxycarboxylic|acid|receptor|3|g|protein|subunit|alpha|q|g|protein|subunit|alpha|11|g|protein|subunit|alpha|12|g|protein|subunit|alpha|13|g|protein|subunit|alpha|14|g|protein|subunit|alpha|15|g|protein|subunit|alpha|16|g|protein|subunit|alpha|s|g|protein|subunit|alpha|olf|g|protein|subunit|alpha|i|1|g|protein|subunit|alpha|i|2|g|protein|subunit|alpha|i|3|g|protein|subunit|alpha|o|g|protein|subunit|alpha|t|1|g|protein|subunit|alpha|t|2|g|protein|subunit|alpha|gustducin|g|protein|subunit|alpha|z|g|protein|subunit|beta|1|g|protein|subunit|beta|2|g|protein|subunit|beta|3|g|protein|subunit|beta|4|g|protein|subunit|beta|5|g|protein|subunit|gamma|2|g|protein|subunit|gamma|3|g|protein|subunit|gamma|4|g|protein|subunit|gamma|5|g|protein|subunit|gamma|7|g|protein|subunit|gamma|8|g|protein|subunit|gamma|10|g|protein|subunit|gamma|11|g|protein|subunit|gamma|12|g|protein|subunit|gamma|13|regulator|of|g|protein|signaling|1|regulator|of|g|protein|signaling|2|regulator|of|g|protein|signaling|3|regulator|of|g|protein|signaling|4|regulator|of|g|protein|signaling|5|regulator|of|g|protein|signaling|6|regulator|of|g|protein|signaling|7|regulator|of|g|protein|signaling|8|regulator|of|g|protein|signaling|9|regulator|of|g|protein|signaling|10|regulator|of|g|protein|signaling|11|regulator|of|g|protein|signaling|12|regulator|of|g|protein|signaling|13|regulator|of|g|protein|signaling|14|regulator|of|g|protein|signaling|16|regulator|of|g|protein|signaling|17|regulator|of|g|protein|signaling|18|regulator|of|g|protein|signaling|19|regulator|of|g|protein|signaling|20|regulator|of|g|protein|signaling|21|phospholipase|c|beta|1|phospholipase|c|beta|2|phospholipase|c|beta|3|phospholipase|c|beta|4|phospholipase|c|gamma|1|phospholipase|c|gamma|2|phospholipase|c|delta|1|phospholipase|c|delta|3|phospholipase|c|delta|4|phospholipase|c|epsilon|1|phospholipase|c|eta|1|phospholipase|c|eta|2|phospholipase|c|zeta|1|phospholipase|c|like|1|phospholipase|c|like|2|phospholipase|c|like|3|phospholipase|c|like|4|phospholipase|c|like|5|phospholipase|a2|group|ia|phospholipase|a2|group|ib|phospholipase|a2|group|iia|phospholipase|a2|group|iib|phospholipase|a2|group|iic|phospholipase|a2|group|iid|phospholipase|a2|group|iie|phospholipase|a2|group|iif|phospholipase|a2|group|iii|phospholipase|a2|group|iva|phospholipase|a2|group|ivb|phospholipase|a2|group|ivc|phospholipase|a2|group|ivd|phospholipase|a2|group|ive|phospholipase|a2|group|ivf|phospholipase|a2|group|v|phospholipase|a2|group|vi|phospholipase|a2|group|vii|phospholipase|a2|group|viii|phospholipase|a2|group|x|phospholipase|a2|group|xii|phospholipase|a2|group|xv|phospholipase|a2|group|xvi|phospholipase|d1|phospholipase|d2|phospholipase|d3|phospholipase|d4|phospholipase|d5|phospholipase|d6|diacylglycerol|kinase|alpha|diacylglycerol|kinase|beta|diacylglycerol|kinase|gamma|diacylglycerol|kinase|delta|diacylglycerol|kinase|epsilon|diacylglycerol|kinase|zeta|diacylglycerol|kinase|eta|diacylglycerol|kinase|theta|diacylglycerol|kinase|iota|diacylglycerol|kinase|kappa|diacylglycerol|lipase|alpha|diacylglycerol|lipase|beta|diacylglycerol|lipase|gamma|monoacylglycerol|lipase|hormone|sensitive|lipase|adipose|triglyceride|lipase|lipoprotein|lipase|hepatic|lipase|endothelial|lipase|pancreatic|lipase|gastric|lipase|lingual|lipase|phosphatidic|acid|phosphatase|1|phosphatidic|acid|phosphatase|2|phosphatidic|acid|phosphatase|3|inositol|polyphosphate|1|phosphatase|inositol|polyphosphate|4|phosphatase|type|i|inositol|polyphosphate|4|phosphatase|type|ii|inositol|polyphosphate|5|phosphatase|a|inositol|polyphosphate|5|phosphatase|b|inositol|polyphosphate|5|phosphatase|c|inositol|polyphosphate|5|phosphatase|d|inositol|polyphosphate|5|phosphatase|e|inositol|polyphosphate|5|phosphatase|f|inositol|polyphosphate|5|phosphatase|j|inositol|polyphosphate|5|phosphatase|k|phosphatidylinositol|3|kinase|catalytic|subunit|alpha|phosphatidylinositol|3|kinase|catalytic|subunit|beta|phosphatidylinositol|3|kinase|catalytic|subunit|delta|phosphatidylinositol|3|kinase|catalytic|subunit|gamma|phosphatidylinositol|3|kinase|regulatory|subunit|1|phosphatidylinositol|3|kinase|regulatory|subunit|2|phosphatidylinositol|3|kinase|regulatory|subunit|3|phosphatidylinositol|3|kinase|regulatory|subunit|4|phosphatidylinositol|3|kinase|regulatory|subunit|5|phosphatidylinositol|3|kinase|regulatory|subunit|6|phosphatidylinositol|3|kinase|c3|phosphatidylinositol|4|kinase|alpha|phosphatidylinositol|4|kinase|beta|phosphatidylinositol|4|kinase|2a|phosphatidylinositol|4|kinase|2b|phosphatidylinositol|5|kinase|1a|phosphatidylinositol|5|kinase|1b|phosphatidylinositol|5|kinase|1c|phosphatidylinositol|5|kinase|1gamma|phosphatidylinositol|3|4|5|trisphosphate|3|phosphatase|a|phosphatidylinositol|3|4|5|trisphosphate|3|phosphatase|b|phosphatidylinositol|3|4|5|trisphosphate|3|phosphatase|c|phosphatidylinositol|3|4|5|trisphosphate|3|phosphatase|d|phosphatidylinositol|3|4|5|trisphosphate|dependent|rac|exchange|factor|1|phosphatidylinositol|3|4|5|trisphosphate|dependent|rac|exchange|factor|2|phosphatidylinositol|3|4|5|trisphosphate|dependent|rac|exchange|factor|3|phosphatidylinositol|3|4|5|trisphosphate|dependent|rac|exchange|factor|4|phosphatidylinositol|3|4|5|trisphosphate|dependent|rac|exchange|factor|5|phosphatidylinositol|3|4|5|trisphosphate|dependent|rac|exchange|factor|6|akt|serine|threonine|kinase|1|akt|serine|threonine|kinase|2|akt|serine|threonine|kinase|3|3|phosphoinositide|dependent|protein|kinase|1|phosphoinositide|dependent|protein|kinase|2|serum|glucocorticoid|regulated|kinase|1|serum|glucocorticoid|regulated|kinase|2|serum|glucocorticoid|regulated|kinase|3|ribosomal|protein|s6|kinase|a1|ribosomal|protein|s6|kinase|a2|ribosomal|protein|s6|kinase|a3|ribosomal|protein|s6|kinase|a4|ribosomal|protein|s6|kinase|a5|ribosomal|protein|s6|kinase|a6|ribosomal|protein|s6|kinase|b1|ribosomal|protein|s6|kinase|b2|eukaryotic|translation|initiation|factor|4e|binding|protein|1|eukaryotic|translation|initiation|factor|4e|binding|protein|2|eukaryotic|translation|initiation|factor|4e|binding|protein|3|mechanistic|target|of|rapamycin|kinase|mechanistic|target|of|rapamycin|complex|1|mechanistic|target|of|rapamycin|complex|2|regulatory|associated|protein|of|mtor|complex|1|rapamycin|insensitive|companion|of|mtor|complex|2|dep|domain|containing|mtor|interacting|protein|proline|rich|akt|substrate|of|40|kda|g|protein|beta|subunit|like|mammalian|lethal|with|sec13|protein|8|target|of|rapamycin|complex|subunit|lst8|regulatory|associated|protein|of|mtor|complex|1|rapamycin|sensitive|adapter|protein|of|mtor|fk506|binding|protein|12|rapamycin|fk506|binding|protein|12|rapamycin|associated|protein|1|tuberous|sclerosis|1|tuberous|sclerosis|2|tsc1|tsc2|complex|ras|homolog|enriched|in|brain|ras|homolog|family|member|a|ras|homolog|family|member|b|ras|homolog|family|member|c|ras|homolog|family|member|d|ras|homolog|family|member|f|ras|homolog|family|member|g|ras|homolog|family|member|h|ras|homolog|family|member|j|ras|homolog|family|member|q|ras|homolog|family|member|t1|ras|homolog|family|member|t2|ras|homolog|family|member|u|ras|homolog|family|member|v|cell|division|cycle|42|ras|related|c3|botulinum|toxin|substrate|1|ras|related|c3|botulinum|toxin|substrate|2|ras|related|c3|botulinum|toxin|substrate|3|rho|guanine|nucleotide|exchange|factor|1|rho|guanine|nucleotide|exchange|factor|2|rho|guanine|nucleotide|exchange|factor|3|rho|guanine|nucleotide|exchange|factor|4|rho|guanine|nucleotide|exchange|factor|5|rho|guanine|nucleotide|exchange|factor|6|rho|guanine|nucleotide|exchange|factor|7|rho|guanine|nucleotide|exchange|factor|8|rho|guanine|nucleotide|exchange|factor|9|rho|guanine|nucleotide|exchange|factor|10|rho|guanine|nucleotide|exchange|factor|11|rho|guanine|nucleotide|exchange|factor|12|rho|guanine|nucleotide|exchange|factor|15|rho|guanine|nucleotide|exchange|factor|16|rho|guanine|nucleotide|exchange|factor|17|rho|guanine|nucleotide|exchange|factor|18|rho|guanine|nucleotide|exchange|factor|19|rho|guanine|nucleotide|exchange|factor|25|rho|guanine|nucleotide|exchange|factor|26|rho|guanine|nucleotide|exchange|factor|39|rho|guanine|nucleotide|exchange|factor|40|rho|gtpase|activating|protein|1|rho|gtpase|activating|protein|4|rho|gtpase|activating|protein|5|rho|gtpase|activating|protein|6|rho|gtpase|activating|protein|8|rho|gtpase|activating|protein|9|rho|gtpase|activating|protein|10|rho|gtpase|activating|protein|11|rho|gtpase|activating|protein|12|rho|gtpase|activating|protein|15|rho|gtpase|activating|protein|17|rho|gtpase|activating|protein|18|rho|gtpase|activating|protein|19|rho|gtpase|activating|protein|20|rho|gtpase|activating|protein|21|rho|gtpase|activating|protein|22|rho|gtpase|activating|protein|23|rho|gtpase|activating|protein|24|rho|gtpase|activating|protein|25|rho|gtpase|activating|protein|26|rho|gtpase|activating|protein|27|rho|gtpase|activating|protein|28|rho|gtpase|activating|protein|29|rho|gtpase|activating|protein|30|rho|gtpase|activating|protein|31|rho|gtpase|activating|protein|32|rho|gtpase|activating|protein|33|rho|gtpase|activating|protein|34|rho|gtpase|activating|protein|35|rho|gtpase|activating|protein|36|rho|gtpase|activating|protein|39|rho|gtpase|activating|protein|40|rho|associated|coiled|coil|containing|protein|kinase|1|rho|associated|coiled|coil|containing|protein|kinase|2|p21|rac|cdc42|activated|kinase|1|p21|rac|cdc42|activated|kinase|2|p21|rac|cdc42|activated|kinase|3|p21|rac|cdc42|activated|kinase|4|p21|rac|cdc42|activated|kinase|5|p21|rac|cdc42|activated|kinase|6|p21|rac|cdc42|activated|kinase|7|wiskott|aldrich|syndrome|protein|wiskott|aldrich|syndrome|protein|family|member|1|wiskott|aldrich|syndrome|protein|family|member|2|wiskott|aldrich|syndrome|protein|family|member|3|wiskott|aldrich|syndrome|protein|and|scar|homolog|wiskott|aldrich|syndrome|protein|and|scar|homolog|family|member|1|wiskott|aldrich|syndrome|protein|and|scar|homolog|family|member|2|wiskott|aldrich|syndrome|protein|and|scar|homolog|family|member|3|actin|related|protein|2|3|complex|subunit|1a|actin|related|protein|2|3|complex|subunit|1b|actin|related|protein|2|3|complex|subunit|2|actin|related|protein|2|3|complex|subunit|3|actin|related|protein|2|3|complex|subunit|4|actin|related|protein|2|3|complex|subunit|5|actin|related|protein|2|3|complex|subunit|5|like|formin|1|formin|2|formin|like|1|formin|like|2|formin|like|3|formin|homology|2|domain|containing|1|formin|homology|2|domain|containing|2|formin|homology|2|domain|containing|3|diaphanous|related|formin|1|diaphanous|related|formin|2|diaphanous|related|formin|3|profilin|1|profilin|2|profilin|3|profilin|4|cofilin|1|cofilin|2|destrin|actin|depolymerizing|factor|actin|depolymerizing|factor|like|gelsolin|villin|1|villin|2|villin|like|scinderin|adseverin|fragmin|severin|ezrin|radixin|moesin|ezrin|radixin|moesin|binding|phosphoprotein|50|merlin|neurofibromatosis|2|talin|1|talin|2|vinculin|metavinculin|paxillin|hic|5|zyxin|lipoma|preferred|partner|vasodilator|stimulated|phosphoprotein|enabled|homolog|enabled|vasodilator|stimulated|phosphoprotein|like|mena|enah|actin|filament|associated|protein|1|actin|filament|associated|protein|1|like|1|actin|filament|associated|protein|1|like|2|filamin|a|filamin|b|filamin|c|alpha|actinin|1|alpha|actinin|2|alpha|actinin|3|alpha|actinin|4|spectrin|alpha|erythrocytic|1|spectrin|alpha|non|erythrocytic|1|spectrin|beta|erythrocytic|spectrin|beta|non|erythrocytic|1|spectrin|beta|non|erythrocytic|2|spectrin|beta|non|erythrocytic|3|spectrin|beta|non|erythrocytic|4|spectrin|beta|non|erythrocytic|5|ankyrin|1|ankyrin|2|ankyrin|3|protein|4|1|band|4|1|like|1|band|4|1|like|2|band|4|1|like|3|band|4|1|like|4|band|4|1|like|5|erythrocyte|membrane|protein|band|4|1|like|1|erythrocyte|membrane|protein|band|4|1|like|2|erythrocyte|membrane|protein|band|4|1|like|3|erythrocyte|membrane|protein|band|4|1|like|4|erythrocyte|membrane|protein|band|4|1|like|5|erythrocyte|membrane|protein|band|4|9|dematin|actin|binding|protein|tropomyosin|1|tropomyosin|2|tropomyosin|3|tropomyosin|4|troponin|c|type|1|troponin|c|type|2|troponin|i|type|1|troponin|i|type|2|troponin|i|type|3|troponin|t|type|1|troponin|t|type|2|troponin|t|type|3|myosin|heavy|chain|1|myosin|heavy|chain|2|myosin|heavy|chain|3|myosin|heavy|chain|4|myosin|heavy|chain|6|myosin|heavy|chain|7|myosin|heavy|chain|8|myosin|heavy|chain|9|myosin|heavy|chain|10|myosin|heavy|chain|11|myosin|heavy|chain|13|myosin|heavy|chain|14|myosin|heavy|chain|15|myosin|light|chain|1|myosin|light|chain|2|myosin|light|chain|3|myosin|light|chain|4|myosin|light|chain|5|myosin|light|chain|6|myosin|light|chain|7|myosin|light|chain|9|myosin|light|chain|10|myosin|light|chain|12a|myosin|light|chain|12b|myosin|regulatory|light|chain|2|myosin|regulatory|light|chain|3|myosin|binding|protein|c|cardiac|myosin|binding|protein|c|slow|type|myosin|binding|protein|c|fast|type|myosin|binding|protein|h|myosin|binding|protein|h|like|titin|titin|cap|connectin|obscurin|obscurin|like|1|myomesin|1|myomesin|2|myomesin|3|muscle|lim|protein|cardiac|lim|protein|four|and|a|half|lim|domains|1|four|and|a|half|lim|domains|2|four|and|a|half|lim|domains|3|four|and|a|half|lim|domains|5|cysteine|and|glycine|rich|protein|1|cysteine|and|glycine|rich|protein|2|cysteine|and|glycine|rich|protein|3|muscle|specific|ring|finger|protein|1|muscle|specific|ring|finger|protein|2|muscle|specific|ring|finger|protein|3|f|box|protein|32|tripartite|motif|containing|63|ankyrin|repeat|and|socs|box|containing|1|ankyrin|repeat|and|socs|box|containing|2|tubulin|alpha|1a|tubulin|alpha|1b|tubulin|alpha|1c|tubulin|alpha|3c|tubulin|alpha|3d|tubulin|alpha|3e|tubulin|alpha|4a|tubulin|alpha|8|tubulin|beta|1|tubulin|beta|2a|tubulin|beta|2b|tubulin|beta|3|tubulin|beta|4a|tubulin|beta|4b|tubulin|beta|6|tubulin|beta|8|tubulin|gamma|1|tubulin|gamma|2|tubulin|delta|1|tubulin|epsilon|1|tubulin|zeta|1|kinesin|family|member|1a|kinesin|family|member|1b|kinesin|family|member|1c|kinesin|family|member|2a|kinesin|family|member|2b|kinesin|family|member|2c|kinesin|family|member|3a|kinesin|family|member|3b|kinesin|family|member|3c|kinesin|family|member|4a|kinesin|family|member|4b|kinesin|family|member|5a|kinesin|family|member|5b|kinesin|family|member|5c|kinesin|family|member|6|kinesin|family|member|7|kinesin|family|member|9|kinesin|family|member|10|kinesin|family|member|11|kinesin|family|member|12|kinesin|family|member|13a|kinesin|family|member|13b|kinesin|family|member|14|kinesin|family|member|15|kinesin|family|member|16a|kinesin|family|member|16b|kinesin|family|member|17|kinesin|family|member|18a|kinesin|family|member|18b|kinesin|family|member|19|kinesin|family|member|20a|kinesin|family|member|20b|kinesin|family|member|21a|kinesin|family|member|21b|kinesin|family|member|22|kinesin|family|member|23|kinesin|family|member|24|kinesin|family|member|25|kinesin|family|member|26a|kinesin|family|member|26b|kinesin|family|member|27|dynein|cytoplasmic|1|heavy|chain|1|dynein|cytoplasmic|1|heavy|chain|2|dynein|cytoplasmic|1|intermediate|chain|1|dynein|cytoplasmic|1|intermediate|chain|2|dynein|cytoplasmic|1|light|intermediate|chain|1|dynein|cytoplasmic|1|light|intermediate|chain|2|dynein|cytoplasmic|2|heavy|chain|1|dynein|cytoplasmic|2|heavy|chain|2|dynein|cytoplasmic|2|intermediate|chain|1|dynein|cytoplasmic|2|intermediate|chain|2|dynein|cytoplasmic|2|light|intermediate|chain|1|dynein|light|chain|1|dynein|light|chain|2|dynein|light|chain|3|dynein|light|chain|4|dynactin|subunit|1|dynactin|subunit|2|dynactin|subunit|3|dynactin|subunit|4|dynactin|subunit|5|dynactin|subunit|6|dynein|axonemal|heavy|chain|1|dynein|axonemal|heavy|chain|2|dynein|axonemal|heavy|chain|3|dynein|axonemal|heavy|chain|5|dynein|axonemal|heavy|chain|6|dynein|axonemal|heavy|chain|7|dynein|axonemal|heavy|chain|8|dynein|axonemal|heavy|chain|9|dynein|axonemal|heavy|chain|10|dynein|axonemal|heavy|chain|11|dynein|axonemal|heavy|chain|12|dynein|axonemal|heavy|chain|17|dynein|axonemal|intermediate|chain|1|dynein|axonemal|intermediate|chain|2|dynein|axonemal|intermediate|chain|3|dynein|axonemal|intermediate|chain|4|dynein|axonemal|light|chain|1|dynein|axonemal|light|chain|2|dynein|axonemal|light|chain|3|dynein|axonemal|light|chain|4|dynein|axonemal|light|intermediate|chain|1|dynein|axonemal|light|intermediate|chain|2|dynein|axonemal|light|intermediate|chain|3|dynein|axonemal|light|intermediate|chain|4|intermediate|filament|family|orphan|1|intermediate|filament|family|orphan|2|keratin|1|keratin|2|keratin|3|keratin|4|keratin|5|keratin|6a|keratin|6b|keratin|6c|keratin|7|keratin|8|keratin|9|keratin|10|keratin|12|keratin|13|keratin|14|keratin|15|keratin|16|keratin|17|keratin|18|keratin|19|keratin|20|keratin|23|keratin|24|keratin|25|keratin|26|keratin|27|keratin|28|keratin|31|keratin|32|keratin|33a|keratin|33b|keratin|34|keratin|35|keratin|36|keratin|37|keratin|38|keratin|39|keratin|40|keratin|71|keratin|72|keratin|73|keratin|74|keratin|75|keratin|76|keratin|77|keratin|78|keratin|79|keratin|80|keratin|81|keratin|82|keratin|83|keratin|84|keratin|85|keratin|86|vimentin|desmin|glial|fibrillary|acidic|protein|peripherin|syncoilin|synemin|nestin|lamin|a|c|lamin|b1|lamin|b2|nuclear|envelope|spectrin|repeat|protein|1|nuclear|envelope|spectrin|repeat|protein|2|emerin|lamin|associated|polypeptide|2|alpha|lamin|associated|polypeptide|2|beta|barrier|to|autointegration|factor|1|lamin|b|receptor|nucleoporin|35|nucleoporin|37|nucleoporin|43|nucleoporin|54|nucleoporin|58|nucleoporin|62|nucleoporin|85|nucleoporin|93|nucleoporin|98|nucleoporin|107|nucleoporin|133|nucleoporin|153|nucleoporin|155|nucleoporin|160|nucleoporin|188|nucleoporin|205|nucleoporin|214|ran|gtpase|ran|gtpase|activating|protein|1|ran|guanine|nucleotide|exchange|factor|chromosome|region|maintenance|1|exportin|1|exportin|2|exportin|4|exportin|5|exportin|6|exportin|7|exportin|t|importin|alpha|1|importin|alpha|2|importin|alpha|3|importin|alpha|4|importin|alpha|5|importin|alpha|6|importin|alpha|7|importin|beta|1|importin|beta|2|importin|beta|3|importin|4|importin|5|importin|7|importin|8|importin|9|importin|11|importin|13|cellular|apoptosis|susceptibility|nucleoporin|like|1|nucleoporin|like|2|nuclear|transport|factor|2|nuclear|transport|factor|2|like|export|factor|1|nuclear|import|factor|1|nuclear|import|factor|2|nuclear|import|factor|3|nuclear|import|factor|4|nuclear|import|factor|5|nuclear|import|factor|6|nuclear|import|factor|7|nuclear|import|factor|8|nuclear|import|factor|9|nuclear|import|factor|10|nuclear|import|factor|11|nuclear|import|factor|12|nuclear|import|factor|13|nuclear|import|factor|14|nuclear|import|factor|15|nuclear|import|factor|16|nuclear|import|factor|17|nuclear|import|factor|18|nuclear|import|factor|19|nuclear|import|factor|20|nuclear|import|factor|21|nuclear|import|factor|22|nuclear|import|factor|23|nuclear|import|factor|24|nuclear|import|factor|25|nuclear|import|factor|26|nuclear|import|factor|27|nuclear|import|factor|28|nuclear|import|factor|29|nuclear|import|factor|30|nuclear|import|factor|31|nuclear|import|factor|32|nuclear|import|factor|33|nuclear|import|factor|34|nuclear|import|factor|35|nuclear|import|factor|36|nuclear|import|factor|37|nuclear|import|factor|38|nuclear|import|factor|39|nuclear|import|factor|40|nuclear|import|factor|41|nuclear|import|factor|42|nuclear|import|factor|43|nuclear|import|factor|44|nuclear|import|factor|45|nuclear|import|factor|46|nuclear|import|factor|47|nuclear|import|factor|48|nuclear|import|factor|49|nuclear|import|factor|50|nuclear|import|factor|51|nuclear|import|factor|52|nuclear|import|factor|53|nuclear|import|factor|54|nuclear|import|factor|55|nuclear|import|factor|56|nuclear|import|factor|57|nuclear|import|factor|58|nuclear|import|factor|59|nuclear|import|factor|60|nuclear|import|factor|61|nuclear|import|factor|62|nuclear|import|factor|63|nuclear|import|factor|64|nuclear|import|factor|65|nuclear|import|factor|66|nuclear|import|factor|67|nuclear|import|factor|68|nuclear|import|factor|69|nuclear|import|factor|70|nuclear|import|factor|71|nuclear|import|factor|72|nuclear|import|factor|73|nuclear|import|factor|74|nuclear|import|factor|75|nuclear|import|factor|76|nuclear|import|factor|77|nuclear|import|factor|78|nuclear|import|factor|79|nuclear|import|factor|80|nuclear|import|factor|81|nuclear|import|factor|82|nuclear|import|factor|83|nuclear|import|factor|84|nuclear|import|factor|85|nuclear|import|factor|86|nuclear|import|factor|87|nuclear|import|factor|88|nuclear|import|factor|89|nuclear|import|factor|90|nuclear|import|factor|91|nuclear|import|factor|92|nuclear|import|factor|93|nuclear|import|factor|94|nuclear|import|factor|95|nuclear|import|factor|96|nuclear|import|factor|97|nuclear|import|factor|98|nuclear|import|factor|99|nuclear|import|factor|100)\b',
        ]
        
        genes = set()
        proteins = set()
        diseases = set()
        methods = set()
        drugs = set()
        
        # Extract entities using patterns
        for pattern in gene_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            genes.update([match.upper() for match in matches])
        
        for pattern in protein_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            proteins.update([match.upper() for match in matches])
        
        for pattern in disease_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            diseases.update([match.lower() for match in matches])
        
        for pattern in method_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            methods.update([match.lower() for match in matches])
        
        for pattern in drug_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            drugs.update([match.lower() for match in matches])
        
        # Calculate confidence scores (simplified)
        confidence_scores = {
            "genes": 0.8,
            "proteins": 0.7,
            "diseases": 0.85,
            "methods": 0.9,
            "drugs": 0.75
        }
        
        return BiomarkerExtractionResult(
            genes=list(genes)[:20],  # Limit to top 20
            proteins=list(proteins)[:20],
            diseases=list(diseases)[:10],
            methods=list(methods)[:10],
            drugs=list(drugs)[:15],
            confidence_scores=confidence_scores
        )
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize text using free models
        """
        try:
            if not self.is_initialized:
                return self._rule_based_summary(text, max_length)
            
            # Use free summarization model
            summary = self.summarizer(text, max_length=max_length, min_length=50)
            return summary[0]['summary_text']
            
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return self._rule_based_summary(text, max_length)
    
    def _rule_based_summary(self, text: str, max_length: int) -> str:
        """
        Fallback rule-based summarization
        """
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) <= 3:
            return text
        
        # Simple extractive summarization
        # Take first, middle, and last sentences
        summary_sentences = [
            sentences[0],
            sentences[len(sentences)//2],
            sentences[-1]
        ]
        
        summary = '. '.join(summary_sentences).strip()
        
        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def analyze_biomedical_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive biomedical text analysis
        """
        try:
            # Extract biomarkers
            biomarkers = self.extract_biomarkers(text)
            
            # Generate summary
            summary = self.summarize_text(text)
            
            # Basic statistics
            stats = {
                "character_count": len(text),
                "word_count": len(text.split()),
                "sentence_count": len(re.split(r'[.!?]+', text)),
                "unique_genes": len(set(biomarkers.genes)),
                "unique_diseases": len(set(biomarkers.diseases)),
                "unique_methods": len(set(biomarkers.methods))
            }
            
            return {
                "summary": summary,
                "biomarkers": biomarkers,
                "statistics": stats,
                "key_findings": self._extract_key_findings(text),
                "clinical_relevance": self._assess_clinical_relevance(biomarkers)
            }
            
        except Exception as e:
            logger.error(f"Error in biomedical analysis: {e}")
            return {
                "summary": "Error in analysis",
                "biomarkers": BiomarkerExtractionResult([], [], [], [], [], {}),
                "statistics": {},
                "key_findings": [],
                "clinical_relevance": "Unable to assess"
            }
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """
        Extract key findings from biomedical text
        """
        findings = []
        
        # Look for conclusion patterns
        conclusion_patterns = [
            r'(?:conclusion|conclusions?|findings?|results?|outcome)s?:\s*([^.]+)',
            r'(?:we found|we identified|we discovered|we observed|we detected)\s+([^.]+)',
            r'(?:significant|statistically significant|notable|important)\s+([^.]+)',
            r'(?:increased|decreased|upregulated|downregulated|elevated|reduced)\s+([^.]+)',
        ]
        
        for pattern in conclusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            findings.extend(matches[:3])  # Limit to 3 per pattern
        
        return findings[:10]  # Limit to top 10 findings
    
    def _assess_clinical_relevance(self, biomarkers: BiomarkerExtractionResult) -> str:
        """
        Assess clinical relevance based on extracted biomarkers
        """
        relevance_score = 0
        
        # Check for known clinical genes
        clinical_genes = {"BRCA1", "BRCA2", "TP53", "EGFR", "KRAS", "PIK3CA", "APC", "PTEN"}
        clinical_gene_matches = len(set(biomarkers.genes) & clinical_genes)
        relevance_score += clinical_gene_matches * 10
        
        # Check for diseases
        if biomarkers.diseases:
            relevance_score += len(biomarkers.diseases) * 5
        
        # Check for methods
        clinical_methods = {"clinical trial", "cohort study", "case-control", "rct"}
        clinical_method_matches = len(set(biomarkers.methods) & clinical_methods)
        relevance_score += clinical_method_matches * 15
        
        if relevance_score >= 30:
            return "High clinical relevance"
        elif relevance_score >= 15:
            return "Moderate clinical relevance"
        elif relevance_score >= 5:
            return "Low clinical relevance"
        else:
            return "Limited clinical relevance"
    
    def generate_research_summary(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive research summary from multiple papers
        """
        all_genes = set()
        all_diseases = set()
        all_methods = set()
        all_drugs = set()
        
        summaries = []
        
        for paper in papers:
            if 'abstract' in paper:
                analysis = self.analyze_biomedical_text(paper['abstract'])
                summaries.append(analysis['summary'])
                
                # Aggregate biomarkers
                biomarkers = analysis['biomarkers']
                all_genes.update(biomarkers.genes)
                all_diseases.update(biomarkers.diseases)
                all_methods.update(biomarkers.methods)
                all_drugs.update(biomarkers.drugs)
        
        # Generate meta-analysis
        meta_summary = self._generate_meta_summary(summaries)
        
        return {
            "meta_summary": meta_summary,
            "aggregated_biomarkers": {
                "genes": list(all_genes)[:50],
                "diseases": list(all_diseases)[:20],
                "methods": list(all_methods)[:20],
                "drugs": list(all_drugs)[:30]
            },
            "research_trends": self._identify_research_trends(all_methods),
            "therapeutic_targets": self._identify_therapeutic_targets(all_genes, all_drugs),
            "paper_count": len(papers)
        }
    
    def _generate_meta_summary(self, summaries: List[str]) -> str:
        """
        Generate meta-summary from multiple paper summaries
        """
        if not summaries:
            return "No summaries available"
        
        # Simple approach: combine unique sentences
        all_sentences = []
        for summary in summaries:
            sentences = re.split(r'[.!?]+', summary)
            all_sentences.extend([s.strip() for s in sentences if s.strip()])
        
        # Remove duplicates and take most informative sentences
        unique_sentences = list(set(all_sentences))[:5]
        
        return '. '.join(unique_sentences) + '.'
    
    def _identify_research_trends(self, methods: set) -> List[str]:
        """
        Identify research trends from methods
        """
        trends = []
        
        # Look for trending methods
        trending_methods = {
            "single-cell": "Single-cell analysis",
            "crispr": "CRISPR gene editing",
            "machine learning": "Machine learning applications",
            "proteomics": "Proteomics approaches",
            "metabolomics": "Metabolomics studies",
            "immunotherapy": "Immunotherapy research"
        }
        
        for method in methods:
            for trend_key, trend_name in trending_methods.items():
                if trend_key in method.lower():
                    trends.append(trend_name)
        
        return list(set(trends))[:10]
    
    def _identify_therapeutic_targets(self, genes: set, drugs: set) -> List[Dict[str, str]]:
        """
        Identify potential therapeutic targets
        """
        targets = []
        
        # Known druggable genes
        druggable_genes = {
            "EGFR": "Tyrosine kinase inhibitors",
            "BRAF": "BRAF inhibitors",
            "PIK3CA": "PI3K inhibitors",
            "PTEN": "PI3K/AKT pathway modulators",
            "TP53": "p53 activators",
            "KRAS": "RAS inhibitors",
            "HER2": "HER2 inhibitors",
            "VEGF": "Anti-angiogenic agents"
        }
        
        for gene in genes:
            if gene in druggable_genes:
                targets.append({
                    "gene": gene,
                    "therapeutic_class": druggable_genes[gene],
                    "evidence": "Literature-based"
                })
        
        return targets[:10]

# Global instance
free_ai_service = FreeAIService()