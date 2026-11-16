from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_accounts_user_username_case_insensitive_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="location",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="profile",
            name="learning_goal",
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
