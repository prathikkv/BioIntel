import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import PyPDF2
from io import BytesIO

# Conditional import for pdfplumber (better PDF parsing)
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("⚠️  pdfplumber not available - falling back to PyPDF2 for PDF parsing")
import httpx

from models.database import get_db
from models.literature import LiteratureSummary, ChatSession, ChatMessage, KnowledgeBase
from models.user import User
from utils.logging import get_logger
from utils.config import get_settings
from utils.security import security_utils
from services.free_ai_service import free_ai_service
from services.bio_apis_service import bio_apis_service

settings = get_settings()
logger = get_logger(__name__)

class LiteratureService:
    """Service for literature processing and AI-powered summarization using FREE AI"""
    
    def __init__(self):
        self.db = next(get_db())
        self.free_ai = free_ai_service
        self.bio_apis = bio_apis_service
    
    @staticmethod
    async def initialize():
        """Initialize literature service"""
        logger.info("Literature service initialized")
    
    async def process_abstract(self, user_id: int, abstract_text: str, 
                             metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process and summarize research paper abstract"""
        try:
            # Validate abstract length
            if len(abstract_text) > settings.MAX_PAPER_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Abstract too long. Maximum length: {settings.MAX_PAPER_LENGTH} characters"
                )
            
            # Clean and validate abstract text
            cleaned_abstract = self._clean_text(abstract_text)
            
            # Create literature summary record
            literature_summary = LiteratureSummary(
                user_id=user_id,
                title=metadata.get("title", "Untitled"),
                authors=metadata.get("authors"),
                journal=metadata.get("journal"),
                publication_date=self._parse_date(metadata.get("publication_date")),
                doi=metadata.get("doi"),
                pmid=metadata.get("pmid"),
                abstract=cleaned_abstract,
                source_type="abstract",
                source_url=metadata.get("source_url"),
                processing_status="processing"
            )
            
            self.db.add(literature_summary)
            self.db.commit()
            self.db.refresh(literature_summary)
            
            # Process abstract with AI
            summary_result = await self._generate_summary(cleaned_abstract, "abstract")
            
            # Update literature summary with results
            literature_summary.summary = summary_result["summary"]
            literature_summary.key_findings = summary_result["key_findings"]
            literature_summary.biomarkers = summary_result["biomarkers"]
            literature_summary.genes = summary_result["genes"]
            literature_summary.diseases = summary_result["diseases"]
            literature_summary.methods = summary_result["methods"]
            literature_summary.confidence_score = summary_result["confidence_score"]
            literature_summary.processing_status = "completed"
            
            self.db.commit()
            
            logger.info(f"Abstract processed successfully: {literature_summary.id}")
            
            return {
                "message": "Abstract processed successfully",
                "literature_summary": literature_summary.to_dict(),
                "processing_results": summary_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing abstract: {str(e)}")
            
            # Update status to failed if record exists
            if 'literature_summary' in locals():
                literature_summary.processing_status = "failed"
                literature_summary.processing_log = str(e)
                self.db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during abstract processing"
            )
    
    async def process_pdf(self, user_id: int, pdf_data: bytes, 
                         metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process and summarize PDF research paper"""
        try:
            # Validate PDF size
            if len(pdf_data) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF file too large"
                )
            
            # Extract text from PDF
            try:
                full_text = await self._extract_pdf_text(pdf_data)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error extracting text from PDF: {str(e)}"
                )
            
            # Validate extracted text length
            if len(full_text) > settings.MAX_PAPER_LENGTH:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PDF content too long. Maximum length: {settings.MAX_PAPER_LENGTH} characters"
                )
            
            # Extract abstract from full text
            abstract = self._extract_abstract(full_text)
            
            # Create literature summary record
            literature_summary = LiteratureSummary(
                user_id=user_id,
                title=metadata.get("title", "Untitled"),
                authors=metadata.get("authors"),
                journal=metadata.get("journal"),
                publication_date=self._parse_date(metadata.get("publication_date")),
                doi=metadata.get("doi"),
                pmid=metadata.get("pmid"),
                abstract=abstract,
                full_text=full_text,
                source_type="full_paper",
                file_name=metadata.get("file_name"),
                processing_status="processing"
            )
            
            self.db.add(literature_summary)
            self.db.commit()
            self.db.refresh(literature_summary)
            
            # Process full text with AI
            summary_result = await self._generate_summary(full_text, "full_paper")
            
            # Update literature summary with results
            literature_summary.summary = summary_result["summary"]
            literature_summary.key_findings = summary_result["key_findings"]
            literature_summary.biomarkers = summary_result["biomarkers"]
            literature_summary.genes = summary_result["genes"]
            literature_summary.diseases = summary_result["diseases"]
            literature_summary.methods = summary_result["methods"]
            literature_summary.confidence_score = summary_result["confidence_score"]
            literature_summary.processing_status = "completed"
            
            self.db.commit()
            
            logger.info(f"PDF processed successfully: {literature_summary.id}")
            
            return {
                "message": "PDF processed successfully",
                "literature_summary": literature_summary.to_dict(),
                "processing_results": summary_result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            
            # Update status to failed if record exists
            if 'literature_summary' in locals():
                literature_summary.processing_status = "failed"
                literature_summary.processing_log = str(e)
                self.db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during PDF processing"
            )
    
    async def _extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        try:
            # Try pdfplumber first (better for complex layouts)
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(BytesIO(pdf_data)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            else:
                # Skip pdfplumber if not available, go directly to PyPDF2
                raise Exception("pdfplumber not available, using PyPDF2")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {str(e)}, trying PyPDF2")
            
            try:
                # Fallback to PyPDF2
                reader = PyPDF2.PdfReader(BytesIO(pdf_data))
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e:
                raise Exception(f"Failed to extract text from PDF: {str(e)}")
        
        if not text.strip():
            raise Exception("No text could be extracted from PDF")
        
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
        
        # Remove very short lines (likely artifacts)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        return '\n'.join(cleaned_lines).strip()
    
    def _extract_abstract(self, full_text: str) -> str:
        """Extract abstract from full text"""
        # Look for abstract section
        abstract_patterns = [
            r'ABSTRACT\s*\n(.*?)\n(?:INTRODUCTION|KEYWORDS|1\.|BACKGROUND)',
            r'Abstract\s*\n(.*?)\n(?:Introduction|Keywords|1\.|Background)',
            r'SUMMARY\s*\n(.*?)\n(?:INTRODUCTION|KEYWORDS|1\.|BACKGROUND)',
            r'Summary\s*\n(.*?)\n(?:Introduction|Keywords|1\.|Background)'
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no abstract found, return first few sentences
        sentences = re.split(r'[.!?]+', full_text)
        return '. '.join(sentences[:5]) + '.' if sentences else ""
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse publication date string"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%d/%m/%Y",
                "%B %d, %Y",
                "%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    async def _generate_summary(self, text: str, content_type: str) -> Dict[str, Any]:
        """Generate AI-powered summary using FREE AI service"""
        try:
            logger.info(f"Generating summary for {content_type} using free AI")
            
            # Use free AI service for comprehensive analysis
            analysis = self.free_ai.analyze_biomedical_text(text)
            
            # Enhance with PubMed literature search if possible
            try:
                # Extract key terms for literature search
                key_terms = analysis["biomarkers"].genes[:3] + analysis["biomarkers"].diseases[:2]
                if key_terms:
                    search_query = " AND ".join(key_terms)
                    pubmed_results = await self.bio_apis.search_pubmed(search_query, max_results=5)
                    
                    # Add related literature context
                    related_papers = [
                        {
                            "title": paper.title,
                            "authors": paper.authors[:3],  # First 3 authors
                            "pmid": paper.pmid
                        }
                        for paper in pubmed_results
                    ]
                    analysis["related_literature"] = related_papers
            except Exception as e:
                logger.warning(f"Could not fetch related literature: {e}")
                analysis["related_literature"] = []
            
            # Convert to expected format
            return {
                "summary": analysis["summary"],
                "key_findings": analysis["key_findings"],
                "biomarkers": analysis["biomarkers"].genes + analysis["biomarkers"].proteins,
                "genes": analysis["biomarkers"].genes,
                "diseases": analysis["biomarkers"].diseases,
                "methods": analysis["biomarkers"].methods,
                "confidence_score": analysis["biomarkers"].confidence_scores.get("genes", 0.8),
                "clinical_relevance": analysis["clinical_relevance"],
                "related_literature": analysis.get("related_literature", [])
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return self._rule_based_processing(text)
    
    def _create_abstract_prompt(self, abstract: str) -> str:
        """Create prompt for abstract processing"""
        return f"""
        You are an expert biomedical researcher. Analyze the following research paper abstract and extract key information.

        Abstract:
        {abstract}

        Please provide a structured analysis in JSON format with the following fields:
        - summary: A concise 2-3 sentence summary
        - key_findings: List of main findings
        - biomarkers: List of biomarkers mentioned
        - genes: List of genes/proteins mentioned
        - diseases: List of diseases/conditions mentioned
        - methods: List of research methods used
        - confidence_score: Your confidence in the analysis (0-1)

        Focus on accuracy and be conservative in your extractions. Only include information that is explicitly mentioned.
        """
    
    def _create_full_paper_prompt(self, full_text: str) -> str:
        """Create prompt for full paper processing"""
        return f"""
        You are an expert biomedical researcher. Analyze the following research paper and extract key information.

        Paper content:
        {full_text[:10000]}...  # Truncate for API limits

        Please provide a structured analysis in JSON format with the following fields:
        - summary: A comprehensive summary (4-6 sentences)
        - key_findings: List of main findings and conclusions
        - biomarkers: List of biomarkers mentioned
        - genes: List of genes/proteins mentioned
        - diseases: List of diseases/conditions mentioned
        - methods: List of research methods and techniques used
        - confidence_score: Your confidence in the analysis (0-1)

        Focus on accuracy and be conservative in your extractions. Only include information that is explicitly mentioned.
        """
    
    async def _call_free_ai(self, question: str, context: str) -> str:
        """Call free AI service for Q&A"""
        try:
            # Use free AI for question answering
            if len(context) > 5000:
                context = context[:5000]  # Truncate for efficiency
            
            combined_text = f"Context: {context}\n\nQuestion: {question}"
            analysis = self.free_ai.analyze_biomedical_text(combined_text)
            
            # Generate answer based on context
            answer = self._generate_contextual_answer(question, context, analysis)
            return answer
            
        except Exception as e:
            logger.error(f"Free AI error: {str(e)}")
            return "I'm sorry, I couldn't process your question. Please try rephrasing it."
    
    def _generate_contextual_answer(self, question: str, context: str, analysis: Dict[str, Any]) -> str:
        """Generate contextual answer using rule-based approach"""
        try:
            question_lower = question.lower()
            
            # Check for specific question types
            if "biomarker" in question_lower or "marker" in question_lower:
                biomarkers = analysis["biomarkers"].genes + analysis["biomarkers"].proteins
                if biomarkers:
                    return f"Based on the text, the following biomarkers were mentioned: {', '.join(biomarkers[:10])}"
                else:
                    return "No specific biomarkers were clearly identified in the provided text."
            
            elif "gene" in question_lower:
                genes = analysis["biomarkers"].genes
                if genes:
                    return f"The following genes were mentioned: {', '.join(genes[:10])}"
                else:
                    return "No specific genes were clearly identified in the provided text."
            
            elif "disease" in question_lower:
                diseases = analysis["biomarkers"].diseases
                if diseases:
                    return f"The following diseases or conditions were mentioned: {', '.join(diseases[:10])}"
                else:
                    return "No specific diseases were clearly identified in the provided text."
            
            elif "method" in question_lower:
                methods = analysis["biomarkers"].methods
                if methods:
                    return f"The following methods were mentioned: {', '.join(methods[:10])}"
                else:
                    return "No specific research methods were clearly identified in the provided text."
            
            elif "summary" in question_lower:
                return analysis["summary"]
            
            elif "finding" in question_lower:
                findings = analysis["key_findings"]
                if findings:
                    return f"Key findings include: {'. '.join(findings[:5])}"
                else:
                    return "No specific findings were clearly identified in the provided text."
            
            else:
                # General response
                return f"Based on the analysis: {analysis['summary']}"
                
        except Exception as e:
            logger.error(f"Error generating contextual answer: {e}")
            return "I'm sorry, I couldn't generate a proper answer. Please try rephrasing your question."
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON found, create structured response
            return {
                "summary": response[:500] + "..." if len(response) > 500 else response,
                "key_findings": [],
                "biomarkers": [],
                "genes": [],
                "diseases": [],
                "methods": [],
                "confidence_score": 0.5
            }
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._rule_based_processing(response)
    
    def _rule_based_processing(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based processing"""
        # Simple keyword extraction
        biomarker_keywords = ["biomarker", "marker", "indicator", "signature"]
        gene_keywords = ["gene", "protein", "mRNA", "expression"]
        disease_keywords = ["cancer", "disease", "disorder", "syndrome", "condition"]
        method_keywords = ["sequencing", "PCR", "western blot", "immunohistochemistry", "analysis"]
        
        biomarkers = self._extract_keywords(text, biomarker_keywords)
        genes = self._extract_keywords(text, gene_keywords)
        diseases = self._extract_keywords(text, disease_keywords)
        methods = self._extract_keywords(text, method_keywords)
        
        return {
            "summary": text[:300] + "..." if len(text) > 300 else text,
            "key_findings": [],
            "biomarkers": biomarkers,
            "genes": genes,
            "diseases": diseases,
            "methods": methods,
            "confidence_score": 0.3
        }
    
    def _extract_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Extract keywords from text"""
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def chat_with_paper(self, user_id: int, literature_id: int, 
                            question: str, session_id: int = None) -> Dict[str, Any]:
        """Chat with paper using RAG-style Q&A"""
        try:
            # Get literature summary
            literature = self.db.query(LiteratureSummary).filter(
                LiteratureSummary.id == literature_id,
                LiteratureSummary.user_id == user_id
            ).first()
            
            if not literature:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Literature not found"
                )
            
            # Get or create chat session
            if session_id:
                session = self.db.query(ChatSession).filter(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                ).first()
                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Chat session not found"
                    )
            else:
                session = ChatSession(
                    user_id=user_id,
                    literature_summary_id=literature_id,
                    session_name=f"Chat with {literature.title[:50]}..."
                )
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
            
            # Store user message
            user_message = ChatMessage(
                session_id=session.id,
                message_type="user",
                content=question
            )
            self.db.add(user_message)
            
            # Generate response using AI
            response = await self._generate_chat_response(literature, question)
            
            # Store assistant message
            assistant_message = ChatMessage(
                session_id=session.id,
                message_type="assistant",
                content=response["content"],
                citations=response.get("citations", []),
                confidence_score=response.get("confidence_score", 0.5)
            )
            self.db.add(assistant_message)
            
            # Update session
            session.total_messages += 2
            session.last_activity = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Chat response generated for user {user_id}, literature {literature_id}")
            
            return {
                "session_id": session.id,
                "question": question,
                "response": response["content"],
                "citations": response.get("citations", []),
                "confidence_score": response.get("confidence_score", 0.5)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in chat with paper: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during chat"
            )
    
    async def _generate_chat_response(self, literature: LiteratureSummary, 
                                    question: str) -> Dict[str, Any]:
        """Generate chat response using AI"""
        try:
            # Create context from literature
            context = self._create_chat_context(literature)
            
            # Create prompt
            prompt = f"""
            You are an AI research assistant. Answer the following question based ONLY on the provided paper content.
            If the information is not available in the paper, say "This information is not found in the paper."

            Paper Content:
            {context}

            Question: {question}

            Provide a clear, accurate answer based only on the paper content. Include relevant citations or sections where possible.
            """
            
            # Generate response using free AI service
            try:
                response_text = await self._call_free_ai(question, context)
                return {
                    "content": response_text,
                    "citations": [],
                    "confidence_score": 0.8
                }
            except Exception as e:
                logger.error(f"Free AI failed for chat: {str(e)}")
                
                # Fallback response
                return {
                    "content": "I'm sorry, but I cannot process your question at the moment due to technical issues. Please try again later.",
                    "citations": [],
                    "confidence_score": 0.0
                }
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return {
                "content": "An error occurred while processing your question.",
                "citations": [],
                "confidence_score": 0.0
            }
    
    def _create_chat_context(self, literature: LiteratureSummary) -> str:
        """Create context for chat from literature"""
        context_parts = []
        
        if literature.title:
            context_parts.append(f"Title: {literature.title}")
        
        if literature.authors:
            context_parts.append(f"Authors: {literature.authors}")
        
        if literature.abstract:
            context_parts.append(f"Abstract: {literature.abstract}")
        
        if literature.summary:
            context_parts.append(f"Summary: {literature.summary}")
        
        if literature.key_findings:
            context_parts.append(f"Key Findings: {', '.join(literature.key_findings)}")
        
        if literature.full_text:
            # Use first 3000 characters of full text
            context_parts.append(f"Full Text (excerpt): {literature.full_text[:3000]}...")
        
        return "\n\n".join(context_parts)
    
    async def list_literature_summaries(self, user_id: int, skip: int = 0, 
                                      limit: int = 20) -> Dict[str, Any]:
        """List user's literature summaries"""
        try:
            summaries = self.db.query(LiteratureSummary).filter(
                LiteratureSummary.user_id == user_id
            ).offset(skip).limit(limit).all()
            
            total = self.db.query(LiteratureSummary).filter(
                LiteratureSummary.user_id == user_id
            ).count()
            
            return {
                "summaries": [summary.to_dict() for summary in summaries],
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error listing literature summaries: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_chat_sessions(self, user_id: int, literature_id: int = None) -> Dict[str, Any]:
        """Get user's chat sessions"""
        try:
            query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)
            
            if literature_id:
                query = query.filter(ChatSession.literature_summary_id == literature_id)
            
            sessions = query.all()
            
            return {
                "sessions": [session.to_dict() for session in sessions]
            }
            
        except Exception as e:
            logger.error(f"Error getting chat sessions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def get_chat_messages(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """Get chat messages for a session"""
        try:
            # Verify session belongs to user
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).all()
            
            return {
                "session": session.to_dict(),
                "messages": [message.to_dict() for message in messages]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting chat messages: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

# Global literature service instance
literature_service = LiteratureService()