"""add settings table

Revision ID: a51ed05cd6af
Revises: [revisi_sebelumnya]  # ganti dengan revisi yang benar
Create Date: 2026-02-21 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a51ed05cd6af'
down_revision = "0feea2c0fcdd"  # <-- GANTI DENGAN REVISI SEBELUMNYA YANG BENAR
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_settings_key')
    )

def downgrade():
    op.drop_table('settings')