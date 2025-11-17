"""
AI Assistant module using Claude API for intelligent form filling
"""

import anthropic
from typing import Dict, List, Optional
import json
from loguru import logger

try:
    import config
except ImportError:
    logger.error("config.py not found. Copy config.example.py to config.py and fill in your details.")
    raise


class AIAssistant:
    """
    AI Assistant using Claude to understand and fill job application forms
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL
        
    def analyze_form_fields(self, form_html: str, cv_data: Dict) -> Dict:
        """
        Analyze form fields and determine what information is needed
        
        Args:
            form_html: HTML content of the form
            cv_data: Parsed CV/resume data
            
        Returns:
            Dictionary with field mappings
        """
        prompt = f"""You are helping fill out a job application form. 

Here is the form HTML:
<form_html>
{form_html[:5000]}  # Limit to avoid token limits
</form_html>

Here is the candidate's information from their CV:
<cv_data>
{json.dumps(cv_data, indent=2)}
</cv_data>

Analyze the form and return a JSON object mapping each form field to:
1. The appropriate value from the CV data
2. If it's a required field
3. The field type (text, select, checkbox, etc.)

Return ONLY valid JSON, no other text. Format:
{{
  "fields": [
    {{
      "name": "field_name",
      "label": "field_label",
      "type": "text|select|checkbox|textarea",
      "required": true|false,
      "value": "value from CV data or appropriate response",
      "confidence": "high|medium|low"
    }}
  ]
}}

For questions like "Why do you want this job?", provide a brief, professional response.
For salary expectations, use the minimum from CV data or respond "Negotiable".
For work authorization questions, use the provided authorization info.
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            
            result = json.loads(response_text.strip())
            logger.info(f"Analyzed {len(result.get('fields', []))} form fields")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing form: {e}")
            return {"fields": []}
    
    def generate_cover_letter(self, job_description: str, cv_data: Dict, 
                            company_name: str, position: str) -> str:
        """
        Generate a tailored cover letter for the job
        
        Args:
            job_description: The job posting description
            cv_data: Parsed CV/resume data
            company_name: Name of the company
            position: Job position title
            
        Returns:
            Generated cover letter text
        """
        prompt = f"""Write a professional cover letter for this job application.

Company: {company_name}
Position: {position}

Job Description:
{job_description[:2000]}

Candidate Background:
{json.dumps(cv_data, indent=2)}

Write a concise, professional cover letter (250-300 words) that:
1. Shows enthusiasm for the role
2. Highlights relevant experience from the candidate's background
3. Explains why they're a good fit
4. Maintains a professional but warm tone

Return only the cover letter text, no additional commentary.
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            cover_letter = message.content[0].text.strip()
            logger.info(f"Generated cover letter for {position} at {company_name}")
            return cover_letter
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return ""
    
    def answer_screening_question(self, question: str, cv_data: Dict, 
                                 context: Optional[str] = None) -> str:
        """
        Answer a screening question intelligently
        
        Args:
            question: The screening question
            cv_data: Parsed CV/resume data
            context: Additional context about the job
            
        Returns:
            Answer to the question
        """
        prompt = f"""Answer this job application screening question professionally.

Question: {question}

Candidate Background:
{json.dumps(cv_data, indent=2)}

{"Job Context: " + context if context else ""}

Provide a clear, concise, and honest answer (2-3 sentences).
If the answer should be Yes/No, start with that.
Return only the answer, no additional commentary.
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = message.content[0].text.strip()
            logger.info(f"Answered screening question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return ""
    
    def should_apply_to_job(self, job_description: str, job_title: str, 
                          cv_data: Dict, preferences: Dict) -> Dict:
        """
        Determine if the candidate should apply to this job
        
        Args:
            job_description: Full job description
            job_title: Job title
            cv_data: Parsed CV/resume data
            preferences: User's job preferences
            
        Returns:
            Dictionary with decision and reasoning
        """
        prompt = f"""Analyze if this candidate should apply to this job.

Job Title: {job_title}

Job Description:
{job_description[:3000]}

Candidate Background:
{json.dumps(cv_data, indent=2)}

Candidate Preferences:
{json.dumps(preferences, indent=2)}

Analyze the match and return a JSON object:
{{
  "should_apply": true|false,
  "match_score": 0-100,
  "reasoning": "brief explanation",
  "pros": ["list", "of", "matching", "points"],
  "cons": ["list", "of", "concerns"]
}}

Consider:
1. Skills match
2. Experience level match
3. Location/remote preferences
4. Salary expectations
5. Company culture fit indicators

Return ONLY valid JSON, no other text.
"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            
            result = json.loads(response_text.strip())
            logger.info(f"Job match score: {result.get('match_score', 0)}/100")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing job match: {e}")
            return {
                "should_apply": False,
                "match_score": 0,
                "reasoning": "Error analyzing job",
                "pros": [],
                "cons": ["Analysis failed"]
            }
