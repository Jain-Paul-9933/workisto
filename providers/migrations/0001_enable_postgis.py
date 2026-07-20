"""
Ensure the PostGIS extension exists BEFORE any geo model migration runs.

The postgis Docker image usually creates it already, but relying on that is
fragile (only true on a fresh volume). CreateExtension runs
`CREATE EXTENSION IF NOT EXISTS postgis`, so it's safe and idempotent — and it
also makes the *test* database (built fresh each run) spatial-capable.

The model migration for ServiceProvider/ServiceOffering is generated later by
makemigrations and will depend on this one automatically.
"""

from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        CreateExtension("postgis"),
    ]
