"""Cross-database compatible column types for UUID and JSON.

Uses native PostgreSQL types when available, falls back to
SQLite-compatible types (CHAR(32) for UUID, JSON for JSONB).
"""
import uuid
from sqlalchemy import String, JSON, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as CHAR(32).
    """
    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == "postgresql":
                # PostgreSQL expects native UUID or string
                if isinstance(value, uuid.UUID):
                    return str(value)
                return str(uuid.UUID(value))
            # SQLite: store as hex
            if isinstance(value, uuid.UUID):
                return value.hex
            return uuid.UUID(value).hex
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return value
            # Handle asyncpg UUID type
            return uuid.UUID(str(value))
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(32))


class JSONB_COMPAT(TypeDecorator):
    """Cross-DB JSON type: PostgreSQL JSONB or generic JSON."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
