"""create salaries table

Revision ID: 9a1c6de98a5d
Revises: 5390a2232e26
Create Date: 2026-02-17 20:44:56.123456

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9a1c6de98a5d'
down_revision = '5390a2232e26'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'salaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nik', sa.String(length=20), nullable=False),
        sa.Column('periode', sa.Date(), nullable=False),
        sa.Column('gaji_pokok', sa.Numeric(10, 2), nullable=True),
        sa.Column('tunj_berkala', sa.Numeric(10, 2), nullable=True),
        sa.Column('tunj_jabatan', sa.Numeric(10, 2), nullable=True),
        sa.Column('tunj_kerajinan', sa.Numeric(10, 2), nullable=True),
        sa.Column('tunj_pph21', sa.Numeric(10, 2), nullable=True),
        sa.Column('uang_shift', sa.Numeric(10, 2), nullable=True),
        sa.Column('uang_makan', sa.Numeric(10, 2), nullable=True),
        sa.Column('ins_prod', sa.Numeric(10, 2), nullable=True),
        sa.Column('bonus_skill', sa.Numeric(10, 2), nullable=True),
        sa.Column('ins_hadir', sa.Numeric(10, 2), nullable=True),
        sa.Column('kompensasi_cuti', sa.Numeric(10, 2), nullable=True),
        sa.Column('lainnya1', sa.Numeric(10, 2), nullable=True),
        sa.Column('lainnya2', sa.Numeric(10, 2), nullable=True),
        sa.Column('lainnya3', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_salaries_nik'), 'salaries', ['nik'], unique=False)
    op.create_index(op.f('ix_salaries_periode'), 'salaries', ['periode'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_salaries_periode'), table_name='salaries')
    op.drop_index(op.f('ix_salaries_nik'), table_name='salaries')
    op.drop_table('salaries')