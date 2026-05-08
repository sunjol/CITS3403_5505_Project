def polish_prompt(prompt_text, tone=None, output_format=None, audience=None):
    """Local fallback prompt optimiser used until an external AI service is wired in."""
    sections = [
        "Role: Act as a precise prompt engineer.",
        f"Task: Improve this prompt for {audience or 'the intended audience'}.",
        f"Tone: Use a {tone or 'clear and professional'} tone.",
        f"Format: Return the answer as {output_format or 'structured sections'}.",
        "Constraints: Remove ambiguity, add context, and state success criteria.",
        f"Draft: {prompt_text.strip()}",
    ]
    return "\n".join(sections)


def quota_summary(limit, used_count=0):
    remaining = max(limit - used_count, 0)
    return {
        "limit": limit,
        "used": used_count,
        "remaining": remaining,
    }
