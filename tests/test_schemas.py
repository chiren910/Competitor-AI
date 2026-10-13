from schemas.company_schema import (
    AnalysisRecord,
    AnalysisSummary,
    CompanyProfile,
    Competitor,
    CompetitorDetail,
    MessageResponse,
    SurpassRecommendations,
)


def test_company_profile_defaults():
    profile = CompanyProfile()
    assert profile.name is None
    assert profile.services is None
    assert profile.industries is None


def test_company_profile_populated():
    profile = CompanyProfile(name="Acme", services=["Consulting"])
    assert profile.name == "Acme"
    assert profile.services == ["Consulting"]


def test_analysis_record_full():
    record = AnalysisRecord(
        link="https://acme.com",
        user_id="user-1",
        company_name="Acme",
        swot_analysis={"swot_analysis": {"our_company": {}}},
        local_competitor=[{"competitor_name": "Rival"}],
    )
    assert record.link == "https://acme.com"
    assert record.user_id == "user-1"
    assert record.local_competitor[0]["competitor_name"] == "Rival"


def test_analysis_summary_fields():
    summary = AnalysisSummary(link="https://acme.com", company_name="Acme")
    assert summary.category is None
    assert summary.created_at is None


def test_competitor_models():
    comp = Competitor(competitor_name="Rival", link="https://rival.com")
    detail = CompetitorDetail(**comp.model_dump(), profile={"name": "Rival"})
    assert detail.profile == {"name": "Rival"}


def test_message_response():
    msg = MessageResponse(message="deleted")
    assert msg.message == "deleted"


def test_recommendations():
    rec = SurpassRecommendations(recommendations=[{"competitor": "Rival", "actions": ["Do X"]}])
    assert rec.recommendations[0]["competitor"] == "Rival"