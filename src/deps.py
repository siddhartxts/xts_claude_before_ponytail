from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db

# Inject a database session into a route with:  db: db_dependency
db_dependency = Annotated[Session, Depends(get_db)]
