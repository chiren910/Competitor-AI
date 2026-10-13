#llm_processing/llm_processor.py


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from llm_processing.prompt_templates import get_company_profile_prompt, get_comparison_table_prompt, get_competitor_analysis_prompt, get_market_size_prompt, get_market_share_prompt, get_surpass_recommendation_prompt, get_swot_analysis_prompt
from llm_processing.prompt_templates import get_detailed_competitor_profile_prompt
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
import logging
import json
import re

from utils.news_scraper import fetch_top_news_snippets

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProcessor:
    def __init__(self):
        # List of candidate models to fallback to in case of rate-limiting or quota exhaustion
        self.candidate_models = [
            GEMINI_MODEL,
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
        ]
        # Remove duplicates while preserving priority order
        seen = set()
        self.candidate_models = [m for m in self.candidate_models if not (m in seen or seen.add(m))]
        self._chats = {}
        for m in self.candidate_models:
            self._chats[m] = ChatGoogleGenerativeAI(
                model=m,
                google_api_key=GEMINI_API_KEY,
                temperature=0.1,  # Low temperature for consistent, factual responses
            )
        self.chat = self._chats[self.candidate_models[0]]
    
    async def process_with_gemini(self, prompt):
        """Generic method to process a prompt with Gemini with automatic multi-model fallback"""
        last_exception = None
        for model_name in self.candidate_models:
            chat = self._chats.get(model_name)
            if not chat:
                chat = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=GEMINI_API_KEY,
                    temperature=0.1,
                )
                self._chats[model_name] = chat

            try:
                logger.info(f"Sending prompt to Gemini model '{model_name}' (length: {len(prompt)})")
                response = chat.invoke([HumanMessage(content=prompt)])
                logger.info(f"Received response from Gemini model '{model_name}'")

                if response and hasattr(response, 'content'):
                    content = response.content
                    logger.info(f"Response sample from {model_name}: {str(content)[:100]}...")

                    if isinstance(content, dict):
                        return content

                    if isinstance(content, list):
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                text_parts.append(item["text"])
                            elif isinstance(item, str):
                                text_parts.append(item)
                        content = "\n".join(text_parts)

                    if isinstance(content, str):
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            json_block_match = re.search(r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```", content, re.DOTALL)
                            if json_block_match:
                                try:
                                    extracted_json = json_block_match.group(1)
                                    return json.loads(extracted_json)
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse extracted JSON block from {model_name}: {e}")
                                    return {
                                        "error": "Failed to parse extracted JSON block",
                                        "raw_content": content
                                    }

                            logger.warning(f"No valid JSON block found in response from {model_name}")
                            return {"error": "Failed to extract valid JSON from response", "raw_content": content}

                    return {"error": f"Unexpected response type: {type(content)}"}

                else:
                    logger.warning(f"Invalid response structure from model '{model_name}'. Trying next model.")
                    continue

            except Exception as e:
                err_str = str(e)
                logger.warning(f"Model '{model_name}' failed ({err_str[:120]}). Trying fallback model...")
                last_exception = e
                continue

        logger.error(f"All Gemini models exhausted. Last error: {last_exception}")
        return {"error": "All Gemini models failed", "exception": str(last_exception)}

    async def get_competitor_analysis(self, company_profile: dict, market_data: dict, competitors: list) -> dict:
        """
        Run a competitor analysis using company profile, market data, and competitor list.
        """
        try:
            logger.info("Generating competitor analysis prompt")
            prompt = get_competitor_analysis_prompt(company_profile, market_data, competitors)
            logger.info("Sending competitor analysis prompt to Gemini")
            return await self.process_with_gemini(prompt)
        except Exception as e:
            logger.error(f"Exception in get_competitor_analysis: {e}")
            return {"error": "Error during competitor analysis", "exception": str(e)}

    async def extract_company_info(self, html_content: str) -> dict:
        """Extract company information from website content"""
        try:
            # Check if HTML content is valid
            if not html_content or len(html_content.strip()) < 100:
                logger.warning("HTML content is too limited for meaningful extraction")
                return {"error": "Limited website content available", "content_length": len(html_content) if html_content else 0}
            
            # Prepare the prompt for company profile extraction
            prompt = get_company_profile_prompt(html_content)
            
            # Process with Gemini
            return await self.process_with_gemini(prompt)
            
        except Exception as e:
            logger.error(f"Exception in extract_company_info: {e}")
            return {"error": "Error during extraction process", "exception": str(e)}

    async def get_market_size(self, company_profile: dict) -> dict:
        """Get market size information based on company profile"""
        try:
            # Prepare the prompt for market size analysis
            prompt = get_market_size_prompt(company_profile)
            
            # Process with Gemini
            return await self.process_with_gemini(prompt)
            
        except Exception as e:
            logger.error(f"Exception in get_market_size: {e}")
            return {"error": "Error during market size analysis", "exception": str(e)}

    async def get_market_share(self, company_profile: dict, market_data: dict) -> dict:
        """Get market share information based on company profile and market data"""
        try:
            # Prepare the prompt for market share analysis
            prompt = get_market_share_prompt(company_profile, market_data)
            
            # Process with Gemini
            return await self.process_with_gemini(prompt)
            
        except Exception as e:
            logger.error(f"Exception in get_market_share: {e}")
            return {"error": "Error during market share analysis", "exception": str(e)}
    async def run_market_analysis_with_news(self, company_profile: dict) -> dict:
        """
        Combines company profile with latest industry news to produce a full market analysis.
        Returns structured JSON with market size, growth, top players, etc.
        """
        try:
            category = company_profile.get("category", "")
            if not category:
                # Fallback: use company name + description to build a search query
                name = company_profile.get("name", "")
                desc = company_profile.get("description", "")
                category = name or desc or "technology industry"
                logger.warning(f"Missing category in company profile. Using fallback: '{category}'")

            # Step 1: Fetch industry news
            logger.info(f"Fetching news for category: {category}")
            news_snippets = fetch_top_news_snippets(category)

            # Step 2: Generate prompt
            logger.info("Generating prompt for market analysis")
            prompt = get_market_size_prompt(company_profile, news_snippets)

            # Step 3: Send to Gemini
            logger.info("Sending market analysis prompt to Gemini")
            return await self.process_with_gemini(prompt)

        except Exception as e:
            logger.error(f"Exception in run_market_analysis_with_news: {e}")
            return {"error": "Error during market analysis with news", "exception": str(e)}
    
    async def generate_competitor_list(self, company_profile: dict, market_data: dict) -> list:
        """
        Generate a list of competitors (local, national, global) using Gemini.
        Returns a list of dictionaries with keys: competitor_name, description, link.
        """
        try:
            prompt = f"""
    You are a market research assistant. Based on the company profile and market data below, identify 11 competitors:
    - 5 local competitors (same city or region)
    - 3 national competitors (same country)
    - 3 global competitors (international)

    Company Profile:
    Name: {company_profile.get('name')}
    Category: {company_profile.get('category')}
    Location: {company_profile.get('location')}
    Services: {', '.join(company_profile.get('services', [])) if isinstance(company_profile.get('services'), list) else company_profile.get('services')}
    Industries: {', '.join(company_profile.get('industries', [])) if isinstance(company_profile.get('industries'), list) else company_profile.get('industries')}

    Market:
    Sector: {market_data.get('sector')}
    Regions: {', '.join(market_data.get('major_regions', []))}

    Return a JSON list with only these 3 keys:
    [
    {{
        "competitor_name": "Example Co",
        "description": "What this company does",
        "link": "https://example.com"
    }},
    ...
    ]

    Only return valid JSON, no markdown, no explanations.
    """
            response = await self.process_with_gemini(prompt)
            if isinstance(response, list):
                return response
            if isinstance(response, dict) and 'error' in response:
                return []
            return json.loads(response) if isinstance(response, str) else []
        except Exception as e:
            logger.error(f"Error generating competitor list: {e}")
            return []
    async def analyze_single_competitor(self, competitor_text: str, our_profile: dict) -> dict:
        try:
            prompt = get_detailed_competitor_profile_prompt(competitor_text, our_profile)
            return await self.process_with_gemini(prompt)
        except Exception as e:
            logger.error(f"Error analyzing single competitor: {e}")
            return {"error": str(e)}
        
    async def generate_swot_analysis(self, our_profile: dict, competitors: list) -> dict:
        try:
            prompt = get_swot_analysis_prompt(our_profile, competitors)
            return await self.process_with_gemini(prompt)
        except Exception as e:
            logger.error(f"Error generating SWOT analysis: {e}")
            return {"error": str(e)}

    async def generate_comparison_table(self, our_profile: dict, competitors: list) -> dict:
        try:
            prompt = get_comparison_table_prompt(our_profile, competitors)
            return await self.process_with_gemini(prompt)
        except Exception as e:
            logger.error(f"Error generating comparison table: {e}")
            return {"error": str(e)}
    async def generate_surpass_recommendations(self, our_profile: dict, competitors: list) -> dict:
        try:
            prompt = get_surpass_recommendation_prompt(our_profile, competitors)
            return await self.process_with_gemini(prompt)
        except Exception as e:
            logger.error(f"Error generating surpass recommendations: {e}")
            return {"error": str(e)}