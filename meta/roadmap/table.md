# Tableau des charges (minima)
## Bloc A — PDP (finitions vers 1.0)

| Sous-contenu                                                                          | Estim. min |
| ------------------------------------------------------------------------------------- | ---------: |
| Intégration module “Currency” externe (taux par date, fallback)                       |    **4 h** |
| Tests supplémentaires — batteries paramétriques (produits × marges × devises × dates) |    **8 h** |
| Tests — invariants (cohérence marges, idempotence devise, sensibilité date)           |    **4 h** |
| Sécurité minimale (groupes/ACL/record rules)                                          |    **6 h** |
| Documentation dev (MkDocs prêt à l’emploi + 4 pages de base + docstrings)             |    **8 h** |
| **Total Bloc A**                                                                      |   **30 h** |


## Bloc B — SIS (impressions via HTML→PDF)
| Sous-contenu                              | Estim. min |
| ----------------------------------------- | ---------: |
| Service générique HTML→PDF (réutilisable) |    **8 h** |
| Gabarit Devis (HTML/CSS + contexte)       |    **4 h** |
| Gabarit Commande                          |    **4 h** |
| Crud Models (customers, documents, etc)   |    **8 h** |
| Intégration “Prices PDP → SIS”            |    **4 h** |
| Tests & validation visuelle               |    **4 h** |
| **Total Bloc B**                          |   **32 h** |



## Bloc C — PCS (Core)
| Sous-contenu                                                     | Estim. min |
| ---------------------------------------------------------------- | ---------: |
| Modèles & flux d’import SO→PCS (Documents/Items, pipeline Dept.) |    **4 h** |
| Dashboard Production & Stone (KPIs WIP/Done/Overdue)             |   **12 h** |
| Barcodes & vues rapides (listes filtrables)                      |   **12 h** |
| Écran Priorities (actions rapides)                               |    **8 h** |
| Tests de bout en bout (transitions, règles)                      |   **10 h** |
| Ajustements adoption atelier                                     |    **4 h** |
| **Total Bloc C**                                                 |   **82 h** |

## Total général (A + B + C) : **144 h** (18 j ouvrés)

