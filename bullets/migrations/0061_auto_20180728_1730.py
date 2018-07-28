# Generated by Django 2.0.5 on 2018-07-28 16:30

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('bullets', '0060_bigbulletrider'),
    ]

    operations = [
        migrations.CreateModel(
            name='FredLeaderBoard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strava_activity_id', models.CharField(max_length=50, verbose_name='Strava Activity ID')),
                ('distance', models.PositiveIntegerField(verbose_name='Distance')),
                ('elevation', models.FloatField(verbose_name='Elevation')),
                ('start_date', models.DateTimeField(verbose_name='Activity Date')),
                ('ratio', models.FloatField(verbose_name='elevation per mile')),
            ],
        ),
        migrations.CreateModel(
            name='FredRider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('email', models.EmailField(max_length=200, verbose_name='email address')),
                ('date_added', models.DateField(auto_now_add=True, verbose_name='date created')),
                ('email_checked', models.DateField(blank=True, null=True, verbose_name='date email confirmed')),
                ('email_check_ref', models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='random uuid for email confirmation')),
                ('access_token', models.CharField(max_length=500, verbose_name='Strava access token')),
                ('checked_upto_date', models.DateTimeField(blank=True, null=True, verbose_name='Checked up to')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FredHighLeaderBoard',
            fields=[
                ('fredleaderboard_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='bullets.FredLeaderBoard')),
            ],
            options={
                'ordering': ['-elevation'],
            },
            bases=('bullets.fredleaderboard',),
        ),
        migrations.CreateModel(
            name='FredLowLeaderBoard',
            fields=[
                ('fredleaderboard_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='bullets.FredLeaderBoard')),
            ],
            options={
                'ordering': ['ratio'],
            },
            bases=('bullets.fredleaderboard',),
        ),
        migrations.AddField(
            model_name='fredleaderboard',
            name='rider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bullets.FredRider'),
        ),
    ]
