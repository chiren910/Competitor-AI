# schemas/company_schema.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    """Company profile extracted from a website."""
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    founded_year: Optional[Any] = None
    category: Optional[str] = None
    link: Optional[str] = None
    created_at: Optional[str] = None
    icon: Optional[str] = None
    tagline: Optional[str] = None
    elevator_pitch: Optional[str] = None
    industries: Optional[List[str]] = None
    services: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    team_size: Optional[Any] = None
    key_people: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    clients: Optional[List[str]] = None
    contact_info: Optional[Any] = None
    social_media: Optional[List[str]] = None
    awards: Optional[List[str]] = None


class MarketSize(BaseModel):
    sector: Optional[str] = None
    total_market_size: Optional[Dict[str, Any]] = None
    growth_rate: Optional[Dict[str, Any]] = None
    key_drivers: Optional[List[str]] = None
    major_regions: Optional[List[str]] = None
    top_companies: Optional[List[Dict[str, Any]]] = None
    forecast: Optional[Dict[str, Any]] = None


class MarketData(MarketSize):
    """Market analysis including size, drivers, regions, top players."""


class MarketShare(BaseModel):
    market_capture: Optional[Dict[str, Any]] = None
    current_position: Optional[Dict[str, Any]] = None
    growth_recommendations: Optional[Dict[str, Any]] = None


class Competitor(BaseModel):
    """Basic competitor entry (name, description, link)."""
    competitor_name: Optional[str] = None
    description: Optional[str] = None
    link: Optional[str] = None


class CompetitorDetail(Competitor):
    """Detailed competitor profile with comparison against our company."""
    profile: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None


class SwotAnalysis(BaseModel):
    swot_analysis: Optional[Dict[str, Any]] = None


class ComparisonTable(BaseModel):
    comparison_table: Optional[Dict[str, Any]] = None


class SurpassRecommendations(BaseModel):
    recommendations: Optional[List[Dict[str, Any]]] = None


class AnalysisSummary(BaseModel):
    """Lightweight summary of a saved analysis used for list views."""
    link: Optional[str] = None
    company_name: Optional[str] = None
    category: Optional[str] = None
    created_at: Optional[str] = None


class AnalysisRecord(BaseModel):
    """Full competitor_analysis database row."""
    link: str
    user_id: str
    created_at: Optional[str] = None
    company_name: Optional[str] = None
    category: Optional[str] = None
    company_profile: Optional[Dict[str, Any]] = None
    market_data: Optional[Dict[str, Any]] = None
    market_capture: Optional[Dict[str, Any]] = None
    local_competitor: Optional[List[Dict[str, Any]]] = None
    national_competitor: Optional[List[Dict[str, Any]]] = None
    global_competitor: Optional[List[Dict[str, Any]]] = None
    swot_analysis: Optional[Dict[str, Any]] = None
    comparison_table: Optional[Dict[str, Any]] = None
    surpass_recommendations: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    message: str