# Generated by Django 4.2.10 on 2024-06-15 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geos_py', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('codename', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'auth_permission',
            },
        ),
    ]
