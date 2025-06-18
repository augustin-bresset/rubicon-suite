# rubicon_core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .models.reference.metal import *
from .models.reference.misc import *
from .models.reference.parts import *
from .models.reference.prices import *
from .models.reference.stone import *
from .models.transaction.stock import *
from .models.transaction.stone import *

# URL de connexion PostgreSQL (à adapter selon tes credentials)
DATABASE_URL = "postgresql+psycopg2://odoo:odoo@localhost:5432/rubicon"

# 1) Crée l'engine
engine = create_engine(DATABASE_URL, echo=True)

# 2) Base pour les modèles
Base = declarative_base()

# 3) Fabrique un sessionmaker
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
