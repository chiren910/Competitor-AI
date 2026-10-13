#llm_processing/prompt_templates.py

import json

def get_company_profile_prompt(website_text: str) -> str:
    return f"""You are an intelligent agent that extracts structured company profile information from raw web page content.

    Given the following HTML/text:
    \"\"\"
    {website_text}
    \"\"\"

    Extract all relevant company information you can find and organize it into a JSON format.

    Required fields (must be included with either a value or null):
    - name: The company's full name
    - description: A concise description of what the company does
    - location: Company's headquarters location
    - founded_year: When the company was founded
    - category: The high-level business category (e.g., IT Consultancy, Transportation, Healthcare, Manufacturing, Education, Financial Services, etc.)
    - created_at: The timestamp when this profile was created
    - link: Company website URL or domain

    Dynamic fields (include only if found in the text):
    - icon: URL to company icon/logo
    - tagline: Company's main slogan or tagline
    - elevator_pitch: A brief summary of the company's value proposition
    - industries: List of industries the company operates in
    - services: List of services offered by the company
    - technologies: Technologies or platforms the company works with
    - team_size: Number of employees or team members
    - key_people: List of key executives with their names and roles
    - certifications: Any certifications or accreditations
    - clients: Notable clients mentioned
    - contact_info: Contact information like phone, email, etc.
    - social_media: Social media links
    - awards: Any awards or recognitions mentioned

    Return only a clean, structured JSON response with no explanations or additional text.
    """
def get_market_size_prompt(company_profile: dict, news_snippets: list) -> str:
    news_formatted = "\n".join(f"- {item}" for item in news_snippets) if news_snippets else "No relevant news found."

    return f"""
    You are a market research analyst with expertise in industry sizing and growth analysis.

    Company Profile:
    Company Name: {company_profile.get('name', 'Unknown')}
    Business Description: {company_profile.get('description', 'Unknown')}
    Industry/Category: {company_profile.get('category', 'Unknown')}
    Services Offered: {', '.join(company_profile.get('services', [])) if isinstance(company_profile.get('services'), list) else company_profile.get('services', 'Unknown')}
    Industries Served: {', '.join(company_profile.get('industries', [])) if isinstance(company_profile.get('industries'), list) else company_profile.get('industries', 'Unknown')}

    Recent Industry News:
    {news_formatted}

    Using the company profile and the latest industry developments, provide:

    - The specific name of the sector (e.g., Global IT Services, Indian SaaS Market)
    - Estimated total market size in financial units (not raw numbers)
    - Current annual growth rate (%)
    - Key growth drivers
    - Major regions or countries where the market is concentrated
    - Top 4-5 players in the market with market shares (if available)
    - 5-year forecast (estimated market size + CAGR)

    Format your response strictly as a valid JSON object like this:

    {{
      "sector": "Example: Global IT Services Market",
      "total_market_size": {{
        "value": "1.38 trillion USD",
        "year": 2024
      }},
      "growth_rate": {{
        "percentage": 5.5,
        "period": "annual"
      }},
      "key_drivers": ["...", "..."],
      "major_regions": ["...", "..."],
      "top_companies": [
        {{
          "name": "Company A",
          "market_share": "15%"
        }},
        ...
      ],
      "forecast": {{
        "year_5": {{
          "value": "1.8 trillion USD"
        }},
        "cagr": 5.5
      }}
    }}

    Do not use large raw integers; always format values using units like million/billion USD or crore/lakh INR.
    """


