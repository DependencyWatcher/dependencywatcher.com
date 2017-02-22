"""empty message

Revision ID: 2ca57a8203ba
Revises: 435c1fb10826
Create Date: 2015-09-23 13:56:48.539989

"""

# revision identifiers, used by Alembic.
revision = '2ca57a8203ba'
down_revision = '435c1fb10826'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_settings', sa.Column('unstable_vers', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_settings', 'unstable_vers')
    ### end Alembic commands ###
