@startuml
actor Utilisateur
node Odoo
database PostgreSQL
folder rubicon_addons
node rubicon_core

Utilisateur --> Odoo : HTTP 8069
Odoo --> PostgreSQL : db:5432
Odoo --> rubicon_addons : volume extra-addons
Odoo --> rubicon_core : API / FDW
rubicon_core --> PostgreSQL : SQLAlchemy
@enduml
