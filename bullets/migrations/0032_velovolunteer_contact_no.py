# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-17 17:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bullets', '0031_bulletsrunner_paid_offline'),
    ]

    operations = [
        migrations.AddField(
            model_name='velovolunteer',
            name='contact_no',
            field=models.CharField(default='-', max_length=100, verbose_name='contact number'),
            preserve_default=False,
        ),
    ]
