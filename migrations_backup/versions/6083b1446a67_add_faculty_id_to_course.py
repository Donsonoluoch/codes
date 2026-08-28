"""Add faculty_id to course

Revision ID: 6083b1446a67
Revises: 
Create Date: 2025-07-26 09:57:09.974193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6083b1446a67'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### Adjusted Alembic commands ###
    # 1) Add faculty_id and give the FK a name
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('faculty_id', sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_course_faculty_id',   # ← named constraint
            'faculty',                # target table
            ['faculty_id'],           # local cols
            ['id']                    # remote cols
        )

    # 2) Add student.reg_no and name, alter is_deferred, and name the unique constraint
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('reg_no', sa.String(length=20), nullable=False)
        )
        batch_op.add_column(
            sa.Column('name', sa.String(length=100), nullable=False)
        )
        batch_op.alter_column(
            'is_deferred',
            existing_type=sa.INTEGER(),
            type_=sa.Boolean(),
            existing_nullable=False,
            existing_server_default=sa.text('0')
        )
        batch_op.create_unique_constraint(
            'uq_student_reg_no',      # ← named unique constraint
            ['reg_no']
        )
    # ### end Alembic commands ###


def downgrade():
    # ### Revert student changes first ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_constraint(
            'uq_student_reg_no',
            type_='unique'
        )
        batch_op.alter_column(
            'is_deferred',
            existing_type=sa.Boolean(),
            type_=sa.INTEGER(),
            existing_nullable=False,
            existing_server_default=sa.text('0')
        )
        batch_op.drop_column('name')
        batch_op.drop_column('reg_no')

    # ### Then revert course changes ###
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_course_faculty_id',
            type_='foreignkey'
        )
        batch_op.drop_column('faculty_id')
    # ### end Alembic commands ###
