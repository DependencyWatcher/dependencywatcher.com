"""empty message

Revision ID: 1f23788d2c8e
Revises: None
Create Date: 2015-02-23 07:54:07.279715

"""

# revision identifiers, used by Alembic.
revision = '1f23788d2c8e'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    role = op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=64), nullable=False),
    sa.Column('description', sa.Unicode(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.bulk_insert(role, [
        {"id": 1, "name": u"admin", "description": u"Administrator with full set of permissions"},
        {"id": 2, "name": u"editor", "description": u"Blog editor"}
    ])
    op.create_table('blog_post',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.Unicode(length=128), nullable=True),
    sa.Column('author', sa.Unicode(length=255), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blog_post_slug'), 'blog_post', ['slug'], unique=False)
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=255), nullable=True),
    sa.Column('email', sa.Unicode(length=255), nullable=False),
    sa.Column('avatar_sm', sa.Text(), nullable=True),
    sa.Column('password', sa.Unicode(length=255), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('activation_code', sa.String(length=32), nullable=True),
    sa.Column('recovery_code', sa.String(length=32), nullable=True),
    sa.Column('github', sa.Text(), nullable=True),
    sa.Column('bitbucket', sa.Text(), nullable=True),
    sa.Column('plan', sa.Integer(), nullable=True),
    sa.Column('api_key', sa.String(length=36), nullable=True),
    sa.Column('is_ldap', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('license',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=255), nullable=False),
    sa.Column('normalized', sa.Unicode(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('repository',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('url', sa.Unicode(length=255), nullable=False),
    sa.Column('auth_type', sa.Integer(), nullable=True),
    sa.Column('username', sa.Unicode(length=255), nullable=True),
    sa.Column('password', sa.Unicode(length=255), nullable=True),
    sa.Column('ssh_key', sa.Text(), nullable=True),
    sa.Column('last_update', sa.DateTime(), nullable=True),
    sa.Column('last_view', sa.DateTime(), nullable=True),
    sa.Column('deleted', sa.Boolean(), nullable=True),
    sa.Column('fetched', sa.Boolean(), nullable=True),
    sa.Column('parsed', sa.Boolean(), nullable=True),
    sa.Column('private', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repository_url'), 'repository', ['url'], unique=False)
    op.create_table('key_pair',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('private', sa.Text(), nullable=True),
    sa.Column('public', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('post_tags',
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['blog_post.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE'),
    sa.UniqueConstraint('tag_id', 'post_id')
    )
    op.create_table('user_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('deps', sa.Integer(), nullable=True),
    sa.Column('alerts', sa.Integer(), nullable=True),
    sa.Column('alerts_f', sa.Integer(), nullable=True),
    sa.Column('oldver', sa.Integer(), nullable=True),
    sa.Column('oldver_f', sa.Integer(), nullable=True),
    sa.Column('oldver_maj', sa.Integer(), nullable=True),
    sa.Column('oldver_min', sa.Integer(), nullable=True),
    sa.Column('oldver_bug', sa.Integer(), nullable=True),
    sa.Column('recommends', sa.Integer(), nullable=True),
    sa.Column('recommends_f', sa.Integer(), nullable=True),
    sa.Column('licissues', sa.Integer(), nullable=True),
    sa.Column('licissues_f', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('avatar',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('image128', sa.LargeBinary(), nullable=True),
    sa.Column('image32', sa.LargeBinary(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('user_stats_prev',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('deps', sa.Integer(), nullable=True),
    sa.Column('alerts', sa.Integer(), nullable=True),
    sa.Column('alerts_f', sa.Integer(), nullable=True),
    sa.Column('oldver', sa.Integer(), nullable=True),
    sa.Column('oldver_f', sa.Integer(), nullable=True),
    sa.Column('oldver_maj', sa.Integer(), nullable=True),
    sa.Column('oldver_min', sa.Integer(), nullable=True),
    sa.Column('oldver_bug', sa.Integer(), nullable=True),
    sa.Column('recommends', sa.Integer(), nullable=True),
    sa.Column('recommends_f', sa.Integer(), nullable=True),
    sa.Column('licissues', sa.Integer(), nullable=True),
    sa.Column('licissues_f', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('user_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('alerts_NV', sa.Boolean(), nullable=True),
    sa.Column('alerts_NL', sa.Boolean(), nullable=True),
    sa.Column('weekly', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('dependency',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Unicode(length=128), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('context', sa.String(length=64), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('version', sa.Unicode(length=36), nullable=True),
    sa.Column('license_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.Unicode(length=1024), nullable=True),
    sa.ForeignKeyConstraint(['license_id'], ['license.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'context')
    )
    op.create_table('user_roles',
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.UniqueConstraint('role_id', 'user_id')
    )
    op.create_table('dependency_reference',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version', sa.Unicode(length=36)),
    sa.Column('file', sa.Unicode(length=255), nullable=False),
    sa.Column('dependency_id', sa.Integer(), nullable=True),
    sa.Column('repository_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['dependency_id'], ['dependency.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['repository_id'], ['repository.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('file', 'dependency_id', 'repository_id')
    )
    op.create_table('alert',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('read', sa.Boolean(), nullable=True),
    sa.Column('sent', sa.Boolean(), nullable=True),
    sa.Column('fixed', sa.Boolean(), nullable=True),
    sa.Column('release_type', sa.Integer(), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['reference_id'], ['dependency_reference.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('type', 'reference_id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('alert')
    op.drop_table('dependency_reference')
    op.drop_table('user_roles')
    op.drop_table('dependency')
    op.drop_table('user_settings')
    op.drop_table('user_stats_prev')
    op.drop_table('avatar')
    op.drop_table('user_stats')
    op.drop_table('post_tags')
    op.drop_table('key_pair')
    op.drop_index(op.f('ix_repository_url'), table_name='repository')
    op.drop_table('repository')
    op.drop_table('license')
    op.drop_table('user')
    op.drop_index(op.f('ix_blog_post_slug'), table_name='blog_post')
    op.drop_table('blog_post')
    op.drop_table('role')
    op.drop_table('tag')
    ### end Alembic commands ###
