# Generated by Django 5.2 on 2025-05-07 11:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordinaryusermodel',
            name='car_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.carmodelsmodel', verbose_name='Car model'),
        ),
        migrations.AddField(
            model_name='ordinaryusermodel',
            name='username',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Username'),
        ),
        migrations.AlterField(
            model_name='ordinaryusermodel',
            name='first_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='First Name'),
        ),
        migrations.AlterField(
            model_name='ordinaryusermodel',
            name='last_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Last Name'),
        ),
    ]
