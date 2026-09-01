BEATSBACKEND - DOCKERISATION ET AUDIT DE SECURITE



Rapport technique complet, du fork jusqu'au correctif de la faille critique.



Realise par : Sassou Florent FOEVI

Depot : https://github.com/FOEVI/beatsBackend (fork de aklaaX/beatsBackend)

Environnement : Windows (Cmd) + Docker Desktop + Git

Periode : 19 aout 2026 (mise en place et decouverte de la faille) au 1er septembre 2026 (correctif applique et verifie)



SECTION 0 - MISSION CONFIEE


Brief recu en 5 points : utiliser le compte GitHub personnel et forker le

depot, creer un Dockerfile, creer un docker-compose avec une base de donnees

MySQL et l'application, s'assurer que ca fonctionne, puis realiser un audit

de securite du code comme le ferait un ingenieur securite, en etant explicite

sur chaque etape.



SECTION 1 - FORK ET CLONE

Le depot original aklaaX/beatsBackend a ete forke sur le compte GitHub
personnel, creant github.com/FOEVI/beatsBackend. Le fork a ensuite ete
clone en local avec les commandes suivantes :

git clone https://github.com/FOEVI/beatsBackend.git
cd beatsBackend
git remote -v

La commande git remote -v confirme que origin pointe bien vers le fork
personnel, pas vers le depot original.

SECTION 2 - CREATION DU DOCKERFILE

Construit a partir d'une lecture reelle du code, pas d'un modele generique.
Lecture de requirements.txt (Django 4.1.7, compatible Python 3.11) et de
Source/settings.py (ENGINE: django.db.backends.mysql, donc l'application
utilise MySQL et non SQLite, malgre le fichier db.sqlite3 present dans le
depot original).

Contenu du Dockerfile :

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config default-mysql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

Le paquet mysqlclient est un connecteur Python/MySQL partiellement ecrit en
C. Les paquets systeme build-essential, default-libmysqlclient-dev et
pkg-config sont necessaires pour le compiler a l'installation.

SECTION 3 - CORRECTION DE REQUIREMENTS.TXT

Le fichier original avait deux problemes reels identifies en le lisant
directement :

- Encodage UTF-16 au lieu d'UTF-8, source classique de bugs silencieux
  selon l'environnement pip.
- Dependance suspecte : django-rest-framework==0.1.0 en plus du vrai paquet
  djangorestframework==3.14.0. Nom quasi identique (avec et sans tirets) au
  paquet officiel, schema classique de typosquatting sur PyPI. Retiree par
  precaution.

Version corrigee, en UTF-8, sans la dependance suspecte :

asgiref==3.6.0
Django==4.1.7
django-filter==22.1
djangorestframework==3.14.0
djangorestframework-simplejwt==5.2.2
pillow==11.2.1
PyJWT==2.6.0
pytz==2022.7.1
sqlparse==0.4.3
tzdata==2022.7
mysqlclient
pymysql
django-cors-headers
django-environ==0.9.0
django-extensions
werkzeug


SECTION 4 - DOCKER-COMPOSE.YML

Le Dockerfile construit une seule image, celle de l'application Django.
Le projet a besoin de deux containers qui communiquent entre eux : l'app
et une base MySQL nommee exactement mysql-vuln, car c'est le HOST attendu
par Source/settings.py.

Contenu de docker-compose.yml :

services:
  mysql-vuln:
    image: mysql:8.0
    container_name: mysql-vuln
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: beatdb
      MYSQL_USER: beatuser
      MYSQL_PASSWORD: beatpass
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-ubeatuser", "-pbeatpass"]
      interval: 5s
      timeout: 5s
      retries: 15

  app:
    build: .
    container_name: beats_backend
    restart: unless-stopped
    depends_on:
      mysql-vuln:
        condition: service_healthy
    environment:
      DJANGO_ALLOWED_HOSTS: "*"
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"

volumes:
  mysql_data:

Le port cote Windows a ete mis a 3307 (au lieu de 3306) car ce dernier
etait deja utilise par un autre service local. Erreur rencontree et
corrigee au premier essai de demarrage.

SECTION 5 - BUILD, DEMARRAGE ET VERIFICATION

Commande de demarrage :

docker compose up --build

