# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-02 15:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bullets', '0002_activitycache'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bullet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('postcode', models.CharField(max_length=5, verbose_name='first part of postcode')),
                ('email', models.EmailField(max_length=200, verbose_name='mmail address')),
                ('contact_no', models.CharField(max_length=100, verbose_name='contact number')),
                ('over_18', models.BooleanField(help_text='Please confirm you are over 18?', verbose_name='over 18')),
                ('get_emails', models.BooleanField(help_text='Can we contact you regarding Collective events?', verbose_name='get emails')),
            ],
        ),
    ]
