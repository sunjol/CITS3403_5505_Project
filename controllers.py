import json
import urllib.error
import urllib.request
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from extensions import db
from models import DailyQuotaUsage, Prompt


class ExternalModelError(RuntimeError):
    pass


PROMPT_CATEGORIES = ("Writing", "Coding", "Study", "Marketing", "Research")
COMMUNITY_VISIBILITY_OPTIONS = {
    "all": "All",
    "community": "Community Public Posts",
    "my": "My Posts",
}
COMMUNITY_SORT_OPTIONS = {
    "newest": "Newest",
    "oldest": "Oldest",
    "title": "Title A-Z",
}
HISTORY_TYPE_OPTIONS = {
    "all": "All prompts",
    "optimised": "Optimised prompts",
    "saved": "Saved drafts",
}
HISTORY_VISIBILITY_OPTIONS = {
    "all": "All visibility",
    "public": "Public",
    "private": "Private",
}


def polish_prompt(prompt_text, tone=None, output_format=None, audience=None):
    """Local fallback prompt optimiser used when no external model is requested."""
    sections = [
        "Role: Act as a precise prompt engineer.",
        f"Task: Improve this prompt for {audience or 'the intended audience'}.",
        f"Tone: Use a {tone or 'clear and professional'} tone.",
        f"Format: Return the answer as {output_format or 'structured sections'}.",
        "Constraints: Remove ambiguity, add context, and state success criteria.",
        f"Draft: {prompt_text.strip()}",
    ]
    return "\n".join(sections)


def optimise_prompt(prompt_text, tone=None, output_format=None, audience=None, focus=None):
    focus_text = ", ".join(focus or ["clarity", "constraints"])
    return polish_prompt(
        f"{prompt_text.strip()}\nFocus areas: {focus_text}.",
        tone=tone,
        output_format=output_format,
        audience=audience,
    )


def optimise_prompt_with_groq(
    prompt_text,
    api_key,
    api_url,
    model,
    timeout,
    user_agent,
    tone=None,
    output_format=None,
    audience=None,
    focus=None,
):
    if not api_key:
        raise ValueError("Groq API key is not configured.")

    focus_text = ", ".join(focus or ["clarity", "constraints"])
    messages = [
        {
            "role": "system",
            "content": (
                "You are a prompt optimisation assistant. Return only the improved prompt. "
                "Use Australian English where natural. Do not explain your process."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original prompt:\n{prompt_text.strip()}\n\n"
                f"Tone: {tone or 'Clear and professional'}\n"
                f"Audience: {audience or 'General users'}\n"
                f"Output format: {output_format or 'Structured sections'}\n"
                f"Optimisation focus: {focus_text}\n\n"
                "Rewrite the prompt so it has a clear role, task, context, constraints, "
                "and expected output format."
            ),
        },
    ]
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 900,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        },
        method="POST",
    )

    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if error.code == 403 and "1010" in detail:
            raise ExternalModelError(
                "Groq blocked the external-model request with HTTP 403 / error 1010. "
                "This is usually caused by Groq or Cloudflare rejecting the current "
                "network, VPN, proxy, or request fingerprint. The app used the local "
                "fallback optimiser instead."
            ) from error
        raise ExternalModelError(
            f"Groq request failed with HTTP {error.code}. The app used the local fallback optimiser instead."
        ) from error
    except urllib.error.URLError as error:
        raise ExternalModelError(
            f"Could not reach Groq: {error.reason}. The app used the local fallback optimiser instead."
        ) from error

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise ExternalModelError(
            "Groq returned an unexpected response. The app used the local fallback optimiser instead."
        ) from error


def quota_summary(limit, used_count=0):
    remaining = max(limit - used_count, 0)
    return {
        "limit": limit,
        "used": used_count,
        "remaining": remaining,
    }


def app_timezone(timezone_name):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Australia/Perth")


def quota_period(timezone_name):
    timezone = app_timezone(timezone_name)
    now = datetime.now(timezone)
    usage_date = now.date()
    next_reset = datetime.combine(
        usage_date + timedelta(days=1),
        time.min,
        tzinfo=timezone,
    )
    return usage_date, next_reset


def format_reset_time(reset_time):
    return reset_time.strftime("%d %b %Y, %I:%M %p %Z").replace(", 0", ", ")


def quota_usage_for_user(user, limit, timezone_name):
    usage_date, next_reset = quota_period(timezone_name)
    usage = DailyQuotaUsage.query.filter_by(
        user_id=user.id,
        usage_date=usage_date,
    ).first()
    used_count = usage.used_count if usage else 0
    summary = quota_summary(limit, used_count)
    summary.update(
        {
            "usage_date": usage_date,
            "next_reset": next_reset,
            "next_reset_label": format_reset_time(next_reset),
        }
    )
    return summary


def ensure_quota_available(user, limit, timezone_name):
    summary = quota_usage_for_user(user, limit, timezone_name)
    if summary["remaining"] <= 0:
        raise RuntimeError("Daily prompt quota exhausted. Please try again after the next reset.")
    return summary


