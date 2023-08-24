# Generated by Django 4.1 on 2023-06-23 16:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("caim_base", "0031_userprofile_city_userprofile_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="animal",
            name="behaviour_cats",
            field=models.CharField(
                choices=[
                    ("POOR", "Poor"),
                    ("SELECTIVE", "Selective"),
                    ("GOOD", "Good"),
                    ("NOT_TESTED", "Not tested"),
                ],
                default="NOT_TESTED",
                max_length=10,
                verbose_name="Behavior with cats",
            ),
        ),
        migrations.AlterField(
            model_name="animal",
            name="behaviour_dogs",
            field=models.CharField(
                choices=[
                    ("POOR", "Poor"),
                    ("SELECTIVE", "Selective"),
                    ("GOOD", "Good"),
                    ("NOT_TESTED", "Not tested"),
                ],
                default="NOT_TESTED",
                max_length=10,
                verbose_name="Behavior with dogs",
            ),
        ),
        migrations.AlterField(
            model_name="animal",
            name="behaviour_kids",
            field=models.CharField(
                choices=[
                    ("POOR", "Poor"),
                    ("SELECTIVE", "Selective"),
                    ("GOOD", "Good"),
                    ("NOT_TESTED", "Not tested"),
                ],
                default="NOT_TESTED",
                max_length=10,
                verbose_name="Behavior with kids",
            ),
        ),
        migrations.AlterField(
            model_name="fostererprofile",
            name="hours_alone_description",
            field=models.TextField(
                blank=True,
                default=None,
                null=True,
                verbose_name="How many hours per day will your foster animal be left alone?",
            ),
        ),
    ]
