
## Programmes à installer

- GRASS-GIS 7.*
  * [Download & install](https://grass.osgeo.org/grass7/)
  * [Compile and Install](https://grasswiki.osgeo.org/wiki/Compile_and_Install)

- GDAL 
  * [Install](https://gdal.gloobe.org/install.html#linux)

## Modules [Python 2] nécessaires 
```
- grass.script
- os
- tempfile
- sys
- json
- yaml
- shutil
- calendar
- datetime
- requests
- argparse
```

## Fichier de configuration [__config.json__](config.json)
Le fichier comprend les différents clés à indiquer :
- « grass_config_envs » pour les variables d’environnement de l’instance Grass installée,
- « tempPath » chemin où le répertoire temporaire Grass va être créé,
- « geoserver_info » permettant la publication des mosaïques temporelles sur [Geoserver],
- « processing_path » répertoire dans lequel vont être créé :
	- le répertoire temporaire des bandes téléchargées « images_out »,
	-  le répertoire «  RGB_geoserver » où les 4 mosaïques vont être créé dans 4 répertoires
	   « RGB_Mosaic_path_row » distinguée par « path,row ».

-  « database_path » répertoire où les 4 bases (json) des 4 images vont être crées

## Scripts utilisées : 

[__grass_location_config.py__](grass_location_config.py) comprend la classe __GrassLocationConfig__ qui permet,  à sont instanciation, de déclarer les variables d'environnement Grass, créer un repertoir temporaire dont les fichiers nécessaires pour faire tourner les algorithmes Grass et lire le fichier de configuration [config.json](config.json)

[__search_download_landsat8.py__](search_download_landsat8.py) comprend la classe __SearchDownloadLandsat8__ dont différentes les méthodes nécessaires pour la recherche, la création de base d'information JSON, le téléchargement des images landsat8 en utilisant comme information de base le (PATH, ROW) et la date de chaque image.

[__image_processes.py__](image_processes.py) comprend la classe __ImageProcesses__ qui permet, à sont instanciation, de lancer la création du répertoire temporaire de Grass. Elle comporte les méthodes permettant :
 - l'import/export (Grass), 
 - la correction radiométrique et atmosphérique (DOS) des différentes bandes de l’image, 
 - le pansharpning des bandes 2, 3 et 4
 - la création de la composition colorée
 - création et publication sur [Geoserver] de la mosaïque temporelle.

[__main_job.py__](main_job.py) C'est le script principale à exécuter avec les arguments de date de début (jour, mois et année), commande d'aide : ```./main_job.py --help```
Le script comprend la classe __Main__ dont les méthode __make_RGB_work__ là où il faut appeler les méthodes de traitement souhaitées. Cette dernière sera appeler dans deux endroits (lignes : 233 & 258) dans la méthode à exécuter nommée __main_job__.
Le comportement de la méthode __main_job__ est le suivant :
- En commençant par une date choisie (la date par défaut et 01//11/2013),
- Pour chaque pathRow et ficher de base de donnée :
    - si tu __trouve pas__ le fichier de base de donnée locale :
        - commence la recherche par jour sur la base [AWS], si tu trouve une image :
          - Lance le traitement avec __make_RGB_work__ et ajouter l’image dans la base locale
          - faire ça tout les 16 jours jusqu'à aujourd'hui
    - si tu __trouve__ le fichier de base de donnée locale :
        - commence la recherche, par jour, sur la base [AWS], depuis la date de la dernière image +1 jour, si tu trouve une image :
          - Lance le traitement avec __make_RGB_work__ et ajouter l’image dans la base locale
          - faire ça tout les jours jusqu'à aujourd'hui

## Script pas utilisé :
[__landsat_vrt_rgb_pan.sh__](landsat_vrt_rgb_pan.sh) c'est un script Shell qui permet de créer une composition colorée pansharpnée à partir des 4 bandes 2, 3, 4 et 8 et utilisant les commandes GDAL suivantes:
- __gdalbuildvrt__
- __gdal_translate__
- __gdal_landsat_pansharp__
- __gdaladdo__

__NB :__ 
- Ce script permet de créer une composition colorée avec un meilleur rendu (couleurs, contraste, luminosité...) mais [Geoserver] n'arrive pas à l'afficher.
- Il se peut que __gdal_landsat_pansharp__ ne sera pas installé par défaut avec GDAL, voir [ici](https://github.com/gina-alaska/dans-gdal-scripts/blob/master/README.md)  pour l'instalation.


__TODO :__
- Affiner le traitement concernant la création de la composition colorée avec [__landsat_vrt_rgb_pan.sh__](landsat_vrt_rgb_pan.sh) afin de pouvoir l'afficher sur [Geoserver].
- Déveloper une méthode qui permet de créer un masque des nuages en utilisant le fichier .BQA de l’image.
- Brancher le modèle de l'indice de sécheresse ou autre.

***
##### Powred by [![AGROCAMPUS-OUEST](http://www.agrocampus-ouest.fr/infoglueDeliverLive/digitalAssets/89735_Logo-AGROCAMPUS-OUEST.png)](http://www.agrocampus-ouest.fr)
***
[![Creative Commons License](https://licensebuttons.net/l/by-sa/3.0/88x31.png)](https://creativecommons.org/licenses/by-sa/4.0/)



[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen.)

	
   [Python 2]: <https://www.python.org/downloads/release>
   [Geoserver]: <http://geoserver.org/>
   [AWS]: <https://pages.awscloud.com/public-data-sets-landsat.html>
