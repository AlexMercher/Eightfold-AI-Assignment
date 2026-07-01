import os
from typing import Any, Optional

import httpx

from app.models.canonical import Candidate, Experience, SocialProfile
from app.models.canonical.components import ProvenanceEntry
from app.pipeline.normalization.normalizers.url import GitHubURLClassifier
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubAdapter:
    API_BASE = "https://api.github.com/users"

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    def enrich(self, profile_url: str, candidate: Candidate) -> Candidate:
        try:
            username = GitHubURLClassifier.username(profile_url)
            if not username:
                logger.warning("GitHub enrichment skipped for non-profile URL")
                return candidate

            token = os.getenv("GITHUB_TOKEN")
            headers = {"Accept": "application/vnd.github+json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            else:
                logger.info("GITHUB_TOKEN is not set; using unauthenticated GitHub API")

            response = httpx.get(
                f"{self.API_BASE}/{username}",
                headers=headers,
                timeout=self.timeout_seconds,
            )
            if response.status_code == 404:
                logger.warning(f"GitHub profile does not exist: {username}")
                return candidate
            if response.status_code in {403, 429}:
                logger.warning(f"GitHub API rate limited or forbidden for: {username}")
                return candidate
            if response.status_code >= 500:
                logger.warning(f"GitHub API server error {response.status_code} for: {username}")
                return candidate
            if response.status_code >= 400:
                logger.warning(f"GitHub API error {response.status_code} for: {username}")
                return candidate

            data = response.json()
            if (data.get("login") or "").lower() != username:
                logger.warning(f"GitHub API login mismatch for: {username}")
                return candidate

            enriched = candidate.model_copy(deep=True)
            self._apply_fields(enriched, data)
            return enriched
        except httpx.TimeoutException:
            logger.warning(f"GitHub API timeout for profile: {profile_url}")
            return candidate
        except Exception as exc:
            logger.warning(f"GitHub enrichment failed for {profile_url}: {exc}")
            return candidate

    def _apply_fields(self, candidate: Candidate, data: dict[str, Any]) -> None:
        self._set_if_empty(candidate, "personal_info.name", data.get("name"))
        self._set_if_empty(candidate, "professional_info.headline", data.get("bio"))
        self._set_if_empty(candidate, "personal_info.location", data.get("location"))

        blog = data.get("blog")
        if blog and self._valid_url(blog) and not candidate.contact_info.website:
            candidate.contact_info.website = blog
            candidate.social_profiles.append(SocialProfile(platform="Portfolio", url=blog))
            self._record(candidate, "links.portfolio", blog)

        company = data.get("company")
        if company and not candidate.professional_info.experiences:
            candidate.professional_info.experiences.append(
                Experience(company=company, title="Unknown")
            )
            if not candidate.professional_info.current_company:
                candidate.professional_info.current_company = company
            self._record(candidate, "experience[0].company", company)

    def _set_if_empty(self, candidate: Candidate, field_path: str, value: Optional[str]) -> None:
        if not value:
            return

        target, attr = self._resolve(candidate, field_path)
        current_value = getattr(target, attr)
        if current_value:
            return

        setattr(target, attr, value)
        provenance_field = {
            "personal_info.name": "full_name",
            "professional_info.headline": "headline",
            "personal_info.location": "location",
        }.get(field_path, field_path)
        self._record(candidate, provenance_field, value)

    def _resolve(self, candidate: Candidate, field_path: str):
        target = candidate
        parts = field_path.split(".")
        for part in parts[:-1]:
            target = getattr(target, part)
        return target, parts[-1]

    def _record(self, candidate: Candidate, field_name: str, value: Any) -> None:
        candidate.provenance.append(
            ProvenanceEntry(
                field=field_name,
                source="github_api",
                method="api_enrichment",
                value=value,
            )
        )

    def _valid_url(self, value: str) -> bool:
        raw = value.strip()
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw
        parsed = httpx.URL(raw)
        return bool(parsed.host)
