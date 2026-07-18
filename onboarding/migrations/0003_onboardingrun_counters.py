"""Add completed_steps and total_steps counters to OnboardingRun."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("onboarding", "0002_onboarding_rls")]

    operations = [
        migrations.AddField(
            model_name="onboardingrun",
            name="completed_steps",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="onboardingrun",
            name="total_steps",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
