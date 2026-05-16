"""Seed 10 demo users with 10 prompts each (100 prompts total)."""
from datetime import timedelta

from controllers import PROMPT_CATEGORIES, optimise_prompt
from extensions import db
from models import Prompt, User, utc_now

DEMO_PASSWORD = "Testpass123"
USER_COUNT = 10
PROMPTS_PER_USER = 10

PROMPT_TITLES = [
    "Resume feedback assistant",
    "Python unit test generator",
    "Lesson plan for Year 9 science",
    "Product launch email draft",
    "Research summary helper",
    "Blog outline for sustainability",
    "SQL query explainer",
    "Interview prep coach",
    "Social post for campus event",
    "Meeting notes summariser",
]

ORIGINAL_PROMPTS = [
    "Help me improve my resume bullet points for a software internship.",
    "Write pytest cases for a Flask login route.",
    "Create a 45-minute lesson on photosynthesis with a short quiz.",
    "Draft a marketing email announcing a new study app feature.",
    "Summarise three papers on renewable energy policy in Australia.",
    "Outline a blog post about reducing household waste.",
    "Explain this SQL join query in plain English: SELECT * FROM users u JOIN orders o ON u.id = o.user_id;",
    "Give me practice questions for a graduate data analyst interview.",
    "Write a friendly Instagram caption for a university hackathon.",
    "Turn these messy meeting notes into action items and owners.",
]


def seed_demo_data():
    created_users = 0
    created_prompts = 0
    now = utc_now()

    for index in range(1, USER_COUNT + 1):
        username = f"demo_user{index:02d}"
        email = f"demo_user{index:02d}@promptshare.test"

        user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if user is None:
            user = User(username=username, email=email)
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
            db.session.flush()
            created_users += 1

        existing_count = Prompt.query.filter_by(user_id=user.id).count()
        if existing_count >= PROMPTS_PER_USER:
            continue

        for prompt_index in range(PROMPTS_PER_USER):
            if prompt_index < existing_count:
                continue

            title = PROMPT_TITLES[prompt_index]
            original = ORIGINAL_PROMPTS[prompt_index]
            category = PROMPT_CATEGORIES[prompt_index % len(PROMPT_CATEGORIES)]
            is_optimised = prompt_index % 3 != 0
            is_public = prompt_index % 2 == 0
            created_at = now - timedelta(days=USER_COUNT - index, hours=prompt_index)

            optimised_text = None
            if is_optimised:
                optimised_text = optimise_prompt(
                    original,
                    tone="Clear and professional",
                    output_format="Structured sections",
                    audience="General users",
                    focus=["clarity", "constraints"],
                )

            prompt = Prompt(
                user_id=user.id,
                title=f"{title} ({username})",
                category=category,
                original_prompt=original,
                optimised_prompt=optimised_text,
                notes=f"Demo seed data for {username}.",
                is_public=is_public,
                created_at=created_at,
                updated_at=created_at,
            )
            db.session.add(prompt)
            created_prompts += 1

    db.session.commit()
    return created_users, created_prompts


if __name__ == "__main__":
    from run import app

    with app.app_context():
        users_added, prompts_added = seed_demo_data()
        total_users = User.query.count()
        total_prompts = Prompt.query.count()
        print(f"Added {users_added} users and {prompts_added} prompts.")
        print(f"Database now has {total_users} users and {total_prompts} prompts.")
        print(f"Demo login: demo_user01 / {DEMO_PASSWORD}")
