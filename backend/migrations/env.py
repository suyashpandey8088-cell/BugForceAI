import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database.session import Base
from app.models import models  # noqa
config = context.config
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL", "sqlite:///./bugforge.db"))
target_metadata = Base.metadata
def run_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
def run_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()
run_online() if context.is_offline_mode() is False else run_offline()
