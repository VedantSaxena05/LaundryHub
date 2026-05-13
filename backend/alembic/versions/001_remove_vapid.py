"""remove web_push_subscription from students

Revision ID: 001_remove_vapid
Revises:
Create Date: 2026-04-04

Removes the web_push_subscription column that was used for VAPID/Web Push.
Notifications are now sent exclusively via Firebase Cloud Messaging (FCM).
The fcm_token column is retained.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_remove_vapid'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the VAPID web push subscription column.
    # This is safe to run even if the column does not exist yet
    # (e.g. on a fresh database).
    with op.batch_alter_table('students') as batch_op:
        try:
            batch_op.drop_column('web_push_subscription')
        except Exception:
            pass  # Column may not exist on fresh installs


def downgrade() -> None:
    # Re-add the column for rollback (nullable so existing rows are not broken)
    with op.batch_alter_table('students') as batch_op:
        batch_op.add_column(sa.Column('web_push_subscription', sa.Text(), nullable=True))
