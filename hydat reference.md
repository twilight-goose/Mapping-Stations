
### Hydat data lookup tables
SED_DATA_TYPES – INSTANT SEDIMENT DATA TYPE
  SED_DATA_TYPE   SED_DATA_TYPE_EN                                        SED_DATA_TYPE_FR
0            BL           Bed Load                                          Charge de fond
1            BM       Bed Material                                        Matériaux du lit
2            DI  Depth Integration                                   Intégration verticale
3            PI  Point Integration                                  Intégration ponctuelle
4            SV     Split Vertical  Intégration fractionnée en tous points de la verticale


DATA_TYPES
  DATA_TYPE               DATA_TYPE_EN           DATA_TYPE_FR
0         H                Water Level          Niveaux d'eau
1         I  Instantantaneous Sediment  Sédiments Instantanés
2         Q                       Flow                  Débit
3         S           Sediment in mg/L        Sédiment (mg/L)
4         T          Daily Mean Tonnes                   None


CONCENTRATION_SYMBOLS – CONCENTRATION SYMBOL
  CONCENTRATION_SYMBOL                          CONCENTRATION_EN                                      CONCENTRATION_FR
0                    B                                    Bottom                                                  Fond
1                    C                   Coarse Material Present                          Matériaux grossiers présents
2                    F                      Sample Bottle Filled                      Bouteille de prélèvement remplie
3                    G                  Organic Material Present                         Matières organiques présentes
4                    K  Sample(s) Collected in a Single Vertical      Échantillons recueillis sur un seul axe vertical
5                    R    Samples Collected in Several Verticals  Échantillons recueillis sur plusieurs axes verticaux
6                    T                                       Top                                               Surface
7                    U                        Automatic Sampling                            Échantillonage automatique


SAMPLING_VERTICAL_LOCATION – INSTANT SEDIMENT SAMPLING VERTICAL LOCATION
  SAMPLING_VERTICAL_LOCATION_ID                    SAMPLING_VERTICAL_LOCATION_EN                        SAMPLING_VERTICAL_LOCATION_FR
0                           ---                                          Unknown                                      Valeur Inconnue
1                          1QLB      One-Quarter the Distance from the Left Bank      Un quart de distance à partir de la rive gauche
2                          1QRB     One-Quarter the Distance from the Right Bank      Un quart de distance à partir de la rive droite
3                          3QLB   Three-Quarters the Distance from the Left Bank  Trois quarts de distance À partir de la rive gauche
4                          3QRB  Three-Quarters the Distance from the Right Bank  Trois quarts de distance À partir de la rive droite
5                           MID                                       Mid Stream                                Milieu du cours c'eau
6                          MULT                   Composite Sediment Measurement                          Mesure des sédiments mixtes
7                          WELB                            Waters Edge Left Bank                          Ligne des eaux, rive gauche
8                          WERB                           Waters Edge Right Bank                          Ligne des eaux, rive droite


SED_VERTICAL_SYMBOLS – INSTANT SEDIMENT SAMPLING VERTICAL SYMBOL
  SAMPLING_VERTICAL_SYMBOL                                                                       SAMPLING_VERTICAL_EN
                             SAMPLING_VERTICAL_FR
0                        K                        Sampling Vertical not at the Regular Single Vertical from Left Bank                      Verticale d'échantillonnage hors de la verticale unique habituelle à partir de la rive gauche
1                        L  Sediment Measurement Vertical not at the Regular Measurement Cross-Section from Left Bank  Verticale de mesure des sédiments hors de la section transversale de mesure habituelle à partir de la rive gauche
2                        M                                                              Sediment Measurement Vertical
                Verticale de mesure des sédiments
3                        X                                       Sampling Vertical not at the Regular Single Vertical                                                 Verticale d'échantillonnage hors de la verticale unique habituelle
4                        Z                 Sediment Measurement Vertical not at the Regular Measurement Cross-Section                             Verticale de mesure des sédiments hors de la section transversale de mesure habituelle


DATA_SYMBOLS – DATA SYMBOLS
  SYMBOL_ID                     SYMBOL_EN                         SYMBOL_FR
0         A                   Partial Day                Journée incomplète
1         B                Ice Conditions                Conditions à glace
2         D                           Dry                               Sec
3         E                     Estimated                            Estimé
4         S  Sample(s) collected this day  échantillons prélevés ce jour-là

MEASUREMENT_CODES - MEASUREMENT METHOD
  MEASUREMENT_CODE               MEASUREMENT_EN                      MEASUREMENT_FR
0                A                    Automatic                         Automatique
1                B  Both (automatic and manual)  Combinée (Automatique et Manuelle)
2                M                       Manual                            Manuelle
3                P                  Power Plant                 Centrale Électrique
4                R                     Recorder                        Enregistreur
5                S               Flow Summation       Superposition des Écoulements

PEAK_CODES
  PEAK_CODE  PEAK_EN   PEAK_FR
0         H  Maximum  Maximale
1         L  Minimum  Minimale

REMARK_CODES
   REMARK_TYPE_CODE           REMARK_TYPE_EN                REMARK_TYPE_FR
0                 2       ANNUAL HYDROMETRIC                REJETS ANNUELS
1                 4     HISTORICAL DISCHARGE         HISTORIQUE DES REJETS
2                 5  HISTORICAL WATER LEVELS  HISTORIQUE DES NIVEAUX D’EAU
3                 6          ANNUAL SEDIMENT  NIVEAUX DE SÉDIMENTS ANNUELS
4                 7      HISTORICAL SEDIMENT      HISTORIQUE DES SÉDIMENTS
5                11      ANNUAL WATER LEVELS         NIVEAUX D’EAU ANNUELS

   PRECISION_CODE                PRECISION_EN                    PRECISION_FR
0               8  in metres (to millimetres)  En mètres (au millimètre près)
1               9  in metres (to centimetres)  En mètres (au centimètre près)
