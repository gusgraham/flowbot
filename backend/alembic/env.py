import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool, text
from sqlmodel import SQLModel
from dotenv import load_dotenv

from alembic import context

# Import your models here
from domain import auth, fsa, fsm, verification, wq, ssd, interim

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Overwrite sqlalchemy.url with the one from env
db_url = os.getenv("DATABASE_URL", "sqlite:///./flowbot.db")
config.set_main_option("sqlalchemy.url", db_url)

db_schema = os.getenv("DB_SCHEMA")
print(f"DEBUG: DB Schema: '{db_schema}'")
print(f"DEBUG: DB URL starts with: {db_url.split('://')[0] if '://' in db_url else 'unknown'}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=db_schema
    )

    with context.begin_transaction():
        if db_schema and url.startswith("postgresql"):
            context.execute(f"SET search_path TO {db_schema}")
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    connect_args = {}
    if db_url.startswith("postgresql") and db_schema:
        connect_args = {"options": f"-c search_path={db_schema}"}

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args
    )

    with connectable.connect() as connection:
        if db_url.startswith("postgresql") and db_schema:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {db_schema}"))
            connection.execute(text(f"SET search_path TO {db_schema}"))
            connection.commit() # Ensure schema creation is committed
            
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            version_table_schema=db_schema # Store alembic_version in the custom schema
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
