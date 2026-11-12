import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "categories"},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("origin", models.CharField(blank=True, max_length=180)),
                ("sustainability_info", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_products",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ProductTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "locale",
                    models.CharField(
                        choices=[
                            ("es-419", "Español (Latinoamérica)"),
                            ("es-es", "Español (España)"),
                            ("ca", "Català"),
                            ("gl", "Galego"),
                            ("eu", "Euskara"),
                            ("en-us", "English (US)"),
                            ("en-gb", "English (UK)"),
                            ("en", "English"),
                            ("pt-br", "Português (Brasil)"),
                            ("pt-pt", "Português (Portugal)"),
                        ],
                        max_length=10,
                    ),
                ),
                ("name", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("sustainability_info", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["locale"]},
        ),
        migrations.AddConstraint(
            model_name="producttranslation",
            constraint=models.UniqueConstraint(
                fields=("product", "locale"), name="unique_product_locale"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["name"], name="product_name_idx"),
        ),
    ]
