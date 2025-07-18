"""add_score_to_recommendations

Revision ID: 0f881ae96642
Revises: b6b5ca62c2d5
Create Date: 2025-02-26 23:10:18.122132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f881ae96642'
down_revision = 'b6b5ca62c2d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('score', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.drop_column('score')

    # ### end Alembic commands ###
