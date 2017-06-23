# -*- coding: utf-8 -*-
"""
Script pour publier des images sur un geoserver.
"""

import os
import sys
import argparse
import requests
import csv

def GeoPublish(url, workspace, store, login, password, raster, datadir):
        '''
        Cree un workspace, puis un entrepot de donnees temporelle 's'ils
        n'existent pas) et publie une image dedans.

        '''

        # Check if workspace exists
        Headers = {'content-type': 'text/xml'}
        urlWorkspace = "%s/%s" % (url, workspace)
        urlStore = "%s/coveragestores/%s" % (urlWorkspace, store)
        
        r = requests.get(urlWorkspace, headers=Headers, auth=(login, password))

        if not r.ok:
            command = "curl -u %s:%s -XPOST -H 'content-type: text/xml' \
            -d '<workspace><name>%s</name></workspace>' %s" \
            % (login, password, workspace, urlWorkspace)
            os.system(command)
            
            print "Creation du workspace."
        else:
            print "Le workspace existe."

        r = requests.get(urlStore, headers=Headers, auth=(login, password))

        # Si l'entrepot existe, ajouter le raster
        if r.ok:
            command = "curl -v -u %s:%s -XPOST -H 'Content-type: text/plain' \
            -d '%s' '%s/external.imagemosaic'" % \
            (login, password, raster, urlStore)
            os.system(command)
            
            print "L'entrepot a ete mis a jour"
            
            ###fix me
            # mettre a jour le fichier config du viewer pour ajouter la date
        else:
            print("Creation des fichiers properties\n")
            with open("%s/indexer.properties" % (datadir), "w") as txtfile:
                txtfile.write("TimeAttribute=ingestion \nElevationAttribute=elevation \
                \nSchema=*the_geom:Polygon,location:String,ingestion:java.util.Date,elevation:Integer \
                \nPropertyCollectors=TimestampFileNameExtractorSPI[timeregex](ingestion)")

            with open("%s/timeregex.properties" % (datadir), "w") as txtfile:
                txtfile.write("regex=[0-9]{8}\n")

            coverage_xml = '''\
                            <coverage>\
                                <title>'''+ titre +'''</title>\
                                <metadata>\
                                    <entry key="time">\
                                        <dimensionInfo>\
                                            <enabled>true</enabled>\
                                            <presentation>LIST</presentation>\
                                            <units>ISO8601</units>\
                                            <defaultValue/>\
                                        </dimensionInfo>\
                                    </entry>\
                                </metadata>\
                                <parameters>\
                                    <entry>\
                                        <string>InputTransparentColor</string>\
                                        <string>''' + in_trans_color + '''</string>\
                                    </entry>\
                                </parameters>\
                            </coverage>'''
            # Enlever les doubles espaces
            coverage_xml = coverage_xml.replace("  ", "")

            # Creation de la mosaique
            mosaic_cmd = "curl -u {0}:{1} -v -XPUT -H 'Content-type: text/plain' -d 'file://{2}' {3}/rest/workspaces/{4}/coveragestores/{5}/external.imagemosaic?coverageName={5}&configure=all".format(login, password, mosaic_dir, url, workspace, nom_mosaic)

            print ("Creation de la mosaique : %s" % (mosaic_cmd))
            gc.call(mosaic_cmd, shell=True)

            # Modification des parameters de la mosaic
            parameters_cmd = "curl -u {0}:{1} -v -XPUT -H 'Content-type: application/xml' -d '{2}' {3}/rest/workspaces/{4}/coveragestores/{5}/coverages/{5}.xml".format(login, password, coverage_xml, url, workspace, nom_mosaic)

            print("Modification des parameters  : %s" % (parameters_cmd))
            gc.call(parameters_cmd, shell=True)

        return

if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", prog, " --help"
        print "        or : ", prog, " -h"
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description="Script pour publier sur\
        un geoserver des images.")
        
                                    
        parser.add_argument("-url", dest="url", action="store",
                            help="Geoserver url like \
                            http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/")
                            
        parser.add_argument("-wspace", dest="wspace", action="store",
                            help="Geoserver workspace") 
                            
        parser.add_argument("-store", dest="store", action="store",
                            help="Geoserver store")          
                                    
        parser.add_argument("-datadir", dest="datadir", action="store",
                            help="Directory with datas")
                            
        parser.add_argument("-co", dest="login", action="store",
                            help="Connexion file with login and password \
                            like login:password", default="user")      
        
        parser.add_argument("-raster", dest="raster", action="store",
                            help="Raster to import")
                            
        args = parser.parse_args()
    
    # Recupere le login et password dans un fichier    
    with open(args.co, "r") as coFile:
        reader = csv.reader(coFile)
        for row in reader:
            login = row[0].split(":")[0]
            password = row[0].split(":")[1]
            break
        
    GeoPublish(args.url, args.workspace, args.store, login, password, args.raster, args.datadir)