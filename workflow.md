````markdown
# Workflow de mise à jour des modèles et migrations

Ce document recense les commandes et bonnes pratiques à suivre pour propager vos modifications de schéma et de modèles, que ce soit côté **rubicon-core** (SQLAlchemy/Alembic) ou **Odoo** (modules personnalisés comme `pdp_reference`).

---

## 1. rubicon-core (SQLAlchemy + Alembic)

1. **Mettre à jour vos modèles** dans `rubicon_core/models/` (SQLAlchemy).
2. **Générer une nouvelle révision Alembic** :
   ```bash
   alembic revision --autogenerate -m "<message clair>"
````

3. **Relire et ajuster le script** dans `alembic/versions/<revision>_*.py` :

   * Vérifier `existing_type` et `type_` des colonnes modifiées.
   * Ajouter `postgresql_using='col::integer'` si nécessaire.
   * Contrôler les contraintes, index et séquences.
4. **Exécuter la migration** :

   ```bash
   alembic upgrade head
   ```
5. **Tester le rollback (optionnel)** :

   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

> **Tip** : pour revenir à l’état initial complet (schéma vide), utilisez `alembic downgrade base` puis `alembic upgrade head`.

---

## 2. Module Odoo (ex. `pdp_reference`)

1. **Modifier vos modèles Python** dans `addons/pdp_reference/models/`.
2. **Incrémenter la version du module** dans le fichier `__manifest__.py` (champ `version`).
3. **Recharger le module dans Odoo** :

   ```bash
   # Exécuter la mise à jour du module via le shell Odoo
   docker compose exec odoo \
     odoo -d rubicon -u pdp_reference --without-demo=all
   ```
4. **Redémarrer le service Odoo** (si besoin) :

   ```bash
   docker compose restart odoo
   ```

> **Astuce** : vous pouvez combiner l’update et le restart :
>
> ```bash
> docker compose exec odoo \
>   odoo -d rubicon -u pdp_reference --without-demo=all && \
> docker compose restart odoo
> ```

---

## 3. Autres étapes utiles

* **Vider le cache d’Odoo** (filestore) si des assets ou images ne se mettent pas à jour :

  ```bash
  docker compose exec odoo \
    rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*
  ```

* **Recompiler les assets front-end** (si vous avez des dépendances Node.js) :

  ```bash
  docker compose exec odoo bash -lc "npm install && npm run build"
  ```

* **Mettre à jour la base via CLI** (initialisation ou nouveaux modules) :

  ```bash
  docker compose exec odoo \
    odoo --db_host=db --db_user=odoo --db_password=odoo \
         -d rubicon -i <module1>,<module2> --without-demo=all
  ```

---

## 4. Versions et fonctionnement d’Alembic

* **Révisions** : chaque migration est identifiée par un hash (`<revision>`) et stockée dans `alembic/versions/`.
* **`head`** : pointe vers la dernière révision disponible.
* **`base`** : état initial (aucune migration appliquée).
* **`stamp <revision>`** : synchronise la table `alembic_version` sans exécuter de SQL.
* **`upgrade <target>`** : applique les migrations jusqu’à la révision cible (`head`, un hash, ou `+n`).
* **`downgrade <target>`** : annule les migrations jusqu’à la révision cible (`base`, un hash, ou `-n`).

> **Schéma rapide** :
>
> ```
> base → rev1 → rev2 → rev3 → head
>                  ↑
>           downgrade 1 step
> ```
>
> * `alembic upgrade head` : base → head
> * `alembic downgrade -1` : head → rev2

---

*Ce guide est à jour pour votre projet `rubicon-suite`.*

```
```
