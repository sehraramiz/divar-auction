"""Initial

Revision ID: 55a590a81203
Revises: 
Create Date: 2024-12-21 17:46:32.990524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55a590a81203'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('auctions',
    sa.Column('post_token', sa.String(length=20), nullable=False),
    sa.Column('seller_id', sa.String(length=16), nullable=False),
    sa.Column('selected_bid', sa.Uuid(), nullable=True),
    sa.Column('starting_price', sa.BigInteger(), nullable=False),
    sa.Column('post_title', sa.String(length=100), nullable=False),
    sa.Column('uid', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('uid', name='auction_pk')
    )
    op.create_table('bids',
    sa.Column('auction_id', sa.Uuid(), nullable=False),
    sa.Column('bidder_id', sa.String(length=16), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('uid', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('uid', name='bid_pk')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('bids')
    op.drop_table('auctions')
    # ### end Alembic commands ###
