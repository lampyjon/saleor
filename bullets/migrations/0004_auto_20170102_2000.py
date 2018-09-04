# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-02 20:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('bullets', '0003_bullet'),
    ]

    operations = [
        migrations.AddField(
            model_name='bullet',
            name='email_check_ref',
            field=models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='random uuid for email confirmation'),
        ),
        migrations.AddField(
            model_name='bullet',
            name='email_checked',
            field=models.BooleanField(default=False, verbose_name='confirmed email'),
        ),
        migrations.AddField(
            model_name='bullet',
            name='joined',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='date joined'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bullet',
            name='get_emails',
            field=models.BooleanField(help_text='Can we contact you regarding Collective events?', verbose_name='receive emails'),
        ),
    ]
