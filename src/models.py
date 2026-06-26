"""Application ORM models.

No application tables are defined yet — add new ORM models below.

``Base`` is re-exported here on purpose and must stay importable:
  * Alembic's ``env.py`` uses ``models.Base.metadata`` as the autogenerate target, and
  * the test suite does ``import models`` to register tables on ``Base.metadata``.
"""

from database import Base  # noqa: F401  (re-exported for Alembic + tests)
