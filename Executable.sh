python '/home/donatien/ProjectGeoBretagne/Scripts/DownloadMODIS.py' -path '/home/donatien/ProjectGeoBretagne/Datas/' -netrc '/home/donatien/ProjectGeoBretagne/.netrc' -fdate 2017-06-01

python '/home/donatien/ProjectGeoBretagne/Scripts/TreatmentEF.py' -d '/home/donatien/ProjectGeoBretagne/Datas' -out '/home/donatien/ProjectGeoBretagne/Datas/Output'

python /home/teledectBZH/Scripts/PublishGeoserver.py -url http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/ -wspace geouest -store EF_teledectBZH -datadir /home/data/gi2016/teledectBZH -co /home/teledectBZH/.logPassGeoserver

