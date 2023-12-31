# Generated by Django 4.2.5 on 2023-09-26 19:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ImageCraftApp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="image",
            name="link_expiration_time",
            field=models.PositiveIntegerField(
                default=300,
                validators=[
                    django.core.validators.MinValueValidator(
                        300, "The validity of the link cannot be less than 300 seconds."
                    ),
                    django.core.validators.MaxValueValidator(
                        30000, "The duration of the link cannot exceed 30000 seconds."
                    ),
                ],
            ),
        ),
    ]
