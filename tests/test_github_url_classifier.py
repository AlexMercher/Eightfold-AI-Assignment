from app.extraction.field_extractor import FieldExtractor
from app.pipeline.normalization.normalizers.url import (
    GitHubURLClassifier,
    GitHubURLType,
)


def test_github_url_classification_matrix():
    cases = {
        "github.com/alexjohnson": GitHubURLType.PROFILE,
        "github.com/alex-sharma-98172": GitHubURLType.PROFILE,
        "github.com/alex_dev": GitHubURLType.PROFILE,
        "github.com/alexjohnson/myrepo": GitHubURLType.REPOSITORY,
        "github.com/alexjohnson/repo/tree/main": GitHubURLType.REPOSITORY,
        "github.com": GitHubURLType.NON_IDENTIFYING,
        "gist.github.com/alexjohnson": GitHubURLType.NON_IDENTIFYING,
        "github.com/login": GitHubURLType.NON_IDENTIFYING,
        "github.com/username": GitHubURLType.NON_IDENTIFYING,
        "github.com/settings/profile": GitHubURLType.NON_IDENTIFYING,
        "http://github.com/alexjohnson": GitHubURLType.PROFILE,
        "https://www.github.com/alexjohnson": GitHubURLType.PROFILE,
        "GITHUB.COM/AlexJohnson": GitHubURLType.PROFILE,
    }

    for raw_url, expected in cases.items():
        assert GitHubURLClassifier.classify(raw_url) == expected


def test_multi_url_priority_keeps_profile_not_repositories():
    text = """
    Alex Johnson
    github.com/realuser
    Projects: github.com/realuser/project-a github.com/realuser/project-b
    """

    result = FieldExtractor().extract([], text)

    assert result.contact.github == "https://github.com/realuser"


def test_multiple_profile_urls_deduplicate_by_username():
    text = """
    Alex Johnson
    github.com/realuser
    http://github.com/realuser
    https://github.com/realuser
    """

    result = FieldExtractor().extract([], text)

    assert result.contact.github == "https://github.com/realuser"


def test_repository_only_urls_do_not_fallback_to_invented_profile():
    text = """
    Alex Johnson
    github.com/realuser/project-a
    https://github.com/realuser/project-b/tree/main
    """

    result = FieldExtractor().extract([], text)

    assert result.contact.github is None
