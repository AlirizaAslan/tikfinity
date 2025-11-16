from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tiktok_live', '0006_userpoints_pointstransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatbotSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_enabled', models.BooleanField(default=False)),
                ('max_messages_per_15_seconds', models.IntegerField(default=2)),
                ('enable_streamerbot', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ChatbotMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', models.CharField(choices=[('help', 'Help'), ('show_global_commands', 'Show global commands'), ('show_subscriber_commands', 'Show subscriber commands'), ('show_user_commands', 'Show user personal commands'), ('points_info_top100', 'Points Information (Top 100)'), ('points_info_other', 'Points Information (Not in top 100)'), ('points_transfer_success', 'Points Transfer - Success'), ('points_transfer_syntax', 'Points Transfer - Incorrect syntax'), ('points_transfer_insufficient', 'Points Transfer - Not enough credits'), ('points_transfer_notfound', 'Points Transfer - Receiver not found'), ('wheel_insufficient', 'Wheel of Fortune - Not enough credits'), ('wheel_no_win', 'Wheel of Fortune - No win'), ('wheel_cooldown', 'Wheel of Fortune - Waiting time'), ('wheel_win', 'Wheel of Fortune - Win'), ('level_up', 'Level Up'), ('action_queue_full', 'My Actions - Queue full'), ('action_insufficient', 'My Actions - Not enough credits'), ('action_level_low', 'My Actions - Level too low'), ('tts_insufficient', 'TTS Speak - Not enough credits'), ('song_insufficient', 'Song Request - Not enough credits'), ('song_not_found', 'Song Request - Not found'), ('song_queue_full', 'Song Request - Queue full'), ('song_user_limit', 'Song Request - User limit'), ('song_duplicate', 'Song Request - Already in queue'), ('song_explicit', 'Song Request - Explicit content'), ('song_added', 'Song Request - Added'), ('song_revoked', 'Song Request - Revoked'), ('song_skip_denied', 'Song Request - Skip not allowed')], max_length=50)),
                ('scenario', models.CharField(blank=True, max_length=200)),
                ('message_text', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'command')},
            },
        ),
        migrations.CreateModel(
            name='ChatbotLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