def consume_quota(user, limit, timezone_name):
    usage_date, next_reset = quota_period(timezone_name)
    usage = DailyQuotaUsage.query.filter_by(
        user_id=user.id,
        usage_date=usage_date,
    ).first()
    if usage is None:
        usage = DailyQuotaUsage(user_id=user.id, usage_date=usage_date, used_count=0)
        db.session.add(usage)

    if usage.used_count >= limit:
        raise RuntimeError("Daily prompt quota exhausted. Please try again after the next reset.")

    usage.used_count += 1
    summary = quota_summary(limit, usage.used_count)
    summary.update(
        {
            "usage_date": usage_date,
            "next_reset": next_reset,
            "next_reset_label": format_reset_time(next_reset),
        }
    )
    return summary


def normalise_community_filters(args, user=None):
    visibility = args.get("visibility", "all")
    if visibility not in COMMUNITY_VISIBILITY_OPTIONS:
        visibility = "all"

    if user is None and visibility == "my":
        visibility = "all"

    category = args.get("category", "")
    if category not in PROMPT_CATEGORIES:
        category = ""

    sort = args.get("sort", "newest")
    if sort not in COMMUNITY_SORT_OPTIONS:
        sort = "newest"

    return {
        "query": args.get("query", "").strip(),
        "category": category,
        "visibility": visibility,
        "sort": sort,
    }


def community_prompts(filters, user=None):
    prompt_query = Prompt.query.join(Prompt.user)
    visibility = filters["visibility"]

    if visibility == "my":
        prompt_query = prompt_query.filter(Prompt.user_id == user.id)
    elif visibility == "community":
        prompt_query = prompt_query.filter(Prompt.is_public.is_(True))
        if user is not None:
            prompt_query = prompt_query.filter(Prompt.user_id != user.id)
    elif user is not None:
        prompt_query = prompt_query.filter(
            (Prompt.is_public.is_(True)) | (Prompt.user_id == user.id)
        )
    else:
        prompt_query = prompt_query.filter(Prompt.is_public.is_(True))

    if filters["category"]:
        prompt_query = prompt_query.filter(Prompt.category == filters["category"])

    if filters["query"]:
        search = f"%{filters['query']}%"
        prompt_query = prompt_query.filter(
            Prompt.title.ilike(search)
            | Prompt.original_prompt.ilike(search)
            | Prompt.optimised_prompt.ilike(search)
            | Prompt.notes.ilike(search)
        )

    if filters["sort"] == "oldest":
        prompt_query = prompt_query.order_by(Prompt.created_at.asc())
    elif filters["sort"] == "title":
        prompt_query = prompt_query.order_by(Prompt.title.asc())
    else:
        prompt_query = prompt_query.order_by(Prompt.created_at.desc())

    return prompt_query.all()


def normalise_history_filters(args):
    prompt_type = args.get("type", "all")
    if prompt_type not in HISTORY_TYPE_OPTIONS:
        prompt_type = "all"

    visibility = args.get("visibility", "all")
    if visibility not in HISTORY_VISIBILITY_OPTIONS:
        visibility = "all"

    category = args.get("category", "")
    valid_categories = PROMPT_CATEGORIES + ("Optimisation",)
    if category not in valid_categories:
        category = ""

    sort = args.get("sort", "newest")
    if sort not in COMMUNITY_SORT_OPTIONS:
        sort = "newest"

    return {
        "query": args.get("query", "").strip(),
        "type": prompt_type,
        "visibility": visibility,
        "category": category,
        "sort": sort,
    }


def user_history_prompts(user, filters):
    prompt_query = Prompt.query.filter(Prompt.user_id == user.id)

    if filters["type"] == "optimised":
        prompt_query = prompt_query.filter(Prompt.optimised_prompt.isnot(None))
    elif filters["type"] == "saved":
        prompt_query = prompt_query.filter(Prompt.optimised_prompt.is_(None))

    if filters["visibility"] == "public":
        prompt_query = prompt_query.filter(Prompt.is_public.is_(True))
    elif filters["visibility"] == "private":
        prompt_query = prompt_query.filter(Prompt.is_public.is_(False))

    if filters["category"]:
        prompt_query = prompt_query.filter(Prompt.category == filters["category"])

    if filters["query"]:
        search = f"%{filters['query']}%"
        prompt_query = prompt_query.filter(
            Prompt.title.ilike(search)
            | Prompt.original_prompt.ilike(search)
            | Prompt.optimised_prompt.ilike(search)
            | Prompt.notes.ilike(search)
        )

    if filters["sort"] == "oldest":
        prompt_query = prompt_query.order_by(Prompt.created_at.asc())
    elif filters["sort"] == "title":
        prompt_query = prompt_query.order_by(Prompt.title.asc())
    else:
        prompt_query = prompt_query.order_by(Prompt.created_at.desc())

    return prompt_query.all()
