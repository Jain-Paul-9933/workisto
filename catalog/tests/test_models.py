import pytest

from catalog.models import ServiceCategory


@pytest.mark.django_db
def test_slug_autogenerates_from_name():
    category = ServiceCategory.objects.create(name="AC Repair")
    assert category.slug == "ac-repair"


@pytest.mark.django_db
def test_default_duration_is_30_minutes():
    category = ServiceCategory.objects.create(name="Haircut")
    assert category.default_duration_minutes == 30
