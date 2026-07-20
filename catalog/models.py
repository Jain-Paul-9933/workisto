"""
The service taxonomy.

`ServiceCategory` is the platform-managed list of *kinds* of service
("Drain cleaning", "Haircut", "AC repair"). It is deliberately dumb: it holds
no price and no provider. Price is a fact about a provider-and-category pair,
so it lives on `providers.ServiceOffering`, not here.
"""

from django.db import models
from django.utils.text import slugify


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    # The standard/default length of a job in this category. An offering may
    # override it, but 30 min is our floor and default.
    default_duration_minutes = models.PositiveIntegerField(default=30)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "service categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
