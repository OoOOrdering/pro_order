from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0002_user_email_verification_token_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="social_id",
        ),
        migrations.RemoveField(
            model_name="user",
            name="social_type",
        ),
    ]
