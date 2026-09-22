import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_templatedownloadcode_templatedownloadlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='templatedownloadcode',
            name='device_type',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='downloaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='downloaded_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='downloaded_codes', to='core.eventcategory'),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='first_visited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='last_activity_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='last_page_viewed',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='time_spent_seconds',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='user_agent',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='templatedownloadcode',
            name='visit_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