Resultat : build reussi, MySQL initialise et sain (Healthy), migrations
Django appliquees (18 migrations), serveur demarre sur http://0.0.0.0:8000/.

Test de vie de l'API, en arriere-plan :

docker compose up -d
curl http://localhost:8000/api/beats/
Reponse obtenue : {"detail":"Authentication required."}

Reponse HTTP 403, comportement attendu : l'endpoint est vivant ET protege
par une authentification. Confirme egalement depuis un navigateur, via
l'interface navigable de Django REST Framework.

SECTION 6 - PUBLICATION SUR GITHUB

git add Dockerfile docker-compose.yml requirements.txt
git commit -m "Add Docker setup: Dockerfile, docker-compose with MySQL, fixed requirements.txt"
git push origin main

Deux imprevus rencontres sur cette machine au premier commit : Git ne
connaissait pas l'identite de l'auteur (message "Please tell me who you
are"), et l'authentification GitHub n'avait jamais ete configuree (fenetre
Git Credential Manager). Corriges avec :

git config --global user.email "foeviflorent@gmail.com"
git config --global user.name "foevi"

Commit et push reussis (commit b526a25), verifie ensuite directement sur
github.com/FOEVI/beatsBackend.

SECTION 7 - RESUME DE L'AUDIT DE SECURITE

Le endpoint /api/beats/ ne verifiait jamais la signature du JWT recu
(verify=False). N'importe qui pouvait forger un token avec un role Admin
arbitraire, sans connaitre aucune cle secrete, et obtenir un acces en
lecture/ecriture complet sur l'API. Cette faille a ete demontree
techniquement, pas seulement identifiee par lecture de code, puis corrigee
et re-testee.

Tableau des findings par severite, statut au 1er septembre 2026 :

Severite Critique : 2 findings au total, 1 corrige (C-01), 1 ouvert (C-02)
Severite Elevee : 4 findings au total, 2 corriges, 2 ouverts
Severite Moyenne : 5 findings au total, 2 corriges, 3 ouverts
Severite Faible : 2 findings au total, 0 corrige

SECTION 8 - C-01 CONTOURNEMENT TOTAL DE L'AUTHENTIFICATION JWT (CRITIQUE) - CORRIGE

Localisation d'origine : Beats/views.py (methode BeatViewSet.initialize_request),
Core/Auth/backend.py (classe UnsafeTokenBackend, supprimee depuis).

Code en cause avant correctif :

backend = TokenBackend(algorithm="HS256", signing_key=None)
payload = backend.decode(token, verify=False)

Le role etait ensuite lu directement dans ce payload non verifie :

def get_queryset(self):
    role = self.request.jwt_payload.get("role", "User")
    return Beat.objects.all() if role == "Admin" else Beat.objects.filter(isPublished=True)

Preuve de concept, journal de decouverte :

Etape A, premier script de forge (forge_token.py version 1) :

import base64, json

def make_token(payload):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesignature"

Test contre l'API, resultat inattendu :

curl -H "Authorization: Bearer <token>" http://localhost:8000/api/beats/
Reponse : {"detail":"Authentication required."}

Le token semblait rejete, un diagnostic etait necessaire plutot que de
conclure trop vite que le code etait sur.

Etape B, diagnostic avec debug_token.py :

from rest_framework_simplejwt.backends import TokenBackend
backend = TokenBackend(algorithm="HS256", signing_key=None)
payload = backend.decode(token, verify=False)

Erreur reelle obtenue :

binascii.Error: Invalid base64-encoded string: number of data characters (13) cannot be 1 more than a multiple of 4
rest_framework_simplejwt.exceptions.TokenBackendError: Token is invalid or expired

Cause : "fakesignature" (13 caracteres) n'est pas une longueur base64
valide. L'exception etait silencieusement avalee par le code applicatif
(except Exception: request.jwt_payload = {}), donnant l'illusion trompeuse
d'un simple rejet d'authentification, alors que le vrai probleme etait un
bug de format, pas une protection qui fonctionnait.

Etape C, script corrige (forge_token.py version 2), signature aleatoire
mais structurellement valide :

fake_sig = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()

Etape D, tests finaux, faille confirmee, etat du code avant correctif :

curl http://localhost:8000/api/beats/
Reference sans token : {"detail":"Authentication required."}

