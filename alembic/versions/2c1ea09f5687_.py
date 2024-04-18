"""empty message

Revision ID: 2c1ea09f5687
Revises: 7d2b3378bffa
Create Date: 2024-04-18 13:00:34.318041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c1ea09f5687'
down_revision: Union[str, None] = '7d2b3378bffa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task', sa.Column('create_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True))
    op.add_column('task', sa.Column('execution_time', sa.Interval(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('task', 'execution_time')
    op.drop_column('task', 'create_at')
    # ### end Alembic commands ###