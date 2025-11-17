"""
CV Parser module to extract information from resume files
"""

import PyPDF2
import docx
import pdfplumber
import re
from typing import Dict, List
from pathlib import Path
from loguru import logger

try:
    import config
except ImportError:
    logger.error("config.py not found. Copy config.example.py to config.py.")
    raise


class CVParser:
    """
    Parse resume/CV files to extract structured information
    """
    
    def __init__(self, resume_path: str = None):
        self.resume_path = resume_path or config.RESUME_PATH
        self.cv_data = {}
        
    def parse(self) -> Dict:
        """
        Parse the resume file and extract information
        
        Returns:
            Dictionary with structured CV data
        """
        resume_path = Path(self.resume_path)
        
        if not resume_path.exists():
            logger.error(f"Resume file not found: {self.resume_path}")
            return self._get_fallback_data()
        
        # Extract text based on file type
        if resume_path.suffix.lower() == '.pdf':
            text = self._extract_from_pdf(str(resume_path))
        elif resume_path.suffix.lower() in ['.docx', '.doc']:
            text = self._extract_from_docx(str(resume_path))
        else:
            logger.error(f"Unsupported file format: {resume_path.suffix}")
            return self._get_fallback_data()
        
        # Parse the extracted text
        self.cv_data = self._parse_text(text)
        
        # Add personal info from config
        self.cv_data['personal_info'] = config.PERSONAL_INFO
        self.cv_data['work_authorization'] = config.WORK_AUTHORIZATION
        self.cv_data['preferences'] = config.JOB_PREFERENCES
        
        logger.info("Successfully parsed resume")
        return self.cv_data
    
    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        
        try:
            # Try with pdfplumber first (better formatting)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
            except Exception as e2:
                logger.error(f"Failed to extract PDF text: {e2}")
                
        return text
    
    def _extract_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(docx_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Failed to extract DOCX text: {e}")
            return ""
    
    def _parse_text(self, text: str) -> Dict:
        """
        Parse extracted text to find structured information
        
        This is a simplified parser. For production, consider using
        an NLP library or AI model for better extraction.
        """
        cv_data = {
            'raw_text': text,
            'skills': self._extract_skills(text),
            'experience': self._extract_experience(text),
            'education': self._extract_education(text),
            'summary': self._extract_summary(text),
        }
        
        return cv_data
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common skill keywords
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI',
            'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'Git', 'CI/CD', 'Jenkins', 'GitHub Actions',
            'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
            'API', 'REST', 'GraphQL', 'Microservices',
            'Agile', 'Scrum', 'TDD', 'Unit Testing'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from resume text"""
        # This is a simplified version
        # In production, use more sophisticated parsing
        
        experience = []
        
        # Look for date patterns (e.g., "2020 - 2023", "Jan 2020 - Present")
        date_pattern = r'(\d{4}|\w{3}\s+\d{4})\s*[-–]\s*(Present|\d{4}|\w{3}\s+\d{4})'
        matches = re.finditer(date_pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Extract context around the date (potential job info)
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(text), match.end() + 200)
            context = text[start_pos:end_pos]
            
            experience.append({
                'date_range': match.group(0),
                'context': context.strip()
            })
        
        return experience[:5]  # Limit to 5 most recent
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education from resume text"""
        education = []
        
        # Common degree keywords
        degree_keywords = [
            'Bachelor', 'Master', 'PhD', 'B.S.', 'M.S.', 'B.A.', 'M.A.',
            'Computer Science', 'Engineering', 'Mathematics'
        ]
        
        lines = text.split('\n')
        for line in lines:
            for keyword in degree_keywords:
                if keyword.lower() in line.lower():
                    education.append(line.strip())
                    break
        
        return education[:3]  # Limit to 3
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary from resume"""
        # Look for summary/objective section
        lines = text.split('\n')
        summary_keywords = ['summary', 'objective', 'about', 'profile']
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Get next few lines as summary
                summary_lines = lines[i+1:i+5]
                return ' '.join(summary_lines).strip()
        
        # If no summary section, return first few lines
        return ' '.join(lines[:3]).strip()
    
    def _get_fallback_data(self) -> Dict:
        """
        Return fallback data using config information when resume can't be parsed
        """
        logger.warning("Using fallback CV data from config")
        
        return {
            'personal_info': config.PERSONAL_INFO,
            'work_authorization': config.WORK_AUTHORIZATION,
            'preferences': config.JOB_PREFERENCES,
            'skills': config.KEYWORDS,
            'experience': [],
            'education': [],
            'summary': 'Experienced professional seeking new opportunities',
            'raw_text': ''
        }
    
    def get_cv_data(self) -> Dict:
        """Get the parsed CV data"""
        if not self.cv_data:
            self.parse()
        return self.cv_data
