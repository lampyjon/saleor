# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-28 17:52
from __future__ import unicode_literals

from django.db import migrations
import django_prices.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0043_auto_20171207_0839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=django_prices.models.PriceField(currency='GBP', decimal_places=2, max_digits=12, verbose_name='price'),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='price_override',
            field=django_prices.models.PriceField(blank=True, currency='GBP', decimal_places=2, max_digits=12, null=True, verbose_name='price override'),
        ),
        migrations.AlterField(
            model_name='stock',
            name='cost_price',
            field=django_prices.models.PriceField(blank=True, currency='GBP', decimal_places=2, max_digits=12, null=True, verbose_name='cost price'),
        ),
    ]
