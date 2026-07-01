import httpx

from app.adapters.github_adapter import GitHubAdapter
from app.models.canonical import Candidate, PersonalInfo, ProfessionalInfo, SocialProfile


def make_candidate() -> Candidate:
    return Candidate(
        candidate_id="candidate-1",
        personal_info=PersonalInfo(),
        professional_info=ProfessionalInfo(),
        social_profiles=[SocialProfile(platform="GitHub", url="https://github.com/octocat")],
    )


def test_github_adapter_enriches_empty_fields_and_records_provenance(monkeypatch):
    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            json={
                "login": "octocat",
                "name": "The Octocat",
                "bio": "GitHub mascot",
                "location": "San Francisco",
                "blog": "https://github.blog",
                "company": "@github",
                "public_repos": 8,
                "followers": 10000,
            },
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    enriched = GitHubAdapter().enrich("https://github.com/octocat", make_candidate())

    assert enriched.personal_info.name == "The Octocat"
    assert enriched.professional_info.headline == "GitHub mascot"
    assert enriched.personal_info.location == "San Francisco"
    assert enriched.contact_info.website == "https://github.blog"
    assert enriched.professional_info.experiences[0].company == "@github"
    assert {item.field for item in enriched.provenance} == {
        "full_name",
        "headline",
        "location",
        "links.portfolio",
        "experience[0].company",
    }
    assert all(item.source == "github_api" for item in enriched.provenance)
    assert all(item.method == "api_enrichment" for item in enriched.provenance)


def test_github_adapter_does_not_overwrite_existing_fields(monkeypatch):
    def fake_get(*args, **kwargs):
        return httpx.Response(
            200,
            json={
                "login": "octocat",
                "name": "The Octocat",
                "bio": "GitHub mascot",
                "location": "San Francisco",
                "blog": "https://github.blog",
                "company": "@github",
            },
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    candidate = make_candidate()
    candidate.personal_info.name = "Existing Name"
    candidate.professional_info.headline = "Existing Headline"

    enriched = GitHubAdapter().enrich("https://github.com/octocat", candidate)

    assert enriched.personal_info.name == "Existing Name"
    assert enriched.professional_info.headline == "Existing Headline"


def test_github_adapter_failure_statuses_return_original_candidate(monkeypatch):
    candidate = make_candidate()

    for status_code in [404, 403, 429]:
        def fake_get(*args, **kwargs):
            return httpx.Response(status_code, json={})

        monkeypatch.setattr(httpx, "get", fake_get)
        result = GitHubAdapter().enrich("https://github.com/octocat", candidate)

        assert result is candidate
        assert result.provenance == []
