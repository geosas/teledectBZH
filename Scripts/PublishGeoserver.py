# -*- coding: utf-8 -*-
"""
Script pour publier des images sur un geoserver.
"""

import os
import sys
import argparse
import requests
import csv

def GeoPublish(workspace, warehouse, login, password, url, raster):
        '''
        Cree un workspace, puis un entrepot de donnees temporelle 's'ils
        n'existent pas) et publie une image dedans.

        '''
        WorkspaceUrl = "%s/rest/workspaces/%s" % (url, workspace)

        # Check if workspace exists
        Headers = {'content-type': 'text/xml'}
        r = requests.get(WorkspaceUrl, headers=Headers, auth=(login, password))

        if not r.ok:
            command = "curl -u %s:%s -XPOST -H 'content-type: text/xml' \
            -d '<workspace><name>%s</name></workspace>' %s/rest/workspaces" \
            % (login, password, workspace, url)
            os.system(command)
            
            print ("Creation du workspace: %s" % (workspace))
        else:
            print ("Le workspace: %s existe." % (workspace))

        WarehouseUrl = "{0}/rest/workspaces/{1}/coveragestores/{2}/coverage.xml" \
        % (url, workspace, warehouse)
        
        r = requests.get(WarehouseUrl, headers=Headers, auth=(login, password))

        # Si l'entrepot existe, ajouter le raster
        if r.ok:
            command = 'curl -u %s:%s -XPOST -H "Content-type: text/plain" \
            -d %s %s/rest/workspaces/%s/coveragestores/%s' \
            % (login, password, raster, url, workspace, os.path.basename(raster))
            os.system(command)
            
            print ("Ajout de l'image: %s" % (os.path.basename(raster)))
        else:
            # Creation des fichiers '.properties' pour la gestion de "time"
            print("Creation des fichiers 'properties' ...\n")
            with open("%s/indexer.properties" % (warehouse), "w") as f:
            	f.write("TimeAttribute=RGB_date \nCanBeEmpty=true \
             \nSchema=*the_geom:Polygon,location:String,RGB_date:java.util.Date:Integer \
             \nPropertyCollectors=TimestampFileNameExtractorSPI[timeregex](RGB_date)")

            with open("%s/timeregex.properties" % (warehouse), "w") as f:
            	f.write("regex=[0-9]{8}\n")

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

def GeoPublishModis(login, password, raster, url):
    """
    """
    command = "curl -v -u %s:%s -XPOST -H 'Content-type: text/plain' \
    -d 'file:///home/data/gi2016/teledectBZH/EF_20170602.tif' \
    'http://geoxxx.agrocampus-ouest.fr/geoserver/rest/workspaces/teledectBZH/coveragestores/EF_teledectBZH/external.imagemosaic'" % \
    (login, password, raster, url)
    os.system(command)

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
        
        parser.add_argument("-wspace", dest="wspace", action="store",
                            help="Geoserver workspace", default="teledec") 
                            
        parser.add_argument("-co", dest="login", action="store",
                            help="Connexion file with login and password \
                            like login:password", default="user")      
                            
        parser.add_argument("-url", dest="url", action="store",
                            help="Geoserver url", default="http://localhost:8282/geoserver")
        
        parser.add_argument("-entrepot", dest="warehouse", action="store",
                            help="Geoserver warehouse", default="/home/donatien/ProjectGeoBretagne/Datas/Output")
        
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
        
    GeoPublishModis(login, password, args.raster, args.url)    
    #GeoPublish(args.wspace, args.warehouse, login, password, args.url, args.raster)