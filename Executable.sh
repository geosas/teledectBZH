#!/bin/sh
today=$(date +%Y-%m-%d)
python '/home/donatien/ProjectGeoBretagne/Scripts/DownloadMODIS.py' -path '/home/donatien/ProjectGeoBretagne/Datas/' -netrc '/home/donatien/ProjectGeoBretagne/.netrc' -fdate $today

python '/home/donatien/ProjectGeoBretagne/Scripts/TreatmentEF.py' -d '/home/donatien/ProjectGeoBretagne/Datas/usgs/' -out '/home/donatien/ProjectGeoBretagne/Datas/Output' -clipshp '/home/donatien/ProjectGeoBretagne/GeoserverFiles/clip.shp' -maskshp '/home/donatien/ProjectGeoBretagne/GeoserverFiles/mask.shp'

#python '/home/dallery/teledectBZH/Scripts/IndicesExport.py' -inurl 'psncalc.agrocampus-ouest.fr' -indst '/home/dallery/teledectBZH/Datas/output' -outurl 'geowww.agrocampus-ouest.fr' -outdst '/home/geoserver/owsserver_data_dir/data/psn' -co '/home/dallery/teledectBZH/.logPassGeoserver'

#python '/home/dallery/teledectBZH/Scripts/PublishGeoserver.py' -url 'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace psn -store ef_modis_bretagne -datadir '/home/geoserver/owsserver_data_dir/data/psn/ef_modis_bretagne' -co '/home/dallery/teledectBZH/.logPassGeoserver'

#python '/home/dallery/teledectBZH/Scripts/PublishGeoserver.py' -url 'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace psn -store ndvi_modis_bretagne -datadir '/home/geoserver/owsserver_data_dir/data/psn/ndvi_modis_bretagne' -co '/home/dallery/teledectBZH/.logPassGeoserver'

#python '/home/dallery/teledectBZH/Scripts/PublishGeoserver.py' -url 'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace psn -store tempjour_modis_bretagne -datadir '/home/geoserver/owsserver_data_dir/data/psn/tempjour_modis_bretagne' -co '/home/dallery/teledectBZH/.logPassGeoserver'

#python '/home/dallery/teledectBZH/Scripts/PublishGeoserver.py' -url 'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/' -wspace psn -store tempnuit_modis_bretagne -datadir '/home/geoserver/owsserver_data_dir/data/psn/tempnuit_modis_bretagne' -co '/home/dallery/teledectBZH/.logPassGeoserver'

