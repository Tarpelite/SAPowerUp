# Generated by Django 2.2 on 2019-05-08 07:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SAcore', '0006_auto_20190508_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='candidate',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='candidate', to='SAcore.Author'),
        ),
    ]
