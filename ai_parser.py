"""
AI-powered obligation extraction using Google Gemini
Parses agreement text and returns structured obligation data
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_gemini_api_key():
    """
    Get Gemini API key from either:
    1. Streamlit Secrets (st.secrets) - for Streamlit Cloud
    2. Environment variable (os.getenv) - for local/Docker
    """
    try:
        # Try Streamlit Secrets first (for Streamlit Cloud)
        import streamlit as st
        if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
            api_key = st.secrets['GEMINI_API_KEY']
            logger.info(f"DEBUG: API key loaded from Streamlit Secrets")
            return api_key
    except Exception as e:
        logger.debug(f"Could not read Streamlit Secrets: {e}")
    
    # Fallback to environment variable (for local/Docker)
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        logger.info(f"DEBUG: API key loaded from environment variable")
    
    return api_key


class GeminiObligationParser:
    """Extract vendor obligations using Google Gemini"""

    def __init__(self):
        """Initialize Gemini model"""
        logger.info(f"DEBUG: Initializing GeminiObligationParser...")
        api_key = get_gemini_api_key()
        
        # Debug logging
        if api_key:
            logger.info(f"DEBUG: API key found! Length: {len(api_key)}, First 10 chars: {api_key[:10]}...")
            if not api_key.startswith('AIza'):
                logger.warning(f"DEBUG: API key looks unusual - doesn't start with 'AIza'. Starts with: {api_key[:10]}")
        else:
            logger.error("DEBUG: GEMINI_API_KEY not found in Streamlit Secrets or environment!")
            raise ValueError("GEMINI_API_KEY not set. Please set it in Streamlit Secrets (Streamlit Cloud) or as an environment variable (local/Docker).")
        
        logger.info(f"Initializing Gemini with API key: {api_key[:10]}...")
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {type(e).__name__}: {e}", exc_info=True)
            raise ValueError(f"Failed to initialize Gemini API: {e}")

    def extract_obligations(self, agreement_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract vendor obligations from agreement text using Gemini
        
        Args:
            agreement_text: Raw text from agreement document
            
        Returns:
            Dictionary with parsed obligations or None if extraction failed
        """
        if not agreement_text or not agreement_text.strip():
            return None
        
        # Construct structured prompt for Gemini
        prompt = f"""
You are a vendor contract analyst. Extract vendor obligations from the agreement text below.
Return ONLY valid JSON with no additional text. If a field is not found, use null.

Agreement Text:
{agreement_text}

Return JSON with exactly these fields:
{{
    "agreement_type": "Type of agreement (e.g., Service Agreement, NDA, etc.)",
    "agreement_term": "Duration or term of agreement (e.g., 12 months, 3 years)",
    "scope_of_work": "Services or deliverables included",
    "service_levels": "SLAs and performance standards",
    "penalties_for_breach": "Penalties or remedies for non-compliance",
    "reporting_obligations": "Reporting frequency and format requirements",
    "servicing_obligations": "Support and maintenance obligations",
    "kpis_or_volume_commitments": "KPIs, volume commitments, or performance metrics",
    "data_security_protocols": "Data security and privacy requirements",
    "payment_obligations": "Payment terms and conditions",
    "milestone_completion": "Key milestones or deliverable dates",
    "dependencies": "Dependencies or prerequisites",
    "billing_status": "Billing frequency and arrangement (monthly, quarterly, annual, etc.)"
}}

Be concise and extract only relevant information from the agreement.
"""
        
        try:
            logger.debug(f"Sending request to Gemini API with {len(agreement_text)} characters")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048
                )
            )
            
            if not response.text:
                logger.error("Empty response from Gemini API - check if API key is valid")
                return None
            
            logger.debug(f"Gemini response: {response.text[:500]}...")
            
            # Parse JSON response
            parsed = self._parse_json_response(response.text)
            if parsed:
                logger.info(f"Successfully parsed obligations: {list(parsed.keys())}")
            else:
                logger.warning("JSON parsing returned None")
            return parsed
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {type(e).__name__}: {e}", exc_info=True)
            logger.error("This usually means: 1) API key is invalid, 2) API quota exceeded, 3) Network error")
            return None

    @staticmethod
    def _parse_json_response(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from Gemini response, handling various formats and incomplete data
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed JSON dictionary or None if parsing failed
        """
        try:
            # Try direct JSON parsing first
            logger.debug("Attempting direct JSON parse...")
            result = json.loads(response_text)
            logger.info("Successfully parsed JSON directly")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")
        
        # Try to extract JSON from markdown code blocks
        try:
            json_str = None
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
                logger.debug("Extracting JSON from markdown code block")
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
                logger.debug("Extracting JSON from generic code block")
            
            if json_str:
                try:
                    result = json.loads(json_str)
                    logger.info("Successfully parsed markdown block as JSON")
                    return result
                except json.JSONDecodeError as e:
                    logger.debug(f"Markdown block JSON parsing failed: {e}")
                    # Try to fix incomplete JSON in markdown block
                    fixed_json = GeminiObligationParser._fix_incomplete_json(json_str)
                    if fixed_json:
                        try:
                            result = json.loads(fixed_json)
                            logger.info("Successfully parsed fixed markdown block JSON")
                            return result
                        except json.JSONDecodeError:
                            logger.debug("Could not parse even after fixing")
        except (IndexError, json.JSONDecodeError) as e:
            logger.debug(f"Markdown block extraction failed: {e}")
        
        # Try to extract JSON object from response
        try:
            logger.debug("Attempting to extract JSON object from response...")
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                logger.debug(f"Found JSON between positions {start_idx}-{end_idx}")
                
                try:
                    result = json.loads(json_str)
                    logger.info("Successfully parsed extracted JSON object")
                    return result
                except json.JSONDecodeError:
                    # Try to fix incomplete JSON
                    fixed_json = GeminiObligationParser._fix_incomplete_json(json_str)
                    if fixed_json:
                        try:
                            result = json.loads(fixed_json)
                            logger.info("Successfully parsed fixed JSON object")
                            return result
                        except json.JSONDecodeError:
                            logger.debug("Could not parse even after fixing")
        except (IndexError, json.JSONDecodeError) as e:
            logger.debug(f"JSON object extraction failed: {e}")
        
        logger.error("Could not parse Gemini response as JSON")
        logger.error(f"Response text: {response_text[:300]}...")
        return None

    @staticmethod
    def _fix_incomplete_json(json_str: str) -> Optional[str]:
        """
        Attempt to fix incomplete or malformed JSON strings
        
        Common issues:
        - Unterminated strings (ending with "...")
        - Missing closing braces
        - Incomplete values
        
        Args:
            json_str: Potentially incomplete JSON string
            
        Returns:
            Fixed JSON string or None if unfixable
        """
        logger.debug("Attempting to fix incomplete JSON...")
        
        try:
            # Count braces to see if we need to close
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            
            if open_braces > close_braces:
                # Add missing closing braces
                json_str = json_str.rstrip() + '}' * (open_braces - close_braces)
                logger.debug(f"Added {open_braces - close_braces} closing braces")
            
            # Fix unterminated strings (e.g., ending with "...")
            # Look for strings that end with "..." and close them properly
            import re
            
            # Replace incomplete string endings like "..." with proper value
            json_str = re.sub(r':\s*"[^"]*\.\.\."', ': null', json_str)
            json_str = re.sub(r':\s*"[^"]*\.\.\.$', ': null', json_str)
            
            # Try to parse the fixed JSON
            result = json.loads(json_str)
            logger.info("Successfully fixed and parsed JSON")
            return json_str
        except Exception as e:
            logger.debug(f"Could not fix JSON: {e}")
            return None

    def extract_with_fallback(self, agreement_text: str) -> Dict[str, Any]:
        """
        Extract obligations with fallback to empty structure if Gemini fails
        
        Args:
            agreement_text: Raw text from agreement
            
        Returns:
            Obligations dictionary with parsed data or empty fields
        """
        logger.info("Starting obligation extraction with fallback...")
        result = self.extract_obligations(agreement_text)
        
        if result is None:
            logger.warning("Extraction failed, returning empty structure")
            logger.warning("IMPORTANT: Make sure GEMINI_API_KEY is set in Streamlit Cloud Secrets!")
            # Return empty structure if extraction failed
            result = {
                "agreement_type": None,
                "agreement_term": None,
                "scope_of_work": None,
                "service_levels": None,
                "penalties_for_breach": None,
                "reporting_obligations": None,
                "servicing_obligations": None,
                "kpis_or_volume_commitments": None,
                "data_security_protocols": None,
                "payment_obligations": None,
                "milestone_completion": None,
                "dependencies": None,
                "billing_status": None
            }
        else:
            logger.info(f"Extraction successful. Fields extracted:")
            for key, value in result.items():
                if value:
                    logger.info(f"  {key}: {str(value)[:80]}...")
        
        return result

    @staticmethod
    def get_obligation_summary(obligations: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of obligations
        
        Args:
            obligations: Parsed obligations dictionary
            
        Returns:
            Formatted summary string
        """
        summary_parts = []
        
        if obligations.get('agreement_type'):
            summary_parts.append(f"📋 Type: {obligations['agreement_type']}")
        
        if obligations.get('agreement_term'):
            summary_parts.append(f"📅 Term: {obligations['agreement_term']}")
        
        if obligations.get('scope_of_work'):
            summary_parts.append(f"🎯 Scope: {obligations['scope_of_work']}")
        
        if obligations.get('service_levels'):
            summary_parts.append(f"⚡ SLAs: {obligations['service_levels']}")
        
        if obligations.get('payment_obligations'):
            summary_parts.append(f"💰 Payment: {obligations['payment_obligations']}")
        
        if obligations.get('data_security_protocols'):
            summary_parts.append(f"🔒 Security: {obligations['data_security_protocols']}")
        
        return "\n".join(summary_parts) if summary_parts else "No obligations extracted"
