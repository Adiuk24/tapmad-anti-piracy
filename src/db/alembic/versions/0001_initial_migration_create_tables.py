"""Initial migration - create tables

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create references table
    op.create_table('references',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False, server_default='video'),
        sa.Column('ref_hash_video', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ref_hash_audio', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_references_platform', 'references', ['platform'], unique=False)
    op.create_index('idx_references_content_type', 'references', ['content_type'], unique=False)
    op.create_index('idx_references_created_at', 'references', ['created_at'], unique=False)

    # Create detections table
    op.create_table('detections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='found'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('found', 'captured', 'fingerprinted', 'matched', 'enforced', 'error')", name='ck_detections_status')
    )
    op.create_index('idx_detections_platform', 'detections', ['platform'], unique=False)
    op.create_index('idx_detections_status', 'detections', ['status'], unique=False)
    op.create_index('idx_detections_created_at', 'detections', ['created_at'], unique=False)
    op.create_index('idx_detections_url', 'detections', ['url'], unique=False)
    op.create_unique_constraint('uq_detections_platform_url', 'detections', ['platform', 'url'])

    # Create evidence table
    op.create_table('evidence',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detection_id', sa.Integer(), nullable=False),
        sa.Column('s3_key_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('video_fp', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('audio_fp', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('duration_sec', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_evidence_detection_id', 'evidence', ['detection_id'], unique=False)
    op.create_index('idx_evidence_created_at', 'evidence', ['created_at'], unique=False)

    # Create matches table
    op.create_table('matches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detection_id', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=False),
        sa.Column('video_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('audio_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('decision', sa.String(length=20), nullable=False, server_default='none'),
        sa.Column('threshold_video', sa.Float(), nullable=False, server_default='0.18'),
        sa.Column('threshold_audio', sa.Float(), nullable=False, server_default='0.72'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ),
        sa.ForeignKeyConstraint(['reference_id'], ['references.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("decision IN ('match', 'likely', 'none')", name='ck_matches_decision'),
        sa.CheckConstraint("video_score >= 0.0 AND video_score <= 1.0", name='ck_matches_video_score'),
        sa.CheckConstraint("audio_score >= 0.0 AND audio_score <= 1.0", name='ck_matches_audio_score')
    )
    op.create_index('idx_matches_detection_id', 'matches', ['detection_id'], unique=False)
    op.create_index('idx_matches_reference_id', 'matches', ['reference_id'], unique=False)
    op.create_index('idx_matches_decision', 'matches', ['decision'], unique=False)
    op.create_index('idx_matches_created_at', 'matches', ['created_at'], unique=False)
    op.create_unique_constraint('uq_matches_detection_reference', 'matches', ['detection_id', 'reference_id'])

    # Create enforcements table
    op.create_table('enforcements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('detection_id', sa.Integer(), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('dmca_message', sa.Text(), nullable=True),
        sa.Column('recipient', sa.String(length=500), nullable=True),
        sa.Column('sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dry_run', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['detection_id'], ['detections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_enforcements_detection_id', 'enforcements', ['detection_id'], unique=False)
    op.create_index('idx_enforcements_sent', 'enforcements', ['sent'], unique=False)
    op.create_index('idx_enforcements_dry_run', 'enforcements', ['dry_run'], unique=False)
    op.create_index('idx_enforcements_created_at', 'enforcements', ['created_at'], unique=False)

    # Create platform_accounts table
    op.create_table('platform_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('account_name', sa.String(length=200), nullable=False),
        sa.Column('credentials', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_platform_accounts_platform', 'platform_accounts', ['platform'], unique=False)
    op.create_index('idx_platform_accounts_active', 'platform_accounts', ['is_active'], unique=False)
    op.create_unique_constraint('uq_platform_accounts_platform_name', 'platform_accounts', ['platform', 'account_name'])

    # Create legacy tables for migration compatibility
    op.create_table('legacy_detections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('video_hash', sa.String(length=64), nullable=True),
        sa.Column('audio_fp', sa.String(length=64), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('watermark_id', sa.String(length=100), nullable=True),
        sa.Column('evidence_key', sa.String(length=200), nullable=True),
        sa.Column('decision', sa.String(length=20), nullable=True),
        sa.Column('takedown_status', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_legacy_detections_detected_at', 'legacy_detections', ['detected_at'], unique=False)
    op.create_index('idx_legacy_detections_platform', 'legacy_detections', ['platform'], unique=False)
    op.create_index('idx_legacy_detections_confidence', 'legacy_detections', ['confidence'], unique=False)

    op.create_table('legacy_reference_fingerprints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content_id', sa.String(length=200), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_legacy_ref_fp_content_id', 'legacy_reference_fingerprints', ['content_id'], unique=False)
    op.create_index('idx_legacy_ref_fp_kind', 'legacy_reference_fingerprints', ['kind'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('legacy_reference_fingerprints')
    op.drop_table('legacy_detections')
    op.drop_table('platform_accounts')
    op.drop_table('enforcements')
    op.drop_table('matches')
    op.drop_table('evidence')
    op.drop_table('detections')
    op.drop_table('references')
