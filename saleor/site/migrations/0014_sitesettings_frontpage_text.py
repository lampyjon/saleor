# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-01-10 19:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0013_merge_20180109_2201'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='frontpage_text',
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
