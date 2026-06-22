"""Initial schema: documents, accounts, extraction_logs, companies

Revision ID: 001
Revises:
Create Date: 2026-06-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trade_name', sa.String(255), nullable=True),
        sa.Column('hgb_reference_number', sa.String(50), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('fiscal_year_end', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('legal_name')
    )
    op.create_index('idx_companies_hgb_ref', 'companies', ['hgb_reference_number'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('extracted_date', sa.DateTime(), nullable=True),
        sa.Column('extraction_status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('validation_status', sa.String(20), nullable=False, server_default='NOT_VALIDATED'),
        sa.Column('balance_variance_amount', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('balance_variance_pct', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_company_id', 'documents', ['company_id'])
    op.create_index('idx_documents_upload_date', 'documents', ['upload_date'])
    op.create_index(
        'idx_documents_company_fiscal_year',
        'documents',
        ['company_id', 'fiscal_year', 'document_type'],
        unique=True
    )

    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('parent_code', sa.String(20), nullable=True),
        sa.Column('order_seq', sa.Integer(), nullable=False),
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('is_subtotal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_header', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('amount_current_year', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('amount_prior_year', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('variance_amount', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('variance_pct', sa.DECIMAL(5, 2), nullable=True),
        sa.Column('variance_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_accounts_document_id', 'accounts', ['document_id'])
    op.create_index('idx_accounts_code', 'accounts', ['code'])
    op.create_index('idx_accounts_parent_code', 'accounts', ['parent_code'])
    op.create_index('idx_accounts_account_type', 'accounts', ['account_type'])
    op.create_index('idx_accounts_document_code', 'accounts', ['document_id', 'code'], unique=True)

    # Create extraction_logs table
    op.create_table(
        'extraction_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('log_type', sa.String(20), nullable=False),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_extraction_logs_document_id', 'extraction_logs', ['document_id'])
    op.create_index('idx_extraction_logs_log_type', 'extraction_logs', ['log_type'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('extraction_logs')
    op.drop_table('accounts')
    op.drop_table('documents')
    op.drop_table('companies')
