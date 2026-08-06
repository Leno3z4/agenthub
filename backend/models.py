"""Legacy SQLAlchemy model scaffold retained for older prototypes.

`main.py` does not import this module; the live runtime uses `db.py` with
sqlite. If this layer is revived later, keep it aligned with the runtime
schema instead of the older provider/provider_id draft.
"""

import uuid

from sqlalchemy import Column, String, DateTime, Integer, LargeBinary
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    google_id = Column(
        String,
        unique=True,
    )

    email = Column(
        String,
        unique=True,
    )

    name = Column(
        String,
    )

    picture = Column(
        String,
    )

    wallet_address = Column(
        String,
        unique=True,
    )

    agent_address = Column(
        String,
    )

    agent_key_encrypted = Column(
        LargeBinary,
    )

    api_key_hash = Column(
        String,
    )

    permissions_confirmed = Column(
        Integer,
        nullable=False,
        default=0,
    )

    last_seen = Column(
        String,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
