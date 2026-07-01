from collections import OrderedDict
from enum import Enum
from urllib.parse import urlparse
from typing import List, Optional
from app.models.canonical import SocialProfile
from app.utils.constants import GITHUB_PLACEHOLDER_USERNAMES, GITHUB_RESERVED_ROUTES
from ..base import BaseNormalizer, NormalizationResult, ValidationState


class GitHubURLType(str, Enum):
    PROFILE = "PROFILE"
    REPOSITORY = "REPOSITORY"
    NON_IDENTIFYING = "NON_IDENTIFYING"


class GitHubURLClassifier:
    @staticmethod
    def _parse(raw_url: str):
        url = (raw_url or "").strip().rstrip(".,;)>\"'")
        if not url:
            return None
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return urlparse(url)

    @classmethod
    def classify(cls, raw_url: str) -> GitHubURLType:
        parsed = cls._parse(raw_url)
        if not parsed:
            return GitHubURLType.NON_IDENTIFYING

        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]

        if host == "gist.github.com":
            return GitHubURLType.NON_IDENTIFYING
        if host != "github.com":
            return GitHubURLType.NON_IDENTIFYING

        segments = [segment for segment in parsed.path.split("/") if segment]
        if not segments:
            return GitHubURLType.NON_IDENTIFYING

        username = segments[0].lower()
        if username in GITHUB_RESERVED_ROUTES or username in GITHUB_PLACEHOLDER_USERNAMES:
            return GitHubURLType.NON_IDENTIFYING

        if len(segments) == 1:
            return GitHubURLType.PROFILE
        return GitHubURLType.REPOSITORY

    @classmethod
    def username(cls, raw_url: str) -> Optional[str]:
        if cls.classify(raw_url) != GitHubURLType.PROFILE:
            return None
        parsed = cls._parse(raw_url)
        if not parsed:
            return None
        segments = [segment for segment in parsed.path.split("/") if segment]
        return segments[0].lower() if len(segments) == 1 else None

    @classmethod
    def normalize_profile_url(cls, raw_url: str) -> Optional[str]:
        username = cls.username(raw_url)
        return f"https://github.com/{username}" if username else None


def select_canonical_github_profile(raw_urls: List[str]) -> Optional[str]:
    profiles = []
    for raw_url in raw_urls:
        username = GitHubURLClassifier.username(raw_url)
        if username:
            profiles.append((username, f"https://github.com/{username}"))

    if not profiles:
        return None

    counts = OrderedDict()
    first_urls = {}
    for username, normalized_url in profiles:
        counts[username] = counts.get(username, 0) + 1
        first_urls.setdefault(username, normalized_url)

    best_username = max(counts, key=lambda username: counts[username])
    return first_urls[best_username]


class UrlNormalizer(BaseNormalizer):
    def normalize(self, profiles: List[SocialProfile]) -> NormalizationResult[List[SocialProfile]]:
        state = ValidationState.VALID
        new_profiles = []
        
        for profile in profiles:
            new_profile = profile.model_copy(deep=True)
            if not new_profile.url or not new_profile.url.strip():
                state = ValidationState.UNPARSEABLE
                new_profiles.append(new_profile)
                continue
                
            url_str = new_profile.url.strip()
            
            # Prepend https if no protocol is given
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'https://' + url_str
                
            try:
                if new_profile.platform.lower() == "github":
                    normalized_github = GitHubURLClassifier.normalize_profile_url(url_str)
                    if normalized_github:
                        new_profile.url = normalized_github
                        new_profiles.append(new_profile)
                        continue
                    state = ValidationState.UNPARSEABLE
                    continue

                parsed = urlparse(url_str)
                # Lowercase host
                host = (parsed.netloc or '').lower()
                # Remove trailing slash from path
                path = parsed.path
                if path and path.endswith('/') and len(path) > 1:
                    path = path.rstrip('/')
                    
                # Reconstruct
                normalized = f"{parsed.scheme}://{host}{path}"
                if parsed.query:
                    normalized += f"?{parsed.query}"
                if parsed.fragment:
                    normalized += f"#{parsed.fragment}"
                    
                new_profile.url = normalized
            except Exception:
                state = ValidationState.UNPARSEABLE
            new_profiles.append(new_profile)
                
        return NormalizationResult(new_profiles, state)