curl -H "Authorization: Bearer <token normal>" http://localhost:8000/api/beats/
Reponse : []  (200 OK, accepte malgre signature fausse)

curl -X POST http://localhost:8000/api/beats/ -H "Authorization: Bearer <token role Admin forge>" -H "Content-Type: application/json" -d "{\"title\":\"PoC-audit\",\"description\":\"test securite\",\"duration\":\"1:00\"}"
Reponse : {"audio":["No file was submitted."]}

Interpretation : le dernier resultat est la preuve decisive. L'erreur
porte sur un champ manquant (audio), pas sur l'authentification
(NotAuthenticated) ni sur la permission (PermissionDenied). La requete a
traverse les deux couches de protection avec un JWT jamais valide
cryptographiquement.

Impact : elevation de privileges complete sans identifiant ni mot de
passe, creation/modification/suppression arbitraire de donnees,
contournement total du controle d'acces par role.

SECTION 9 - CORRECTIF APPLIQUE LE 1ER SEPTEMBRE 2026

La classe UnsafeTokenBackend a ete supprimee. BeatViewSet utilise
desormais l'authentification standard de djangorestframework-simplejwt,
qui verifie la signature HMAC-SHA256 (avec SECRET_KEY) avant de resoudre
request.user :

authentication_classes = [JWTAuthentication]
permission_classes = [IsAuthenticated]

def _role(self):
    return getattr(self.request.user, "role", "Visitor")

Le role est desormais lu sur request.user.role, c'est a dire l'utilisateur
reel en base de donnees, resolu apres verification de la signature, et non
plus sur un payload arbitraire fourni par le client.

SECTION 10 - VERIFICATION POST-CORRECTIF

Trois tests effectues avec le nouveau code en place :

Test 1 - Token forge (role Admin, signature aleatoire), tentative de
creation :
Resultat : 401
Reponse : {"detail":"Given token not valid for any token type", "code":"token_not_valid", ...}

Test 2 - Token legitime (compte cree via /api/auth/register/, vrai JWT
signe par le serveur), tentative de lecture :
Resultat : 200
Reponse : []

Test 3 - Token legitime, role Visitor par defaut (aucun droit Admin
attribue), tentative de creation :
Resultat : 403
Reponse : {"detail":"You do not have permission to create this beat."}

Conclusion : le token forge est desormais rejete des la verification de
signature, avant meme d'atteindre la logique metier. Un compte legitime
peut toujours lire l'API normalement. Un compte legitime sans le role
Admin est refuse proprement par le controle de permission. La logique
d'autorisation fonctionne normalement, sans etre contournable via un JWT
non signe.

Commits concernes : 477236c (nettoyage prealable du depot, retrait de
db.sqlite3 et du fichier requirements.txt corrompu), 764e288 (correctif
C-01).

SECTION 11 - C-02 SECRETS COMMITES EN CLAIR (CRITIQUE) - OUVERT

Localisation : Source/settings.py, SECRET_KEY codee en dur, identifiants
MySQL en dur dans docker-compose.yml.

SECRET_KEY sert a signer les sessions, les tokens CSRF, et avec la config
par defaut de simplejwt (VERIFYING_KEY: None), les JWT eux-memes. Committee
en clair sur un depot public, elle est lisible par n'importe qui, ce qui
permettrait de forger des tokens correctement signes, ce qui est pire que
C-01 qui ne necessitait meme pas de connaitre la cle.

Remediation prevue : charger ces valeurs via variables d'environnement
(django-environ, deja en dependance mais non utilise pour ces valeurs),
regenerer SECRET_KEY et changer les mots de passe si le depot a ete rendu
public avec ces valeurs. Important : l'ancienne cle reste visible dans
l'historique Git meme apres un futur correctif dans le code, un simple
changement de valeur ne suffit pas a effacer l'exposition passee.

SECTION 12 - FINDINGS ELEVES

DEBUG=True et ALLOWED_HOSTS=["*"] par defaut
Localisation : Source/settings.py
Statut : Ouvert

CORS_ALLOW_ALL_ORIGINS=True par defaut
Localisation : Source/settings.py
Statut : Ouvert

