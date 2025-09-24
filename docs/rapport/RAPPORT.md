<!-- Page de présentation -->
<div align="center">

<!-- Titre du document (18 pts) -->
<center>
<h1 style="font-size:18pt;">
Rapport du laboratoire 2
</h1>
</center>

<!-- 4 retours à interligne simple (18 pts) -->
<br>
<br>
<br>
<br>

<!-- (16 pts) -->
<center>
<h2 style="font-size:16pt;">
PAR
</h2>
</center>

<!-- 2 retours à interligne simple (16 pts) -->
<br>
<br>

<!-- Prénom et NOM DE FAMILLE, CODE PERMANENT (16 pts) -->
<center>
<h2 style="font-size:16pt;">
David NGUYEN, NGUD24049607
</h2>
</center>

<!-- 6* retours à interligne simple (16 pts) -->
<!-- * Devrait être 5 retours -->
<br>
<br>
<br>
<br>
<br>
<br>

<!-- Note de présentation (14 pts) -->
<center>
<h3 style="font-size:14pt;">
RAPPORT PRÉSENTÉ À FABIO PETRILLO DANS LE CADRE DU COURS <em>ARCHITECTURE LOGICIELLE</em> (LOG430-02)
</h3>
</center>

<!-- 5 retours à interligne simple (14 pts) -->
<br>
<br>
<br>
<br>
<br>

<!-- Date de remise (14 pts) -->
<center>
<h3 style="font-size:14pt;">
MONTRÉAL, LE 26 SEPTEMBRE 2025
</h3>
</center>

<!-- 5 retours à interligne simple (14 pts) -->
<br>
<br>
<br>
<br>
<br>

<!-- Date de présentation (14 pts) -->
<center>
<h3 style="font-size:14pt;">
ÉCOLE DE TECHNOLOGIE SUPÉRIEURE<br>
UNIVERSITÉ DU QUÉBEC
</h3>
</center>

<!-- 5 retours à interligne simple (14 pts) -->
<br>
<br>
<br>
<br>
<br>

</div>  


---  
<h1> Tables des matières </h1>

- [Mise en place](#mise-en-place)

---

# Mise en place
Le projet a été fork, puis ensuite clôné. Le fichier `.env` a été créé à partir du `.env.example` et `docker-compôse.yml`. En ce qui concerne le port 5000, `store_manager` écoute à l'intérieur du conteneur sur le port 5000 (par défaut, les ports d'un conteneur ne sont pas accessibles depuis la machine, car ils sont isolés). Donc, selon ma compréhension, si je veux ouvrir mon navigateur et aller sur http://localhost:5000, il faut dire à Docker: "Le port 5000 de ma machine hôte doit être relié au port 5000 du conteneur". Ainsi, dans mon `docker-compose.yml`, j'y ai ajouté  
```
store_manager:
    build: .
    volumes:
      - .:/app
    environment:
      DB_HOST: mysql        
      DB_PORT: 3306
      DB_USER: labo02
      DB_PASSWORD: labo02
      DB_NAME: labo02_db
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_DB: 0
    ports:
      - "5000:5000" # Nouvellement ajouté!
    depends_on:
      - mysql
      - redis
```
Par la suite, j'ai `docker compose build` et `docker compose up -d` pour orchestrer les conteneurs ensemble.

Ainsi, on peut lancer l'application dans son conteneur, soit en allant sur http://localhost:5000/ pour voir la vue de l'application. ![App view](app_view.png)

Finalement, pour la préparration de l'environnement de déploiement et le pipeline, j'ai commencé par exécuter les tests en local:
```
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
pytest -q
```

Le fichier `ci.yml` a été modifié en fonction du CI. J'ai procédé par la suite au versionnage du code avec:

```
git add .
git commit -m "MESSAGE DE COMMIT"
git push
```

> À noter qu'il y a eu un changement au niveau du script `init_sql`. De ce fait, j'ai appliqué les changements, puis j'ai rebuild les images comme suit:
```
docker compose down
docker volume ls 
docker volume rm log430-a25-labo2_mysql_data
docker build .
docker compose up -d
```

Maintenant, au niveau du CD, ma stratégie est d'y aller avec la VM de Azure (étant donné qu'actuellement nous travaillons encore à distance et donc les locaux de l'école ne sont pas accessibles).
![VM AZURE](vm_azure.png)

Ensuite, les secrets et les variables ont été configurés dans le repo GitHub:
![Git secrets](git_secrets.png)
![Git var](git_var.png)

Par la suite, j'ai vérifié la connectivité depuis ma machine locale en m'y connectant:
![VM TEST](vm_test.png)

