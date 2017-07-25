#!/bin/sh
today=$(date +%Y-%m-%d)
login="$(cat .logPassCopie | awk -F ":" '{print $1}')"
mdp="$(cat .logPassCopie | awk -F ":" '{print $2}')"

python '/home/dallery/teledectBZH/Scripts/DownloadMODIS.py' -path '/home/dallery/teledectBZH/Datas/' -netrc '/home/dallery/teledectBZH/.netrc' -fdate 2017-07-12

python '/home/dallery/teledectBZH/Scripts/TreatmentEF.py' -d '/home/dallery/teledectBZH/Datas/usgs/' -out '/home/dallery/teledectBZH/Datas/Output' -clipshp '/home/dallery/teledectBZH/GeoserverFiles/clip.shp' -maskshp '/home/dallery/teledectBZH/GeoserverFiles/mask.shp'

python '/home/dallery/teledectBZH/Scripts/IndicesExport.py' -inurl 'psncalc.agrocampus-ouest.fr' -indst '/home/dallery/teledectBZH/Datas/Output' -outurl 'geowww.agrocampus-ouest.fr' -outdst '/home/geoserver/owsserver_data_dir/data/psn' -coCopie '/home/dallery/teledectBZH/.logPassCopie'

sshpass -p"${mdp}" ssh ${login}@geowww.agrocampus-ouest.fr nohup python '/home/dallery/PublishGeoserver.py' -url 'http://geowww.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace 'psn' -store 'ef_modis_bretagne' -datadir '/home/geoserver/owsserver_data_dir/data/psn/ef_modis_bretagne' -co '/home/dallery/.logPassPublie'

sshpass -p"${mdp}" ssh ${login}@geowww.agrocampus-ouest.fr nohup  python '/home/dallery/PublishGeoserver.py' -url 'http://geowww.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace 'psn' -store 'ndvi_modis_bretagne' -datadir '/home/geoserver/owsserver_data_dir/data/psn/ndvi_modis_bretagne' -co '/home/dallery/.logPassPublie'

sshpass -p"${mdp}" ssh ${login}@geowww.agrocampus-ouest.fr nohup  python '/home/dallery/PublishGeoserver.py' -url 'http://geowww.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace 'psn' -store 'tempjour_modis_bretagne' -datadir '/home/geoserver/owsserver_data_dir/data/psn/tempjour_modis_bretagne' -co '/home/dallery/.logPassPublie'

sshpass -p"${mdp}" ssh ${login}@geowww.agrocampus-ouest.fr nohup  python '/home/dallery/PublishGeoserver.py' -url 'http://geowww.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace 'psn' -store 'tempnuit_modis_bretagne' -datadir '/home/geoserver/owsserver_data_dir/data/psn/tempnuit_modis_bretagne' -co '/home/dallery/.logPassPublie'

