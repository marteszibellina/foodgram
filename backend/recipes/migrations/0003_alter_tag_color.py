# Generated by Django 3.2 on 2025-02-27 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_tag_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(default='#FFFFFF', max_length=7, unique=True, verbose_name='Цвет тега'),
        ),
    ]
