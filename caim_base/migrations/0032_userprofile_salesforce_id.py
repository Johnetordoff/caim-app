# Generated by Django 4.1 on 2023-06-17 01:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("caim_base", "0031_userprofile_city_userprofile_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="salesforce_id",
            field=models.CharField(max_length=32, null=True),
        ),
    ]
