# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-05-08 20:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bullets', '0020_auto_20170504_2233'),
    ]

    operations = [
        migrations.CreateModel(
            name='TdBLeaderBoard_Entry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_id', models.PositiveIntegerField(verbose_name='Segment ID')),
                ('athlete_id', models.PositiveIntegerField(verbose_name='Athlete ID')),
                ('time_taken', models.DurationField(verbose_name='Time Taken')),
                ('date_completed', models.DateField(verbose_name='Date completed')),
            ],
        ),
        migrations.CreateModel(
            name='TdBStage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Stage name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('valid_from', models.DateField(verbose_name='Valid from')),
                ('valid_until', models.DateField(verbose_name='Valid until')),
                ('long_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Long segment ID')),
                ('medium_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Medium segment ID')),
                ('short_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Short segment ID')),
                ('social_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Social segment ID')),
                ('hilly_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Hilly segment ID')),
                ('flat_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Flat segment ID')),
            ],
        ),
    ]