def get_market_share_prompt(company_profile: dict, market_data: dict) -> str:
    return f"""You are a financial and business growth strategist.

    Your task is to evaluate the company's estimated market capture and provide focused recommendations for scaling and competitive advantage.

    Use the following data:

    Company Profile:
    Name: {company_profile.get('name', 'Unknown')}
    Description: {company_profile.get('description', 'Unknown')}
    Category: {company_profile.get('category', 'Unknown')}
    Services: {', '.join(company_profile.get('services', [])) if isinstance(company_profile.get('services'), list) else company_profile.get('services', 'Unknown')}
    Team Size: {company_profile.get('team_size', 'Unknown')}
    Founded Year: {company_profile.get('founded_year', 'Unknown')}

    Market Data:
    Sector: {market_data.get('sector', 'Unknown')}
    Total Market Size: {market_data.get('total_market_size', {}).get('value', 'Unknown')} ({market_data.get('total_market_size', {}).get('year', '')})
    Growth Rate: {market_data.get('growth_rate', {}).get('percentage', 'Unknown')}% annually

    Your analysis must include:

    1. **Market Capture Estimate**:
       - Estimated % of market this company captures
       - Confidence level: high / medium / low
       - Clear, concise rationale for estimation (based on team size, services, geography, etc.)

    2. **Current Position Evaluation**:
       - Key strengths: based on profile, team, services, technology,news
       - Key challenges: what may limit growth or scalability

    3. **Strategic Growth Recommendations**:
       a. Vertical Scaling: strategies to deepen capabilities or increase revenue per client (e.g., specialization, pricing, IP)
       b. Horizontal Scaling: strategies to expand reach or diversify (e.g., new markets, services, partnerships)

    Output must be a clean, structured JSON like this:

    {{
        "market_capture": {{
            "percentage": 0.0,
            "confidence_level": "high/medium/low",
            "basis": "Clear explanation"
        }},
        "current_position": {{
            "strengths": ["strength1", "strength2", ...],
            "challenges": ["challenge1", "challenge2", ...]
        }},
        "growth_recommendations": {{
            "vertical_scaling": [
                {{
                    "strategy": "Strategy Title",
                    "description": "Short explanation",
                    "potential_impact": "high/medium/low"
                }},
                ...
            ],
            "horizontal_scaling": [
                {{
                    "strategy": "Strategy Title",
                    "description": "Short explanation",
                    "potential_impact": "high/medium/low"
                }},
                ...
            ]
        }}
    }}

    Keep all responses practical, concise, and based on the company and market context. Do not make assumptions beyond the data.
    """

def get_competitor_analysis_prompt(company_profile: dict, market_data: dict, competitors: list[dict]) -> str:
    def format_competitor_entries(competitor_list: list[dict]) -> str:
        return ",\n".join([
                f"""{{
        "competitor_name": "{c.get('competitor_name', 'Unknown')}",
        "description": "{c.get('description', 'No description available.')}",
        "link": "{c.get('link', '')}"
    }}"""
                for c in competitor_list
            ])

    return f"""You are a strategic market analyst with expertise in competitive intelligence.

    Using the following company and market data, provide a competitor analysis output structured by competition level: local, national, and global.

    Company Profile:
    \"\"\"
    Name: {company_profile.get('name', 'Unknown')}
    Category: {company_profile.get('category', 'Unknown')}
    Services: {', '.join(company_profile.get('services', [])) if isinstance(company_profile.get('services'), list) else company_profile.get('services', 'Unknown')}
    Industries: {', '.join(company_profile.get('industries', [])) if isinstance(company_profile.get('industries'), list) else company_profile.get('industries', 'Unknown')}
    Location: {company_profile.get('location', 'Unknown')}
    \"\"\"

    Market:
    \"\"\"
    Sector: {market_data.get('sector', 'Unknown')}
    Regions: {', '.join(market_data.get('major_regions', []))}
    \"\"\"

    Competitor Data (grouped by region):
    {{
    "local_competition": [
        {format_competitor_entries(competitors[:5])}
    ],
    "national_competition": [
        {format_competitor_entries(competitors[5:8])}
    ],
    "global_competition": [
        {format_competitor_entries(competitors[8:])}
    ]
    }}

    Only return a valid JSON object with keys: competitor_name, description, and link. Do not include any explanations, markdown, or extra fields.
    """
