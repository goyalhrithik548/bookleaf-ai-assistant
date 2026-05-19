from difflib import SequenceMatcher
import logging
import re

from app.database.db import (
    EmptyResultError,
    MultipleResultsError,
)
from app.database.queries import (
    find_author_by_email,
    find_author_by_instagram_handle,
    find_author_by_phone,
    search_author_by_name,
)


logger = logging.getLogger(__name__)

SOCIAL_HANDLE_FIELDS = (
    "twitter",
    "x",
    "instagram",
    "linkedin",
    "facebook",
    "github",
    "social",
    "social_handle",
    "handle",
)


class IdentityNotFoundError(Exception):
    pass


class MultipleIdentityMatchesError(Exception):
    pass


def normalize_text(value):
    """Normalize user-provided text before exact or fuzzy comparison."""
    if value is None:
        return ""

    text = str(value).strip()

    # Accept email values accidentally sent as Markdown mailto links.
    mailto_match = re.match(r"^\[([^\]]+)\]\(mailto:([^)]+)\)$", text, re.IGNORECASE)
    if mailto_match:
        text = mailto_match.group(2)

    text = text.replace("mailto:", "")
    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def calculate_name_similarity(name_1, name_2):
    """Return a fuzzy name similarity score between 0 and 1."""
    normalized_name_1 = normalize_text(name_1)
    normalized_name_2 = normalize_text(name_2)

    if not normalized_name_1 or not normalized_name_2:
        return 0.0

    return SequenceMatcher(None, normalized_name_1, normalized_name_2).ratio()


def _normalize_phone(value):
    return re.sub(r"\D", "", normalize_text(value))


def _normalize_social_handle(value):
    return normalize_text(value).lstrip("@")


def _find_social_match(profile_1, profile_2):
    for field in SOCIAL_HANDLE_FIELDS:
        handle_1 = _normalize_social_handle(profile_1.get(field))
        handle_2 = _normalize_social_handle(profile_2.get(field))

        if handle_1 and handle_2 and handle_1 == handle_2:
            return field

    return None


def _author_to_identity_profile(author):
    return {
        "id": author.get("id"),
        "name": author.get("author_name"),
        "email": author.get("email"),
        "phone": author.get("phone"),
        "instagram": author.get("instagram_handle"),
        "instagram_handle": author.get("instagram_handle"),
        "book_title": author.get("book_title")
    }


def _first_available_social_handle(profile):
    for field in SOCIAL_HANDLE_FIELDS:
        handle = profile.get(field)

        if handle:
            return handle

    return None


def _resolve_profile_from_supabase(profile):
    if not isinstance(profile, dict):
        raise ValueError("Both profiles must be valid objects")

    lookup_attempted = False

    email = profile.get("email")
    if email:
        lookup_attempted = True

        try:
            return _author_to_identity_profile(find_author_by_email(email))

        except EmptyResultError:
            pass

        except MultipleResultsError as exc:
            raise MultipleIdentityMatchesError("Multiple matching authors found") from exc

    phone = profile.get("phone")
    if phone:
        lookup_attempted = True

        try:
            return _author_to_identity_profile(find_author_by_phone(phone))

        except EmptyResultError:
            pass

        except MultipleResultsError as exc:
            raise MultipleIdentityMatchesError("Multiple matching authors found") from exc

    social_handle = _first_available_social_handle(profile)
    if social_handle:
        lookup_attempted = True

        try:
            return _author_to_identity_profile(find_author_by_instagram_handle(social_handle))

        except EmptyResultError:
            pass

        except MultipleResultsError as exc:
            raise MultipleIdentityMatchesError("Multiple matching authors found") from exc

    name = profile.get("name") or profile.get("author_name")
    if name:
        lookup_attempted = True

        try:
            matches = search_author_by_name(name)

        except EmptyResultError:
            matches = []

        if len(matches) == 1:
            return _author_to_identity_profile(matches[0])

        if len(matches) > 1:
            raise MultipleIdentityMatchesError("Multiple matching authors found")

    if lookup_attempted:
        raise IdentityNotFoundError("No matching author found")

    raise ValueError("At least one identity field is required")


def unify_author_identity(profile_1, profile_2):
    resolved_profile_1 = _resolve_profile_from_supabase(profile_1)
    resolved_profile_2 = _resolve_profile_from_supabase(profile_2)

    result = unify_identity(
        resolved_profile_1,
        resolved_profile_2
    )

    logger.info(
        "Identity match completed confidence=%s is_match=%s",
        result["confidence"],
        result["is_match"]
    )

    return result


def unify_identity(profile_1, profile_2):
    """
    Compare two profile dictionaries and decide whether they likely belong
    to the same person.

    This intentionally uses transparent rules for assignment/demo clarity.
    Production systems may combine embeddings, probabilistic matching, and
    graph-based identity resolution for stronger cross-source unification.
    """
    if not isinstance(profile_1, dict) or not isinstance(profile_2, dict):
        raise ValueError("Both profiles must be valid objects")

    score = 0.0
    matched_fields = []
    reasons = []

    email_1 = normalize_text(profile_1.get("email"))
    email_2 = normalize_text(profile_2.get("email"))

    if email_1 and email_2 and email_1 == email_2:
        score += 0.4
        matched_fields.append("email")
        reasons.append("Email matched")

    phone_1 = _normalize_phone(profile_1.get("phone"))
    phone_2 = _normalize_phone(profile_2.get("phone"))

    if phone_1 and phone_2 and phone_1 == phone_2:
        score += 0.3
        matched_fields.append("phone")
        reasons.append("Phone matched")

    matched_social_field = _find_social_match(profile_1, profile_2)

    if matched_social_field:
        score += 0.2
        matched_fields.append("social_handle")
        reasons.append(f"Social handle matched ({matched_social_field})")

    name_similarity = calculate_name_similarity(
        profile_1.get("name"),
        profile_2.get("name")
    )

    if name_similarity > 0.8:
        score += 0.1
        matched_fields.append("name")
        reasons.append("High name similarity")

    confidence = round(min(score, 1.0), 2)

    return {
        "is_match": confidence >= 0.7,
        "confidence": confidence,
        "matched_fields": matched_fields,
        "reasons": reasons
    }
