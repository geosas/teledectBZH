
## Logiciel à installer

- GDAL
  * [Install](https://gdal.gloobe.org/install.html#linux)

- curl
  * [Install](https://curl.haxx.se/)

- sshpass
  * [Install](https://gist.github.com/arunoda/7790979)
## Bibliothèques [Python 2] nécessaires
```
- os
- sys
- datetime
- requests
- argparse
- pandas
- BeautifulSoup
- numpy
- glob
- gdal
- scipy
- matplotlib
- subprocess
- commands
```

## Fichier d'exécution[__Executable.sh__](Executable.sh)
Ce fichier permet de lancer la chaîne de traitement visant à télécharger, calculer et publier les produits MODIS.
Il se distingue en 2 parties :
- les variables à adapter selon le poste de travail et le geoserver (les variables sont décrites en commentaires)
- les commandes à exécuter dans le terminal selon ces variables

## Scripts utilisées :

[__DownloadModis.py__](Scripts/DownloadModis.py) permet de répertorier les dates disponibles pour les produits MOD09Q1 et MOD11A2 pour, selon les dates en entrée (J-1 à J), télécharger les images qui ne l'ont pas encore été. Pour télécharger les images, il est impératif d'avoir un compte USGS et de renseigner ses identifiants dans un fichier .netrc.
Les paramètres de cet outil sont :
- -path : répertoire où télécharger les images (/home/admin)
- -netrc : fichier contenant les identifiants pour télécharger les images (/home/admin/.netrc)
- -fdate : date à partir de laquelle rechercher des images (2017-06-02)
- -ldate : date jusqu'à laquelle rechercher des images (2017-07-02)

[__TreatmentEF.py__](Scripts/TreatmentEF.py) permet de produire le NDVI, l'Evaporative Fraction, la température de jour et de nuit. Pour cela, des prétraitements (découpage, suppression des nuages, conversion) sont effectués pour calculer ensuite ces indices qui sont à publier.
Les paramètres de cet outil sont :
- -d : répertoire contenant les images téléchargées (/home/admin/usgs)
- -out : répartoire où enregistrer les images (/home/admin)
- -clipshp : fichier shape à utiliser pour découper les images (/home/admin/bretagne.shp)
- -maskshp : fichier shape à utiliser pour masquer la mer des images (/home/admin/masque.shp)

[__IndicesExport.py__](Scripts/IndicesExport.py) permet d'exporter les indices calculés sur le serveur de calcul vers le serveur où se trouve le Geoserver. L'exportation s'effectue avec une commande scp.
Les paramètres de cet outil sont :
- -inurl : url du serveur de calcul (calc.agrocampus-ouest.fr)
- -indst : répertoire contenant les images à exporter (/home/admin/output)
- -outurl : url du serveur contenant le geoserver (geo.agrocampus-ouest.fr)
- -outdst : répertoire où enregistrer les images (/home/admin/geoserver)
- -coCopie : fichier contenant les identifiants pour se connecter au geoserver (/home/admin/.identifiant)

[__PublishGeoserver.py__](Scripts/PublishGeoserver.py) permet de mettre à jour un entrepôt avec de nouvelles images. Ce script suppose que le workspace et l'entrepôt ont déjà été créé. La mise à jour s'effectue avec une commande curl. Ce script est à placer sur le Geoserver et non sur le serveur de calcul.
Les paramètres de cet outil sont :
- -url : url du geoserver jusqu'au workspaces (http://geo.agrocampus-ouest.fr/geoserver/rest/workspaces/)
- -wspace : nom du workspace à utiliser (bretagne)
- -store : nom du store à utiliser (NDVI)
- -datadir : répertoire contenant les images à publier dans le store indiqué (/home/admin/geoserver/NDVI)
- -co : fichier contenant les identifiants pour se connecter au geoserver (/home/admin/.identifiant)

## Outil supplémentaire :

[__PlotTimeSerie.py__](Scripts/PlotTimeSerie.py) permet, à partir d'une série d'images et d'un shapefile contenant une entité, de générer un graphique présentant l'évolution des valeurs de la série d'images vis à vis de cette entité.
Les paramètres de cet outil sont :
- -d : répertoire contenant la série d'images (format XXX_YYYYMMDD.xxx) (NDVI_20170602.tif)
- -title : titre du graphique (Evolution du NDVI)
- -ylabel : titre de la série temporelle (NDVI)
- -o : répertoire où enregistrer le graphique (/home/admin)
- -roi : shapefile contenant la zone où collecter les valeurs (/home/admin/zone.shp)
- -ndata : valeur du nodata (-999 si images de GéoBretagne) (-999)
- -a : si présent, génère une courbe représentant la moyenne des valeurs par date (-a)
- -b : si présent, génère une courbe représentant la moyenne mobile des valeurs selon T-1, T, T+1 (-b)

__TODO :__
- Calculer les données manquantes entre les dates (pas de temps de 8 jours). A vérifier la pertinence vis à vis des températures pouvant être très différentes en 16 jours.
***
##### Powered by [![AGROCAMPUS-OUEST](http://geoinfo.agrocampus-ouest.fr/illustrations/logo_agrocampusouest.jpg)](http://www.agrocampus-ouest.fr)
***
[![Creative Commons License](https://licensebuttons.net/l/by-sa/3.0/88x31.png)](https://creativecommons.org/licenses/by-sa/4.0/)



[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen.)


   [Python 2]: <https://www.python.org/downloads/release>
   [Geoserver]: <http://geoserver.org/>
