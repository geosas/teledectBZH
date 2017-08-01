#!/bin/sh

###########################################
#################Variables#################
###########################################

# Determine la date J-1 a partir de laquelle recherche les dates disponibles (si la publication s'est faite vers minuit)
yesterday=$(date --date="15 day ago" +%Y-%m-%d)
# Determine la date J pour rechercher les dates disponibles
today=$(date +%Y-%m-%d)
# login et mot de passe du geoserver pour publier les images avec sshpass pour s'identifier
# necessite cette syntaxe : login:password
login="$(cat /home/dallery/teledectBZH/.logPassCopie | awk -F ":" '{print $1}')"
mdp="$(cat /home/dallery/teledectBZH/.logPassCopie | awk -F ":" '{print $2}')"

# Localisation des scripts, celui de publication doit etre sur le geoserver car il y a une recherche de fichier locaux
scriptDownload="/home/dallery/teledectBZH/Scripts/DownloadMODIS.py"
scriptTreatment="/home/dallery/teledectBZH/Scripts/TreatmentEF.py"
scriptExport="/home/dallery/teledectBZH/Scripts/IndicesExport.py"
scriptPublish="/home/dallery/PublishGeoserver.py"

# fichier contenant les identifiants pour se connecter sur le site de l'usgs
netrc='/home/dallery/teledectBZH/.netrc'
# repertoire dans lequel on souhaite creer le dossier usgs qui va contenir les produits MODIS
datadir='/home/dallery/teledectBZH/Datas'
# Shapefile pour decouper les images a l'echelle de la Bretagne
clipShp='/home/dallery/teledectBZH/GeoserverFiles/clip.shp'
# Shapefile pour masquer les pixels se situant dans la mer
maskShp='/home/dallery/teledectBZH/GeoserverFiles/mask.shp'

# url du serveur de calcul
urlServerCalc='psncalc.agrocampus-ouest.fr'
# url du geoserver ou placer les images
urlGeoserver='geowww.agrocampus-ouest.fr'
# repertoire local du workspace
dirWorkspace='/home/geoserver/owsserver_data_dir/data/psn/'
# fichier contenant les identifiants pour se connecter sur le geoserver
# necessite cette syntaxe : login:password
logpassCopie='/home/dallery/teledectBZH/.logPassCopie'

# url pour acceder aux workspaces
urlWorkspaces='http://geowww.agrocampus-ouest.fr/geoserver/rest/workspaces/'
# nom du workspace
workspace='psn'
# nom des stores actuels
storeEF='ef_modis_bretagne'
storeNDVI='ndvi_modis_bretagne'
storeTj='tempjour_modis_bretagne'
storeTn='tempnuit_modis_bretagne'
# fichier contenant les identifiants pour se connecter sur le geoserver
# necessite cette syntaxe : login:password
logpassPublie='/home/dallery/.logPassPublie'

###########################################
#################Commandes#################
###########################################

python ${scriptDownload} -path ${datadir} -netrc ${netrc} -fdate ${yesterday} -ldate ${today}

python ${scriptTreatment} -d ${datadir}'/usgs/' -out ${datadir}'/Output/' -clipshp ${clipShp} -maskshp ${maskShp}

python ${scriptExport} -inurl ${urlServerCalc} -indst ${datadir}'/Output/' -outurl ${urlGeoserver} -outdst ${dirWorkspace} -coCopie ${logpassCopie}

sshpass -p "${mdp}" ssh ${login}@${urlGeoserver} nohup python ${scriptPublish} -url ${urlWorkspaces} -wspace ${workspace} -store ${storeEF} -datadir ${dirWorkspace}${storeEF} -co ${logpassPublie}

sshpass -p "${mdp}" ssh ${login}@${urlGeoserver} nohup  python ${scriptPublish} -url ${urlWorkspaces} -wspace ${workspace} -store ${storeNDVI} -datadir ${dirWorkspace}${storeNDVI} -co ${logpassPublie}

sshpass -p "${mdp}" ssh ${login}@${urlGeoserver} nohup  python ${scriptPublish} -url ${urlWorkspaces} -wspace ${workspace} -store ${storeTj} -datadir ${dirWorkspace}${storeTj} -co ${logpassPublie}

sshpass -p "${mdp}" ssh ${login}@${urlGeoserver} nohup  python ${scriptPublish} -url ${urlWorkspaces} -wspace ${workspace} -store ${storeTn} -datadir ${dirWorkspace}${storeTn} -co ${logpassPublie}

