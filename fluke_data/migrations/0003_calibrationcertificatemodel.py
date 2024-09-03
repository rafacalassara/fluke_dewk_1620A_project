# Generated by Django 5.0.7 on 2024-09-03 13:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fluke_data', '0002_thermohygrometermodel_last_connection_attempt'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalibrationCertificateModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calibration_date', models.DateField()),
                ('next_calibration_date', models.DateField()),
                ('certificate_number', models.CharField(max_length=100)),
                ('temp_point_1', models.FloatField()),
                ('temp_correction_1', models.FloatField()),
                ('temp_point_2', models.FloatField()),
                ('temp_correction_2', models.FloatField()),
                ('temp_point_3', models.FloatField()),
                ('temp_correction_3', models.FloatField()),
                ('humidity_point_1', models.FloatField()),
                ('humidity_correction_1', models.FloatField()),
                ('humidity_point_2', models.FloatField()),
                ('humidity_correction_2', models.FloatField()),
                ('humidity_point_3', models.FloatField()),
                ('humidity_correction_3', models.FloatField()),
                ('temp_uncertainty', models.FloatField()),
                ('humidity_uncertainty', models.FloatField()),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calibrations', to='fluke_data.thermohygrometermodel')),
            ],
            options={
                'ordering': ['-calibration_date'],
            },
        ),
    ]