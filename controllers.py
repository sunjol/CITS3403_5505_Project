import json
import urllib.error
import urllib.request


class ExternalModelError(RuntimeError):
    pass


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
        with urllib.request.urlopen(request, timeout=timeout) as response:
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
