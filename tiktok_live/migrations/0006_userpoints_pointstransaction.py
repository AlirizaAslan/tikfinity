# Generated manually
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tiktok_live', '0005_countdowntimer_pointshalving_pointssettings'),
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
            name='PointsTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('gift', 'Gift Received'), ('follow', 'Follow'), ('like', 'Like'), ('comment', 'Comment'), ('share', 'Share'), ('manual', 'Manual Adjustment'), ('bonus', 'Bonus Points'), ('penalty', 'Penalty')], max_length=20)),
                ('points_change', models.IntegerField()),
                ('description', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user_points', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tiktok_live.userpoints')),
            ],
        ),
    ]
