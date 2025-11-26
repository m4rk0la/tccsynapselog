"""Add max_clients_per_day to polygon table

Revision ID: add_max_clients_per_day
Revises: 106a1b69bc38
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_max_clients_per_day'
down_revision = '106a1b69bc38'
branch_labels = None
depends_on = None


def upgrade():
    """Adiciona coluna max_clients_per_day à tabela polygon_data"""
    # Usa batch_alter_table para SQLite
    with op.batch_alter_table('polygon_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_clients_per_day', sa.Integer(), nullable=True))
    
    # Opcional: definir valor padrão para registros existentes
    # op.execute("UPDATE polygon_data SET max_clients_per_day = NULL WHERE max_clients_per_day IS NULL")


def downgrade():
    """Remove coluna max_clients_per_day da tabela polygon_data"""
    with op.batch_alter_table('polygon_data', schema=None) as batch_op:
        batch_op.drop_column('max_clients_per_day')
