# Documentation des Tests - PDP Price

## Vue d'ensemble

Ce fichier décrit la batterie de tests unitaires pour le module `pdp_price`. Ces tests valident le bon fonctionnement du calcul des prix et la robustesse face aux données manquantes.

---

## Configuration requise

### Prérequis
1. **Mise à jour des modules en base** : Avant de lancer les tests, assurez-vous que les modules suivants sont à jour en base de données :
   ```bash
   docker compose exec odoo python3 /usr/bin/odoo -d rubicondev -u pdp_metal,pdp_price --stop-after-init --no-http
   ```

2. **Lancement des tests** :
   ```bash
   docker compose exec odoo python3 /usr/bin/odoo --test-enable --stop-after-init -d rubicondev -u pdp_price --http-port=18069 --test-tags=/pdp_price
   ```

---

## Description des Tests

### Classe `TestPriceComputationMock`

Cette classe contient les tests principaux utilisant des **données mock**. Chaque test crée ses propres données qui sont **automatiquement supprimées** après exécution (rollback de transaction Odoo).

| Test | Objectif | Données Mock Créées | Résultat Attendu |
|------|----------|---------------------|------------------|
| `test_stone_zero_cost_warning` | Vérifier qu'une pierre sans coût génère une **alerte** | Pierre (cost=0), Produit | - `warnings` non vide<br>- Message "no cost defined"<br>- `totals.cost = 0` |
| `test_stone_with_cost_no_warning` | Vérifier qu'une pierre avec coût valide **ne génère pas** d'alerte | Pierre (cost=50), Produit (5 pièces) | - Pas de warning pour cette pierre<br>- `cost = 250` |
| `test_empty_product_no_crash` | Vérifier qu'un produit vide ne provoque **pas de crash** | Produit sans métal ni pierre | - `totals.cost = 0`<br>- `totals.price = 0` |
| `test_null_product_returns_error` | Vérifier que passer `None` retourne une erreur structurée | Aucune | - `{'error': 'Product required'}` |
| `test_market_metal_price_lookup` | Vérifier le lien métal ↔ prix de marché | MarketMetal, MarketPrice, Metal(market mode) | - `cost_method = 'market'`<br>- `market_metal_id` correctement lié |

---

## Helpers de Création de Données Mock

La classe fournit des méthodes utilitaires pour créer rapidement des données de test :

### `_create_mock_market_metal(code, name)`
Crée un métal de marché (ex: Or, Argent).
```python
gold = self._create_mock_market_metal('XAU', 'Gold')
```

### `_create_mock_metal(code, name, cost_method, cost, market_metal)`
Crée une définition de métal (18K, 14K...) avec le mode de coût choisi.
```python
metal_18k = self._create_mock_metal('18K', '18K Gold', 'market', 0, gold)
```

### `_create_mock_market_price(market_metal, price, date)`
Crée une entrée de prix de marché pour un jour donné.
```python
self._create_mock_market_price(gold, 3110.35)  # $3110.35/oz
```

### `_create_mock_stone(code, cost)`
Crée une pierre complète avec tous ses attributs (type, forme, teinte, taille).
```python
stone = self._create_mock_stone('DIA-RD-1mm', cost=0.0)  # Pierre sans coût
```

### `_create_mock_product_with_stone(stone, pieces)`
Crée un produit avec une composition de pierres.
```python
product = self._create_mock_product_with_stone(stone, pieces=5)
```

---

## Cycle de Vie des Données

```
┌─────────────────┐
│   Test Start    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ setUp() appelé  │◄─── Données partagées créées (devises...)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  test_xxx()     │◄─── Données mock créées via helpers
│  exécution      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ROLLBACK      │◄─── Odoo annule toutes les créations
│  automatique    │     Aucune donnée ne persiste !
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Test End     │
└─────────────────┘
```

---

## Ajout de Nouveaux Tests

Pour ajouter un nouveau test, suivez ce pattern :

```python
def test_mon_nouveau_cas(self):
    """
    Description du test.
    
    Mock data created:
    - Élément 1
    - Élément 2
    
    Expected: Résultat attendu
    """
    # 1. Créer les données mock
    mock_stone = self._create_mock_stone('TEST_001', cost=100.0)
    mock_product = self._create_mock_product_with_stone(mock_stone, pieces=2)
    
    # 2. Appeler le service
    result = self.env['pdp.price.service'].compute_product_price(
        mock_product, currency=self.usd
    )
    
    # 3. Vérifier le résultat
    self.assertEqual(result['totals']['cost'], 200.0)
```

---

## Résolution de Problèmes

### Erreur `column metals.cost_method does not exist`
**Cause** : Le module `pdp_metal` n'a pas été mis à jour après l'ajout du champ.  
**Solution** : Lancer un upgrade du module.

### Tests non découverts
**Cause** : Le module n'est pas dans l'argument `-u`.  
**Solution** : Utiliser `-u pdp_price` ou `--test-tags=/pdp_price`.
