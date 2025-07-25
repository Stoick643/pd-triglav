"""Initial database schema with all models

Revision ID: e419c8494fed
Revises: 
Create Date: 2025-07-26 15:22:56.509103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e419c8494fed'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('role', sa.Enum('PENDING', 'MEMBER', 'TRIP_LEADER', 'ADMIN', name='userrole'), nullable=False),
    sa.Column('is_approved', sa.Boolean(), nullable=False),
    sa.Column('google_id', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('emergency_contact', sa.String(length=200), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('google_id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('trips',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('destination', sa.String(length=200), nullable=False),
    sa.Column('trip_date', sa.Date(), nullable=False),
    sa.Column('meeting_time', sa.Time(), nullable=True),
    sa.Column('meeting_point', sa.String(length=200), nullable=True),
    sa.Column('return_time', sa.Time(), nullable=True),
    sa.Column('difficulty', sa.Enum('EASY', 'MODERATE', 'DIFFICULT', 'EXPERT', name='tripdifficulty'), nullable=False),
    sa.Column('max_participants', sa.Integer(), nullable=True),
    sa.Column('equipment_needed', sa.Text(), nullable=True),
    sa.Column('cost_per_person', sa.Float(), nullable=True),
    sa.Column('status', sa.Enum('ANNOUNCED', 'CANCELLED', 'COMPLETED', name='tripstatus'), nullable=False),
    sa.Column('leader_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['leader_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trip_participants',
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('CONFIRMED', 'WAITLISTED', 'CANCELLED', name='participantstatus'), nullable=False),
    sa.Column('signup_date', sa.DateTime(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('trip_id', 'user_id')
    )
    op.create_table('trip_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('summary', sa.String(length=500), nullable=True),
    sa.Column('weather_conditions', sa.String(length=200), nullable=True),
    sa.Column('trail_conditions', sa.String(length=200), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('featured', sa.Boolean(), nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('trip_id', 'author_id', name='unique_trip_report_per_author')
    )
    op.create_table('photos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=True),
    sa.Column('caption', sa.String(length=500), nullable=True),
    sa.Column('s3_key', sa.String(length=500), nullable=False),
    sa.Column('s3_bucket', sa.String(length=100), nullable=False),
    sa.Column('thumbnail_s3_key', sa.String(length=500), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('width', sa.Integer(), nullable=True),
    sa.Column('height', sa.Integer(), nullable=True),
    sa.Column('content_type', sa.String(length=50), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=True),
    sa.Column('trip_report_id', sa.Integer(), nullable=False),
    sa.Column('uploaded_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['trip_report_id'], ['trip_reports.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('comment_type', sa.Enum('TRIP', 'TRIP_REPORT', 'PHOTO', name='commenttype'), nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=True),
    sa.Column('trip_report_id', sa.Integer(), nullable=True),
    sa.Column('photo_id', sa.Integer(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('is_approved', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
    sa.ForeignKeyConstraint(['trip_report_id'], ['trip_reports.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('comments')
    op.drop_table('photos')
    op.drop_table('trip_reports')
    op.drop_table('trip_participants')
    op.drop_table('trips')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    # ### end Alembic commands ###
