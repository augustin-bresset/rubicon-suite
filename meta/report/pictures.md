 ---                                                                                                                                         
  Vue d'ensemble
                                                                                                                                              
  ┌──────────────┬────────────────────────────────────────────────────────┬────────┐                                                        
  │    Table     │                          Rôle                          │ Lignes │
  ├──────────────┼────────────────────────────────────────────────────────┼────────┤
  │ Sketches     │ Photos modèle + dessins techniques (source principale) │ 10 656 │
  ├──────────────┼────────────────────────────────────────────────────────┼────────┤
  │ TSketches    │ Photos modèle complémentaires (même schéma)            │ 2      │                                                          
  ├──────────────┼────────────────────────────────────────────────────────┼────────┤                                                          
  │ Snapshots    │ Photos spécifiques produit (variant stone/gold)        │ 250    │                                                          
  ├──────────────┼────────────────────────────────────────────────────────┼────────┤                                                          
  │ dtproperties │ Métadonnées internes SQL Server (inutile)              │ —      │
  └──────────────┴────────────────────────────────────────────────────────┴────────┘                                                          
                                                        
  ---                                                                                                                                         
  Sketches — Photos modèle                              
                          
  Couverture générale
  - 10 628 photos présentes (DATALENGTH > 0) sur 10 656 lignes                                                                                
  - 28 entrées sans photo (null ou vide) — essentiellement la catégorie QU
  - 275 dessins techniques (Sketch) présents                                                                                                  
  - 4 dessins tronqués à exactement 999 996 octets : BQ204, N405D, R1876B, R2078 — artefact de limite SQL Server (1 Mo)                       
                                                                                                                                              
  Tailles des photos                                                                                                                          
  - Min : ~0 KB (corrompu)                                                                                                                    
  - Max : ~1,8 MB                                                                                                                             
  - Moyenne : ~138 KB                                                                                                                         
                                                                                                                                              
  Plage temporelle (LastUpdated)                        
  - Plus ancienne : 1980                                                                                                                      
  - Plus récente : 2024-09-04
  - La base est activement maintenue jusqu'en 2024                                                                                            
                                                                                                                                              
  Répartition par catégorie
                                                                                                                                              
  ┌──────────┬────────┬────────┬─────────┬─────────────────────────────┐
  │  CatID   │ Lignes │ Photos │ Dessins │            Notes            │                                                                      
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤
  │ R        │ 2 879  │ 2 879  │ 20      │ Bagues, catégorie dominante │
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤
  │ E        │ 2 364  │ 2 364  │ 3       │                             │                                                                      
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤                                                                      
  │ QU       │ 1 711  │ ~1 683 │ 234     │ Forte densité de dessins    │                                                                      
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤                                                                      
  │ P        │ 1 494  │ 1 494  │ 4       │                             │
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤                                                                      
  │ N        │ 735    │ 735    │ 7       │                             │
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤                                                                      
  │ BA       │ 409    │ 409    │ 0       │                             │
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤
  │ SP       │ 307    │ 307    │ 5       │                             │
  ├──────────┼────────┼────────┼─────────┼─────────────────────────────┤                                                                      
  │ (autres) │ ~757   │ ~757   │ ~2      │ CF, BQ, T_, etc.            │
  └──────────┴────────┴────────┴─────────┴─────────────────────────────┘                                                                      
                                                        
  Champ Model : vérifié sur 10 656 lignes — Model = RTRIM(CatID) + RTRIM(OrnID) à 100 %. Aucune divergence. Le champ est redondant mais       
  fiable.                                               
                                                                                                                                              
  Correspondance avec Odoo :                            
  - 10 181 / 10 628 photos (95%) ont un code modèle qui existe dans pdp.product.model
  - 447 non-matchés = modèles anciens/discontinués absents d'Odoo                                                                             
  - 14 récupérables par zero-padding (CF1 → CF001)
                                                                                                                                              
  ---                                                   
  Sketches — Dessins techniques                                                                                                               
                                                                                                                                              
  ┌──────────────────────────────┬────────┐
  │            Statut            │ Nombre │                                                                                                   
  ├──────────────────────────────┼────────┤             
  │ Dessins présents et valides  │ 271    │
  ├──────────────────────────────┼────────┤
  │ Dessins tronqués (999 996 B) │ 4      │
  ├──────────────────────────────┼────────┤                                                                                                   
  │ Total                        │ 275    │
  └──────────────────────────────┴────────┘                                                                                                   
                                                        
  Les dessins sont concentrés sur QU (234/275 = 85 %). Les catégories R, E, P, N, SP n'ont que quelques dessins chacune.                      
   
  ---                                                                                                                                         
  Snapshots — Photos produit-spécifiques                

  Couverture générale
  - 250 lignes, toutes avec photo (Picture IS NOT NULL)
  - Données datant uniquement de 2002–2003 — snapshot figé, plus mis à jour                                                                   
                                                                           
  Clés de composition                                                                                                                         
  - GoldID : W = 249, Y = 1 (quasi-exclusivement or blanc)                                                                                    
  - 68 StoneID distincts                                                                                                                      
  - 210 modèles uniques représentés                                                                                                           
                                                                                                                                              
  Top pierres (StoneID)                                 
                                                                                                                                              
  ┌────────────────┬─────────────┐
  │    StoneID     │ Occurrences │                                                                                                            
  ├────────────────┼─────────────┤                      
  │ D (diamant)    │ 28          │
  ├────────────────┼─────────────┤
  │ PEARL          │ 23          │                                                                                                            
  ├────────────────┼─────────────┤
  │ AQUA           │ 19          │                                                                                                            
  ├────────────────┼─────────────┤                      
  │ BTA            │ 11          │
  ├────────────────┼─────────────┤
  │ AM (améthyste) │ 10          │
  ├────────────────┼─────────────┤                                                                                                            
  │ EMCS+CITA      │ 9           │
  ├────────────────┼─────────────┤                                                                                                            
  │ (autres)       │ ~150        │                      
  └────────────────┴─────────────┘                                                                                                            
   
  ▎ Les codes pierres sont en nomenclature 2002 (PEARL, AGATE, EMCS+CITA...) — incompatibles avec les codes produits Odoo actuels.            
                                                        
  Répartition par catégorie                                                                                                                   
                                                        
  ┌────────────┬────────┐
  │   CatID    │ Photos │
  ├────────────┼────────┤
  │ R (bagues) │ 151    │
  ├────────────┼────────┤
  │ P          │ 55     │                                                                                                                     
  ├────────────┼────────┤
  │ E          │ 39     │                                                                                                                     
  ├────────────┼────────┤                               
  │ B          │ 3      │
  ├────────────┼────────┤
  │ PF         │ 2      │
  └────────────┴────────┘

  Modèles avec plusieurs variantes                                                                                                            
  - 38 modèles ont ≥ 2 variantes dans Snapshots
  - E414 et R645 ont 3 variantes chacun                                                                                                       
                                                        
  Taux de correspondance avec Odoo                                                                                                            
  - Par code produit exact : 18 % (82 % de miss — codes pierres obsolètes)
  - Fallback possible (modèle existant dans Odoo) : 167/205 misses → 81 %                                                                     
  - 38 produits dont le modèle n'existe plus dans Odoo : perdus définitivement
                                                                                                                                              
  ---                                                                                                                                         
  TSketches — Photos complémentaires haute résolution                                                                                         
                                                                                                                                              
  Seulement 2 lignes :                                  

  ┌─────────────┬───────────────────────┬──────────────────────┬──────────────────┐                                                           
  │ Code modèle │ Taille dans TSketches │ Taille dans Sketches │      Delta       │
  ├─────────────┼───────────────────────┼──────────────────────┼──────────────────┤                                                           
  │ E1514C      │ 1,18 MB               │ 254 KB               │ × 4,6 plus grand │
  ├─────────────┼───────────────────────┼──────────────────────┼──────────────────┤                                                           
  │ P761        │ 2,41 MB               │ 160 KB               │ × 15 plus grand  │                                                           
  └─────────────┴───────────────────────┴──────────────────────┴──────────────────┘
                                                                                                                                              
  Ces deux entrées sont des doublons améliorés — même modèle que dans Sketches, mais résolution nettement supérieure. L'import doit préférer  
  TSketches pour ces deux modèles.
                                                                                                                                              
  ---                                                   
  Synthèse pour l'import Odoo
                                                                                                                                              
  ┌─────────────────────────────────────┬───────────────────────┬───────────────────────────────────┐
  │              Catégorie              │ Fichiers exportables  │       Matchs Odoo attendus        │                                         
  ├─────────────────────────────────────┼───────────────────────┼───────────────────────────────────┤                                         
  │ Photos modèle (Sketches)            │ 10 628                │ ~10 181 (95%)                     │
  ├─────────────────────────────────────┼───────────────────────┼───────────────────────────────────┤                                         
  │ Dessins (Sketches)                  │ 275 (dont 4 tronqués) │ ~262                              │
  ├─────────────────────────────────────┼───────────────────────┼───────────────────────────────────┤                                         
  │ Photos produit (Snapshots)          │ 250                   │ ~45 directs + 167 fallback modèle │
  ├─────────────────────────────────────┼───────────────────────┼───────────────────────────────────┤                                         
  │ Photos haute résolution (TSketches) │ 2                     │ 2 (remplacement E1514C et P761)   │
  └─────────────────────────────────────┴───────────────────────┴───────────────────────────────────┘                                         
                                                        
  Import actuel : seulement 5 641 photos modèle importées sur ~10 181 possibles (55%). Le re-run de make import-pictures après nettoyage des  
  orphelins devrait monter à ~95%.                      
                                                                                                                                              
  ---                                                   
  Ce rapport est basé sur les données extraites directement de la BAK SQL Server restaurée. Les 447 modèles sans correspondance Odoo sont des
  modèles hors catalogue — aucune action corrective n'est possible sans les réintégrer dans Odoo.                                             
   
