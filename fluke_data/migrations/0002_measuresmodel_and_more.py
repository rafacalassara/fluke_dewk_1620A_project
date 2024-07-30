# Generated by Django 5.0.7 on 2024-07-30 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fluke_data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeasuresModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pn_sn', models.CharField(max_length=200)),
                ('temperature', models.FloatField()),
                ('humidity', models.FloatField()),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.RenameModel(
            old_name='Thermohygrometer',
            new_name='ThermohygrometerModel',
        ),
    ]