db.sqlite3 versionne dans le depot
Localisation : racine du depot
Statut : Corrige, nettoyage du 1er septembre 2026

Dependance suspecte django-rest-framework==0.1.0 (typosquat probable)
Localisation : requirements.txt original
Statut : Corrige, retiree a l'etape de correction du requirements.txt

SECTION 13 - FINDINGS MOYENS

DEFAULT_AUTHENTICATION_CLASSES vide globalement
Localisation : Source/settings.py
Statut : Ouvert, seul Beats/views.py a ete corrige pour l'instant

Absence de rate limiting sur /api/auth/login
Localisation : Core/Auth/viewSets.py
Statut : Ouvert, confirme, aucune classe de throttling configuree

Absence de validation taille/type sur les fichiers uploades
Localisation : Beats/models.py, Core/models.py
Statut : Ouvert

Faute de frappe read_only_field au lieu de read_only_fields, ignoree
silencieusement par Django REST Framework, is_active n'est donc pas
protege en lecture seule sur un endpoint qui accepte PATCH
Localisation : Core/Serializers/serializers.py
Statut : Ouvert, confirme par lecture directe du code

Condition inversee dans BeatSerializer.get_artist (if not obj.artist: au
lieu de if obj.artist:), risque d'AttributeError si jamais artist est None
Localisation : Beats/serializer.py
Statut : Ouvert, confirme par lecture directe du code, risque limite car
artist est un champ obligatoire du modele

SECTION 14 - FINDINGS FAIBLES

MEDIA_ROOT pointe sur la racine du projet au lieu d'un sous-dossier dedie
Localisation : Source/settings.py
Statut : Ouvert

Fichier background.jpg (3,3 Mo) commite dans le depot applicatif
Localisation : racine du depot
Statut : Ouvert

Fichier corrompu (requirements.txt en UTF-16, mal renomme) coexistant
avec le bon requirements.txt
Localisation : racine du depot
Statut : Corrige, nettoyage du 1er septembre 2026

SECTION 15 - PLAN DE CORRECTION

Fait :
- C-01, faille d'authentification JWT, corrigee et re-verifiee
- Nettoyage du depot : db.sqlite3 retire, fichier requirements.txt
  corrompu retire
- Dependance typosquattee retiree, requirements.txt reecrit en UTF-8

Prochaine etape, priorite immediate :
- C-02, secrets en dur (SECRET_KEY, identifiants MySQL)

Court terme :
- DEBUG, ALLOWED_HOSTS, CORS
- Centralisation de DEFAULT_AUTHENTICATION_CLASSES

Moyen terme :
- Rate limiting sur le login
- Validation des fichiers uploades
- Correction des deux bugs de code (read_only_field, get_artist)

Continu :
- .gitignore et .dockerignore propres
- Scan de dependances (pip-audit) en continu

SECTION 16 - RECAPITULATIF, MISSION DEMANDEE VS TRAVAIL REALISE

Point 1, forker le depot : Fait. github.com/FOEVI/beatsBackend, depuis
aklaaX/beatsBackend.

Point 2, creer le Dockerfile : Fait. Base sur lecture reelle du code,
teste, publie.

Point 3, creer un docker-compose avec MySQL et l'application : Fait.
Service mysql-vuln conforme au HOST attendu par settings.py.

Point 4, s'assurer que ca fonctionne : Fait. Build reussi, migrations
appliquees, verifie via navigateur et curl.

Point 5, audit comme un ingenieur securite : Fait. Faille critique
identifiee, demontree techniquement, corrigee et re-verifiee. 12 autres
findings documentes avec severite et statut.

Etre explicite sur chaque etape : Fait. Chaque etape documentee avec les
outils utilises, les erreurs rencontrees, et les corrections apportees.

SECTION 17 - METHODOLOGIE ET LIMITES

Ce travail combine une revue de code statique manuelle (lecture de Core,
Core/Auth, Beats, Blog, Source/settings.py, Source/urls.py,
requirements.txt) et une preuve de concept dynamique (scripts Python
executes dans le container Docker, tests curl) contre l'application
demarree localement via Docker Compose.

Aucun scan automatise (Bandit, ZAP, Burp, pip-audit) n'a ete realise dans
le cadre de cette session. Un audit complet en environnement professionnel
devrait les inclure en complement.