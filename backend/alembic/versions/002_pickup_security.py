"""Add pickup security: tag_type, awaiting_id_scan, pickup audit columns

Revision ID: 002_pickup_security
Revises: 001_remove_vapid
Create Date: 2026-04-04

Schema changes:
  rfid_tags
    + tag_type  VARCHAR/ENUM  NOT NULL DEFAULT 'bag'   (bag | id_card)

  rfid_scan_events
    + pickup_scanned_by_student_id  UUID  NULLABLE  FK → students.id

  bag_status_logs
    + pickup_scanned_by_student  UUID  NULLABLE  FK → students.id

  Enum additions (PostgreSQL only):
    scantypeenum   += pickup_bag, pickup_id
    bagstatusenum  += awaiting_id_scan
    tagtypeenum     = new type (bag, id_card)
"""
from alembic import op
import sqlalchemy as sa


revision = '002_pickup_security'
down_revision = '001_remove_vapid'
branch_labels = None
depends_on = None


def _dialect():
    return op.get_bind().dialect.name


def upgrade() -> None:
    is_pg = _dialect() == "postgresql"

    # ── 1. PostgreSQL: create/extend enum types ───────────────────────────
    if is_pg:
        op.execute("ALTER TYPE scantypeenum  ADD VALUE IF NOT EXISTS 'pickup_bag'")
        op.execute("ALTER TYPE scantypeenum  ADD VALUE IF NOT EXISTS 'pickup_id'")
        op.execute("ALTER TYPE bagstatusenum ADD VALUE IF NOT EXISTS 'awaiting_id_scan'")
        op.execute(
            "DO $$ BEGIN "
            "  CREATE TYPE tagtypeenum AS ENUM ('bag','id_card'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; "
            "END $$"
        )

    # ── 2. rfid_tags.tag_type ─────────────────────────────────────────────
    with op.batch_alter_table("rfid_tags") as b:
        if is_pg:
            b.add_column(sa.Column(
                "tag_type",
                sa.Enum("bag", "id_card", name="tagtypeenum", create_type=False),
                nullable=False,
                server_default="bag",
            ))
        else:
            b.add_column(sa.Column(
                "tag_type",
                sa.String(20),
                nullable=False,
                server_default="bag",
            ))

    # ── 3. rfid_scan_events.pickup_scanned_by_student_id ─────────────────
    with op.batch_alter_table("rfid_scan_events") as b:
        b.add_column(sa.Column(
            "pickup_scanned_by_student_id",
            sa.String(36) if not is_pg else sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
        ))
        if is_pg:
            b.create_foreign_key(
                "fk_scan_event_pickup_student",
                "students", ["pickup_scanned_by_student_id"], ["id"]
            )

    # ── 4. bag_status_logs.pickup_scanned_by_student ──────────────────────
    with op.batch_alter_table("bag_status_logs") as b:
        b.add_column(sa.Column(
            "pickup_scanned_by_student",
            sa.String(36) if not is_pg else sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
        ))
        if is_pg:
            b.create_foreign_key(
                "fk_status_log_pickup_student",
                "students", ["pickup_scanned_by_student"], ["id"]
            )


def downgrade() -> None:
    is_pg = _dialect() == "postgresql"

    with op.batch_alter_table("bag_status_logs") as b:
        if is_pg:
            b.drop_constraint("fk_status_log_pickup_student", type_="foreignkey")
        b.drop_column("pickup_scanned_by_student")

    with op.batch_alter_table("rfid_scan_events") as b:
        if is_pg:
            b.drop_constraint("fk_scan_event_pickup_student", type_="foreignkey")
        b.drop_column("pickup_scanned_by_student_id")

    with op.batch_alter_table("rfid_tags") as b:
        b.drop_column("tag_type")

    if is_pg:
        op.execute("DROP TYPE IF EXISTS tagtypeenum")
