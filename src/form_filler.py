"""
Form Filler module for filling and submitting job applications
"""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from typing import Dict, List
import time
from loguru import logger
from pathlib import Path

try:
    import config
except ImportError:
    logger.error("config.py not found.")
    raise

from src.ai_assistant import AIAssistant


class FormFiller:
    """
    Fill job application forms using AI and browser automation
    """
    
    def __init__(self, page: Page, ai_assistant: AIAssistant):
        self.page = page
        self.ai = ai_assistant
        
    def fill_application(self, job: Dict, cv_data: Dict) -> Dict:
        """
        Fill and optionally submit a job application
        
        Args:
            job: Job dictionary with URL and details
            cv_data: Parsed CV data
            
        Returns:
            Dictionary with application result
        """
        result = {
            'job_id': job.get('url'),
            'job_title': job.get('title'),
            'company': job.get('company'),
            'success': False,
            'message': '',
            'submitted': False
        }
        
        try:
            logger.info(f"Starting application for {job.get('title')} at {job.get('company')}")
            
            # Navigate to job URL
            self.page.goto(job['url'], wait_until='domcontentloaded')
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # Take screenshot before
            if config.TAKE_SCREENSHOTS:
                self._take_screenshot('before_application')
            
            # Find and click apply button
            apply_button = self._find_apply_button()
            if not apply_button:
                result['message'] = 'Could not find apply button'
                logger.warning(f"No apply button found for {job.get('title')}")
                return result
            
            apply_button.click()
            time.sleep(config.PAGE_LOAD_DELAY)
            
            # Check if external application (redirects away)
            if self._is_external_application():
                result['message'] = 'External application (redirects to company site)'
                logger.info(f"External application detected: {job.get('title')}")
                return result
            
            # Fill the application form
            fill_result = self._fill_form(job, cv_data)
            
            if not fill_result['success']:
                result['message'] = fill_result['message']
                return result
            
            # Take screenshot after filling
            if config.TAKE_SCREENSHOTS:
                self._take_screenshot('after_filling')
            
            # Submit if auto-submit is enabled
            if config.AUTO_SUBMIT:
                submit_result = self._submit_application()
                result['submitted'] = submit_result['submitted']
                result['message'] = submit_result['message']
            else:
                result['message'] = 'Form filled, awaiting manual submission'
                logger.info("Auto-submit disabled, form filled but not submitted")
            
            result['success'] = True
            
        except Exception as e:
            result['message'] = f'Error: {str(e)}'
            logger.error(f"Error filling application: {e}")
        
        return result
    
    def _find_apply_button(self):
        """Find the apply button on the page"""
        # Common apply button selectors
        selectors = [
            'button:has-text("Apply")',
            'a:has-text("Apply")',
            'button:has-text("Apply now")',
            'a:has-text("Apply now")',
            'button[class*="apply"]',
            'a[class*="apply"]',
            '#indeedApplyButton',
            '.jobs-apply-button',
        ]
        
        for selector in selectors:
            try:
                button = self.page.locator(selector).first
                if button.is_visible(timeout=2000):
                    return button
            except:
                continue
        
        return None
    
    def _is_external_application(self) -> bool:
        """Check if the application redirects to an external site"""
        current_url = self.page.url
        
        # If we're no longer on the job board, it's external
        job_boards = ['indeed.com', 'linkedin.com', 'glassdoor.com']
        
        for board in job_boards:
            if board in current_url:
                return False
        
        return True
    
    def _fill_form(self, job: Dict, cv_data: Dict) -> Dict:
        """
        Fill the application form
        
        Returns:
            Dictionary with success status and message
        """
        result = {'success': False, 'message': ''}
        
        try:
            # Get form HTML
            form_html = self.page.content()
            
            # Use AI to analyze form fields
            field_mapping = self.ai.analyze_form_fields(form_html, cv_data)
            
            if not field_mapping.get('fields'):
                result['message'] = 'Could not analyze form fields'
                return result
            
            # Fill each field
            filled_count = 0
            for field in field_mapping['fields']:
                if self._fill_field(field):
                    filled_count += 1
            
            logger.info(f"Filled {filled_count} fields")
            
            # Handle file uploads (resume)
            self._upload_resume()
            
            result['success'] = True
            result['message'] = f'Successfully filled {filled_count} fields'
            
        except Exception as e:
            result['message'] = f'Error filling form: {str(e)}'
            logger.error(f"Form filling error: {e}")
        
        return result
    
    def _fill_field(self, field: Dict) -> bool:
        """
        Fill a single form field
        
        Args:
            field: Dictionary with field information from AI
            
        Returns:
            True if filled successfully
        """
        try:
            field_name = field.get('name', '')
            field_type = field.get('type', 'text')
            value = field.get('value', '')
            
            if not field_name or not value:
                return False
            
            # Find the input element
            selectors = [
                f'input[name="{field_name}"]',
                f'textarea[name="{field_name}"]',
                f'select[name="{field_name}"]',
                f'#{field_name}',
                f'[id*="{field_name}"]',
            ]
            
            element = None
            for selector in selectors:
                try:
                    elem = self.page.locator(selector).first
                    if elem.is_visible(timeout=1000):
                        element = elem
                        break
                except:
                    continue
            
            if not element:
                logger.debug(f"Could not find field: {field_name}")
                return False
            
            # Fill based on field type
            if field_type == 'text' or field_type == 'textarea':
                element.fill(str(value))
            elif field_type == 'select':
                element.select_option(label=str(value))
            elif field_type == 'checkbox':
                if str(value).lower() in ['true', 'yes', '1']:
                    element.check()
            
            logger.debug(f"Filled field: {field_name}")
            return True
            
        except Exception as e:
            logger.debug(f"Error filling field {field.get('name')}: {e}")
            return False
    
    def _upload_resume(self) -> bool:
        """Upload resume file if file input exists"""
        try:
            # Find file input for resume
            file_inputs = self.page.locator('input[type="file"]').all()
            
            if not file_inputs:
                return False
            
            resume_path = Path(config.RESUME_PATH)
            if not resume_path.exists():
                logger.warning("Resume file not found for upload")
                return False
            
            # Upload to first file input (usually resume)
            file_inputs[0].set_input_files(str(resume_path.absolute()))
            logger.info("Resume uploaded successfully")
            return True
            
        except Exception as e:
            logger.debug(f"Error uploading resume: {e}")
            return False
    
    def _submit_application(self) -> Dict:
        """
        Submit the application form
        
        Returns:
            Dictionary with submission result
        """
        result = {'submitted': False, 'message': ''}
        
        try:
            # Find submit button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Submit Application")',
                'button:has-text("Apply")',
                'input[type="submit"]',
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        submit_button = btn
                        break
                except:
                    continue
            
            if not submit_button:
                result['message'] = 'Could not find submit button'
                return result
            
            # Click submit
            submit_button.click()
            
            # Wait for submission to complete
            time.sleep(3)
            
            # Check for success message
            success_indicators = [
                'Application submitted',
                'Thank you',
                'Success',
                'application received',
            ]
            
            page_text = self.page.content().lower()
            for indicator in success_indicators:
                if indicator.lower() in page_text:
                    result['submitted'] = True
                    result['message'] = 'Application submitted successfully'
                    logger.info("Application submitted successfully")
                    return result
            
            # If we're on a confirmation page
            if 'confirmation' in self.page.url.lower() or 'success' in self.page.url.lower():
                result['submitted'] = True
                result['message'] = 'Application submitted (confirmation page detected)'
                return result
            
            result['message'] = 'Submit clicked but confirmation unclear'
            
        except Exception as e:
            result['message'] = f'Error submitting: {str(e)}'
            logger.error(f"Submission error: {e}")
        
        return result
    
    def _take_screenshot(self, prefix: str = 'screenshot'):
        """Take a screenshot for debugging"""
        try:
            screenshot_dir = Path('screenshots')
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.png"
            filepath = screenshot_dir / filename
            
            self.page.screenshot(path=str(filepath))
            logger.debug(f"Screenshot saved: {filepath}")
            
        except Exception as e:
            logger.debug(f"Error taking screenshot: {e}")
