from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("mizan", "0002_goal_scope")]

    operations = [
        migrations.CreateModel(
            name="KnowledgeSource",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_id", models.UUIDField()),
                ("source_key", models.CharField(max_length=255)),
                ("locator", models.TextField()),
                ("authority", models.CharField(max_length=120)),
                ("observed_at", models.DateTimeField()),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("content_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "source_key"),
                        name="pusula_unique_team_source_key",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="KnowledgeClaimRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_id", models.UUIDField()),
                ("claim_key", models.CharField(max_length=255)),
                ("kind", models.CharField(max_length=24)),
                ("subject", models.CharField(max_length=255)),
                ("predicate", models.CharField(max_length=255)),
                ("value", models.TextField()),
                ("materiality", models.CharField(max_length=24)),
                ("evidence_keys", models.JSONField(default=list)),
                ("contradicts_claim_keys", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "claim_key"),
                        name="pusula_unique_team_claim_key",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="CapabilityGraphNode",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_id", models.UUIDField()),
                ("node_key", models.CharField(max_length=255)),
                ("node_type", models.CharField(max_length=24)),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "node_key"),
                        name="pusula_unique_team_capability_node",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="EvidenceArtifact",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_id", models.UUIDField()),
                ("evidence_key", models.CharField(max_length=255)),
                ("summary", models.TextField()),
                ("captured_at", models.DateTimeField()),
                ("valid_until", models.DateTimeField(blank=True, null=True)),
                ("data_class", models.CharField(max_length=24)),
                ("retention_days", models.PositiveIntegerField(blank=True, null=True)),
                ("payload_sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="evidence_artifacts",
                        to="mizan.knowledgesource",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "evidence_key"),
                        name="pusula_unique_team_evidence_key",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="CapabilityGraphRelationship",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_id", models.UUIDField()),
                ("relationship_key", models.CharField(max_length=255)),
                ("kind", models.CharField(max_length=24)),
                ("evidence_keys", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "source_node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="outgoing_relationships",
                        to="mizan.capabilitygraphnode",
                    ),
                ),
                (
                    "target_node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="incoming_relationships",
                        to="mizan.capabilitygraphnode",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "relationship_key"),
                        name="pusula_unique_team_capability_rel",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ContradictionResolutionRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("team_id", models.UUIDField()),
                ("resolution_key", models.CharField(max_length=255)),
                ("contradiction_claim_key", models.CharField(max_length=255)),
                ("summary", models.TextField()),
                ("evidence_keys", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("team_id", "resolution_key"),
                        name="pusula_unique_team_resolution_key",
                    )
                ],
            },
        ),
    ]
