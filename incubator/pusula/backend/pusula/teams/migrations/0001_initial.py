from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="Team",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("identity_subject", models.CharField(max_length=255)),
                (
                    "role",
                    models.CharField(
                        choices=[("owner", "Owner"), ("member", "Member"), ("viewer", "Viewer")],
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="teams.team",
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["identity_subject", "team"], name="teams_membe_identit_643a3d_idx")],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team", "identity_subject"),
                        name="pusula_unique_team_identity",
                    )
                ],
            },
        ),
    ]
