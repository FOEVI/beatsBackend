BEATSBACKEND

Fork de aklaaX/beatsBackend (backend Django d'une plateforme de
distribution de beats), utilise ici pour un exercice de dockerisation
et d'audit de securite applicative.

Ce fork contient :

- Dockerisation : Dockerfile + docker-compose.yml (app Django + MySQL),
  construits a partir d'une lecture reelle du code.
- Audit de securite complet : voir AUDIT_SECURITE.md. Faille critique
  d'authentification JWT identifiee et corrigee (avec preuve de concept
  reproductible), plus 6 autres findings corriges et documentes avec
  severite et statut.
- forge_token.py et debug_token.py : scripts de preuve de concept
  utilises pour demontrer la faille C-01, conserves comme documentation.

DEMARRER LE LABO

docker compose up --build

L'API est ensuite accessible sur http://localhost:8000/api/

Depot d'origine par AklaaX (https://github.com/AklaaX). Dockerisation et
audit de securite par Sassou Florent FOEVI.