"""update employees structure

Revision ID: 5390a2232e26
Revises: d4a8e26cb016
Create Date: 2026-02-17 19:11:49.542924

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5390a2232e26"
down_revision: Union[str, Sequence[str], None] = "d4a8e26cb016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hapus kolom yang tidak diperlukan
    op.drop_column('employees', 'umur')
    op.drop_column('employees', 'umur_rekrut')
    op.drop_column('employees', 'lama_bekerja')
    op.drop_column('employees', 'remaining')
    
    # Hapus juga kolom transfer_cash kalau masih ada
    try:
        op.drop_column('employees', 'transfer_cash')
    except Exception:
        pass  # Kolom mungkin sudah tidak ada


def downgrade() -> None:
    # Tambah kembali kolom yang dihapus (kalau perlu rollback)
    op.add_column('employees', sa.Column('umur', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('umur_rekrut', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('lama_bekerja', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('remaining', sa.Integer(), nullable=True))
    op.add_column('employees', sa.Column('transfer_cash', sa.String(length=10), nullable=True))
