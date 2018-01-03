# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-20 18:48
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('order', '0017_auto_20170906_0556'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_id', models.CharField(max_length=30, verbose_name='Strava ID')),
                ('activity_type', models.CharField(choices=[('run', 'Run'), ('ride', 'Ride')], default='ride', max_length=4, verbose_name='Type')),
                ('distance', models.PositiveIntegerField(verbose_name='Distance')),
                ('start_date', models.DateTimeField(verbose_name='Activity Date')),
            ],
        ),
        migrations.CreateModel(
            name='Bullet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('postcode', models.CharField(max_length=5, verbose_name='first part of postcode')),
                ('email', models.EmailField(max_length=200, verbose_name='email address')),
                ('contact_no', models.CharField(max_length=100, verbose_name='contact number')),
                ('over_18', models.BooleanField(help_text='Please confirm that you are over 18?', verbose_name='over 18')),
                ('get_emails', models.BooleanField(help_text='Can we contact you regarding Collective events?', verbose_name='happy to receive emails')),
                ('joined', models.DateField(auto_now_add=True, verbose_name='date joined')),
                ('email_checked', models.BooleanField(default=False, verbose_name='confirmed email')),
                ('email_check_ref', models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='random uuid for email confirmation')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BulletsRunner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('address', models.TextField(verbose_name='address')),
                ('email', models.EmailField(max_length=200, verbose_name='email address')),
                ('contact_no', models.CharField(max_length=100, verbose_name='contact number')),
                ('emergency_contact_no', models.CharField(max_length=100, verbose_name='emergency contact number')),
                ('age', models.PositiveSmallIntegerField(help_text='Your age on the 17th September', verbose_name='age')),
                ('club', models.CharField(blank=True, max_length=200, verbose_name='Club')),
                ('race', models.CharField(choices=[('5', '5k'), ('10', '10k')], default='5', max_length=2, verbose_name='race length')),
                ('gender', models.CharField(choices=[('f', 'female'), ('m', 'male'), ('?', 'not provided')], default='?', max_length=1, verbose_name='gender')),
                ('unique_url', models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='random GUID for URLs')),
                ('paid_offline', models.BooleanField(default=False, verbose_name='paid offline')),
                ('order_reference', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='order.Order')),
            ],
        ),
        migrations.CreateModel(
            name='CTSRider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name='Athlete Name')),
            ],
        ),
        migrations.CreateModel(
            name='CTSRiderPosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance_from_start', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Distance from start')),
                ('timestamp', models.DateTimeField(verbose_name='Timestamp')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Latitude')),
                ('lon', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Longitude')),
                ('rider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bullets.CTSRider')),
            ],
            options={
                'get_latest_by': 'timestamp',
            },
        ),
        migrations.CreateModel(
            name='CTSVehicle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(verbose_name='Vehicle Number')),
                ('name', models.CharField(max_length=300, verbose_name='Vehicle Name')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='CTSVehiclePosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(verbose_name='Time Stamp')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Latitude')),
                ('lon', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Longitude')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bullets.CTSVehicle')),
            ],
            options={
                'get_latest_by': 'timestamp',
            },
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='title')),
                ('extra_title', models.CharField(blank=True, max_length=100, null=True, verbose_name='extra title text (not in link)')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='title')),
                ('redirect_to', models.URLField(blank=True, null=True, verbose_name='redirection story - where to go?')),
                ('story', models.TextField(blank=True, null=True, verbose_name='story')),
                ('date_added', models.DateField(auto_now_add=True, verbose_name='date added')),
                ('display_after', models.DateField(verbose_name='publish on')),
                ('display_until', models.DateField(blank=True, null=True, verbose_name='remove from site on')),
                ('front_page', models.BooleanField(default=False, verbose_name='feature on front page')),
            ],
            options={
                'verbose_name': 'news story',
                'verbose_name_plural': 'news stories',
            },
        ),
        migrations.CreateModel(
            name='SiteValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TdBLeaderBoard_Entry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_id', models.PositiveIntegerField(verbose_name='Segment ID')),
                ('athlete_id', models.PositiveIntegerField(verbose_name='Athlete ID')),
                ('activity_id', models.PositiveIntegerField(verbose_name='Activity ID')),
                ('athlete_name', models.CharField(max_length=300, verbose_name='Athlete Name')),
                ('time_taken', models.DurationField(verbose_name='Time Taken')),
                ('date_completed', models.DateField(verbose_name='Date completed')),
            ],
            options={
                'verbose_name': 'TdB Leaderboard Entry',
                'verbose_name_plural': 'TdB Leaderboard Entries',
            },
        ),
        migrations.CreateModel(
            name='TdBStage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Stage name')),
                ('stage_type', models.CharField(blank=True, max_length=200, null=True, verbose_name='Stage type')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('valid_from', models.DateField(verbose_name='Valid from')),
                ('valid_until', models.DateField(verbose_name='Valid until')),
                ('long_route', models.PositiveIntegerField(blank=True, null=True, verbose_name='Long route ID')),
                ('medium_route', models.PositiveIntegerField(blank=True, null=True, verbose_name='Medium route ID')),
                ('short_route', models.PositiveIntegerField(blank=True, null=True, verbose_name='Short route ID')),
                ('social_route', models.PositiveIntegerField(blank=True, null=True, verbose_name='Social route ID')),
                ('long_distance', models.PositiveIntegerField(blank=True, null=True, verbose_name='Long distance')),
                ('medium_distance', models.PositiveIntegerField(blank=True, null=True, verbose_name='Medium distance')),
                ('short_distance', models.PositiveIntegerField(blank=True, null=True, verbose_name='Short distance')),
                ('social_distance', models.PositiveIntegerField(blank=True, null=True, verbose_name='Social distance')),
                ('hilly_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Hilly segment ID')),
                ('flat_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Flat segment ID')),
                ('overall_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Overall segment ID')),
                ('ss_hilly_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Super Social hilly segment ID')),
                ('ss_flat_segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Super Social flat segment ID')),
            ],
            options={
                'verbose_name': 'TdB Stage',
                'verbose_name_plural': 'TdB Stages',
            },
        ),
        migrations.CreateModel(
            name='VeloVolunteer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=200, verbose_name='email address')),
                ('name', models.CharField(blank=True, help_text='Your name', max_length=200, verbose_name='name')),
                ('address', models.TextField(help_text='Your address', verbose_name='address')),
                ('volunteer_type', models.CharField(choices=[('r', 'rider'), ('n', 'non-rider')], default='r', max_length=1)),
                ('entered_velo', models.BooleanField(verbose_name='have you entered the Velo?')),
                ('average_speed', models.CharField(blank=True, max_length=10, verbose_name='expected average speed for 100mile ride (mph)')),
                ('kit_sex', models.CharField(choices=[('m', 'male-fit'), ('f', 'female-fit')], default='m', max_length=1, verbose_name='do you want male or female-fit kit?')),
                ('jersey_size', models.CharField(choices=[('xs', 'X Small'), ('s', 'Small'), ('m', 'Medium'), ('l', 'Large'), ('xl', 'X Large'), ('xxl', 'XX Large'), ('xxxl', 'XXX Large')], max_length=4, verbose_name='jersey size')),
                ('short_size', models.CharField(choices=[('xs', 'X Small'), ('s', 'Small'), ('m', 'Medium'), ('l', 'Large'), ('xl', 'X Large'), ('xxl', 'XX Large'), ('xxxl', 'XXX Large')], max_length=4, verbose_name='bib short size')),
                ('tshirt_size', models.CharField(choices=[('xs', 'X Small'), ('s', 'Small'), ('m', 'Medium'), ('l', 'Large'), ('xl', 'X Large'), ('xxl', 'XX Large'), ('xxxl', 'XXX Large')], max_length=4, verbose_name='t-shirt size')),
                ('drive_van', models.BooleanField(verbose_name='are you willing to drive a van?')),
                ('drive_bus', models.BooleanField(verbose_name='are you willing to drive a minibus?')),
                ('contact_no', models.CharField(max_length=100, verbose_name='contact number')),
                ('unique_ref', models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='random uuid for emails')),
                ('bullet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bullets.Bullet')),
            ],
        ),
    ]
