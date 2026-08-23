from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="DomainEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("team_id", models.UUIDField()),
                ("aggregate_type", models.CharField(max_length=80)),
                ("aggregate_id", models.UUIDField()),
                ("event_type", models.CharField(max_length=120)),
                ("payload", models.JSONField(default=dict)),
                ("correlation_id", models.UUIDField()),
                ("idempotency_key", models.CharField(max_length=255)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["team_id", "aggregate_type", "aggregate_id"],
                        name="mizan_domai_team_id_d68cec_idx",
                    ),
                    models.Index(fields=["correlation_id"], name="mizan_domai_correla_1a3ae3_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "idempotency_key"),
                        name="pusula_unique_team_idempotency",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="OutboxMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("team_id", models.UUIDField()),
                ("topic", models.CharField(max_length=120)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="outbox",
                        to="mizan.domainevent",
                    ),
                ),
            ],
        ),
    ]
