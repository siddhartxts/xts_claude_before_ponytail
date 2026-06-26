"""Application ORM models.

The schema was reset: the previous ``WatchlistItem`` and ``FinanceNote`` tables
(and all of their table migrations) were removed so the database can be rebuilt
from scratch. There are intentionally **no application tables defined yet** —
add new ORM models below as the new schema is designed.

``Base`` is re-exported here on purpose and must stay:
  * Alembic's ``env.py`` uses ``models.Base.metadata`` as the autogenerate
    target, and
  * the test suite does ``import models`` to register tables on
    ``Base.metadata``.
Removing this import would break both Alembic autogenerate and the tests.
"""

from database import Base  # noqa: F401  (re-exported for Alembic + tests)
