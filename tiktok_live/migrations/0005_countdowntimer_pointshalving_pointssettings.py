# Generated manually
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tiktok_live', '0004_auto_20251111_2242'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPoints',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tiktok_username', models.CharField(max_length=100)),
                ('tiktok_user_id', models.CharField(blank=True, max_length=100)),
                ('display_name', models.CharField(blank=True, max_length=200)),
                ('profile_picture', models.URLField(blank=True)),
                ('points_total', models.IntegerField(default=0)),
                ('points_level', models.IntegerField(default=0)),
                ('level', models.IntegerField(default=1)),
                ('total_gifts_sent', models.IntegerField(default=0)),
                ('total_coins_spent', models.IntegerField(default=0)),
                ('first_activity', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'tiktok_username')},
            },
        ),
        migrations.CreateModel(
            name='PointsSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_users', models.IntegerField(default=2500)),
                ('points_per_gift', models.IntegerField(default=10)),
                ('points_per_follow', models.IntegerField(default=50)),
                ('points_per_like', models.IntegerField(default=1)),
                ('points_per_comment', models.IntegerField(default=5)),
                ('points_per_share', models.IntegerField(default=25)),
                ('level_up_threshold', models.IntegerField(default=100)),
                ('enable_points_system', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CountdownTimer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('widget_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('default_start_value', models.IntegerField(default=10)),
                ('current_value', models.IntegerField(default=10)),
                ('is_running', models.BooleanField(default=False)),
                ('is_paused', models.BooleanField(default=False)),
                ('expire_action', models.CharField(choices=[('none', 'Do Nothing'), ('end_stream', 'End Stream'), ('play_sound', 'Play Sound'), ('show_message', 'Show Message'), ('trigger_action', 'Trigger Action')], default='none', max_length=20)),
                ('expire_action_data', models.JSONField(blank=True, default=dict)),
                ('seconds_per_coin', models.FloatField(default=1.0)),
                ('seconds_per_subscribe', models.FloatField(default=300.0)),
                ('seconds_per_follow', models.FloatField(default=0.0)),
                ('seconds_per_share', models.FloatField(default=0.0)),
                ('seconds_per_like', models.FloatField(default=0.0)),
                ('seconds_per_chat', models.FloatField(default=0.0)),
                ('enable_multiplier', models.BooleanField(default=False)),
                ('multiplier_value', models.FloatField(default=1.5)),
                ('shortcut_start_pause', models.CharField(blank=True, max_length=50)),
                ('shortcut_increase', models.CharField(blank=True, max_length=50)),
                ('shortcut_reduce', models.CharField(blank=True, max_length=50)),
                ('shortcut_step', models.IntegerField(default=1)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('paused_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PointsHalving',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.IntegerField(default=50)),
                ('executed_at', models.DateTimeField(auto_now_add=True)),
                ('affected_users', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
