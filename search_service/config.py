"""
Config for the standalone search service. Reads the SAME environment as Django
so it points at the SAME Postgres — but it never imports Django. The JWT secret
is shared with Django, which is what lets this service trust a token without any
cross-service call (ADR 0001).
"""

import os

JWT_SECRET = os.getenv("SEARCH_JWT_SECRET", "dev-search-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"


def database_url():
    # Read at call time (startup), so tests can point us at the test DB.
    explicit = os.getenv("SEARCH_DATABASE_URL")
    if explicit:
        return explicit
    return (
        f"postgresql://{os.getenv('POSTGRES_USER', 'homeservices')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'homeservices')}@"
        f"{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'homeservices')}"
    )
