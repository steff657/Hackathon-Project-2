from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_savedslot"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("paid", "Paid"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="stripe_checkout_session_id",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
