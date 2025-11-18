"""add_user_id_to_applications

Revision ID: f1fe2de2d184
Revises: ef9073f75fdf
Create Date: 2025-11-18 17:18:05.250510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1fe2de2d184'
down_revision: Union[str, Sequence[str], None] = 'ef9073f75fdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add user_id to applications."""
    # Add user_id column (nullable for existing records)
    op.add_column('applications', sa.Column('user_id', sa.Integer(), nullable=True))

    # Create foreign key constraint
    with op.batch_alter_table('applications') as batch_op:
        batch_op.create_foreign_key(
            'fk_applications_user_id',
            'users',
            ['user_id'],
            ['id']
        )


def downgrade() -> None:
    """Downgrade schema - remove user_id from applications."""
    # Drop foreign key constraint
    with op.batch_alter_table('applications') as batch_op:
        batch_op.drop_constraint('fk_applications_user_id', type_='foreignkey')

    # Drop user_id column
    op.drop_column('applications', 'user_id')
