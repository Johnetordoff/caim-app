# Generated by Django 4.1 on 2023-06-26 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("caim_base", "0030_fosterapplication"),
    ]

    operations = [
        migrations.AddField(
            model_name="awgmember",
            name="canManageApplications",
            field=models.BooleanField(default=False),
        ),
    ]
