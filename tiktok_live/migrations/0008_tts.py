from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tiktok_live', '0007_chatbot'),
    ]

    operations = [
        migrations.CreateModel(
            name='TTSSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_enabled', models.BooleanField(default=False)),
                ('language', models.CharField(default='tr-TR', max_length=10)),
                ('voice', models.CharField(default='default', max_length=50)),
                ('random_voice', models.BooleanField(default=False)),
                ('default_speed', models.IntegerField(default=50)),
                ('default_pitch', models.IntegerField(default=50)),
                ('volume', models.IntegerField(default=100)),
                ('allow_all_users', models.BooleanField(default=True)),
                ('allow_followers', models.BooleanField(default=True)),
                ('allow_subscribers', models.BooleanField(default=True)),
                ('allow_moderators', models.BooleanField(default=True)),
                ('allow_team_members', models.BooleanField(default=True)),
                ('team_members_min_level', models.IntegerField(default=1)),
                ('allow_top_gifters', models.BooleanField(default=True)),
                ('top_gifters_n', models.IntegerField(default=3)),
                ('allow_specific_users', models.BooleanField(default=True)),
                ('comment_type', models.CharField(choices=[('any', 'Any comment'), ('dot', 'Comments starting with dot (.)'), ('slash', 'Comments starting with slash (/)'), ('command', 'Comments starting with Command')], default='any', max_length=20)),
                ('special_command', models.CharField(blank=True, max_length=20)),
                ('charge_points', models.BooleanField(default=False)),
                ('cost_per_message', models.IntegerField(default=5)),
                ('user_cooldown', models.IntegerField(default=0)),
                ('max_queue_length', models.IntegerField(default=5)),
                ('max_comment_length', models.IntegerField(default=300)),
                ('filter_letter_spam', models.BooleanField(default=True)),
                ('filter_mentions', models.BooleanField(default=False)),
                ('filter_commands', models.BooleanField(default=False)),
                ('message_template', models.CharField(default='{comment}', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TTSSpecialUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tiktok_username', models.CharField(max_length=100)),
                ('is_allowed', models.BooleanField(default=True)),
                ('voice', models.CharField(default='default', max_length=50)),
                ('speed', models.IntegerField(default=50)),
                ('pitch', models.IntegerField(default=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'tiktok_username')},
            },
        ),
        migrations.CreateModel(
            name='TTSLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tiktok_username', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