def get_detailed_competitor_profile_prompt(plain_text: str, our_profile: dict) -> str:
    return f"""
    You are a competitive intelligence agent.

    Given the following text from a competitor's website:
    \"\"\"
    {plain_text}
    \"\"\"

    And our company profile:
    \"\"\"
    {json.dumps(our_profile, indent=2)}
    \"\"\"

    Extract a structured company profile of the competitor. Then compare it with our company across fields like:
    - Services
    - Technologies
    - Team Size
    - Industries
    - Positioning

    Return only valid JSON like this:
    {{
    "profile": {{
        "name": "...",
        "description": "...",
        "location": "...",
        "services": [...],
        ...
    }},
    "comparison": {{
        "strengths": ["...", "..."],
        "weaknesses": ["...", "..."],
        "field_comparison": {{
        "services": "...",
        "technologies": "...",
        ...
        }}
    }}
    }}
    """

def get_swot_analysis_prompt(our_profile: dict, competitors: list) -> str:
    return f"""
            You are a strategic analyst.

            Given the following company profile:
            {json.dumps(our_profile, indent=2)}

            And the following competitors (filtered to those at par or ahead):
            {json.dumps(competitors, indent=2)}

            For each entity (our company and each competitor), provide a SWOT analysis with:
            - strengths
            - weaknesses
            - opportunities
            - threats

            Return a JSON object structured like this:

            {{
            "swot_analysis": {{
                "our_company": {{
                "strengths": [...],
                "weaknesses": [...],
                "opportunities": [...],
                "threats": [...]
                }},
                "competitors": [
                {{
                    "competitor_name": "...",
                    "swot": {{
                    "strengths": [...],
                    "weaknesses": [...],
                    "opportunities": [...],
                    "threats": [...]
                    }}
                }},
                ...
                ]
            }}
            }}

            Only return JSON; no extra text.
"""
def get_comparison_table_prompt(our_profile: dict, competitors: list) -> str:
    return f"""
        You are a strategic business analyst.

        You are given the detailed profiles of our company and several competitors.

        Our company profile:
        {json.dumps(our_profile, indent=2)}

        Competitor profiles:
        {json.dumps(competitors, indent=2)}

        Using all available information, create a comprehensive comparison table comparing our company with each competitor.

        Include detailed side-by-side comparisons for the following fields and any other relevant attributes found in the profiles:

        - Company Name
        - Description / Overview
        - Location(s)
        - Services / Products offered
        - Technologies used
        - Team size and expertise
        - Market segments and industries served
        - Key strengths and weaknesses
        - Recent achievements or innovations
        - Customer base / Target audience
        - Pricing strategy (if available)
        - Partnerships or alliances

        Format the output strictly as a JSON object with this structure:

        {{
        "comparison_table": {{
            "our_company": {our_profile},
            "competitors": [
            {{
                "competitor_name": "Name of competitor",
                "details": {{
                "description": "...",
                "location": "...",
                "services": [...],
                "technologies": [...],
                "team_size": "...",
                "industries": [...],
                "strengths": [...],
                "weaknesses": [...],
                "recent_achievements": "...",
                "customer_base": "...",
                "pricing_strategy": "...",
                "partnerships": "..."
                }}
            }},
            ...
            ]
        }}
        }}

        Return only the JSON. Do not include any explanations or commentary.
        """

def get_surpass_recommendation_prompt(our_profile: dict, competitors: list) -> str:
    return f"""
            You are a senior strategic business consultant.

            Given the profile of our company:
            {json.dumps(our_profile, indent=2)}

            And the profiles of competitors that are currently performing at or above our level:
            {json.dumps(competitors, indent=2)}

            For each competitor, propose 2 to 3 concrete, actionable strategies that our company can implement to surpass them.

            Focus your recommendations on areas including but not limited to:
            - Product or service innovation
            - Advanced technology adoption
            - Market positioning and branding differentiation
            - Strategic partnerships or alliances
            - Customer engagement and experience improvements

            Please return ONLY a JSON object formatted as follows:

            {{
            "recommendations": [
                {{
                "competitor": "Competitor Name",
                "actions": [
                    "First actionable strategy",
                    "Second actionable strategy",
                    "Third actionable strategy"
                ]
                }},
                ...
            ]
            }}

            No additional commentary or explanation — strictly the JSON output.
            """

