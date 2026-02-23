"""add salary nik periode unique

Revision ID: a1b2c3d4e5f6
Revises: 9a1c6de98a5d
Create Date: 2026-02-19

"""
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "9a1c6de98a5d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_salary_nik_periode",
        "salaries",
        ["nik", "periode"],
    )


def downgrade():
    op.drop_constraint("uq_salary_nik_periode", "salaries", type_="unique")
