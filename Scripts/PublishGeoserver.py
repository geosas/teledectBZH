# -*- coding: utf-8 -*-
"""
Script pour publier des images sur un geoserver.
"""

import os
import sys
import argparse
#import requests
import csv
#import xml.etree.ElementTree as ET
import commands
    
#def CoverageXML(store):
#    """
#    """
#    coverage_xml = '''\
#                    <coverage>\
#                        <title>'''+ store +'''</title>\
#                        <metadata>\
#                            <entry key="time">\
#                                <dimensionInfo>\
#                                    <enabled>true</enabled>\
#                                    <presentation>LIST</presentation>\
#                                    <units>ISO8601</units>\
#                                    <defaultValue/>\
#                                </dimensionInfo>\
#                            </entry>\
#                        </metadata>\
#                        <parameters>\
#                            <entry>\
#                                <string>SORTING</string>\
#                                <string>'''"time D"'''</string>\
#                            </entry>\
#                        </parameters>\
#                    </coverage>'''
#                    
#    # Enlever les doubles espaces
#    coverage_xml = coverage_xml.replace("  ", "")
#    return coverage_xml


#def CreateStore(datadir, login, password, store, workspace, url):
#    """
#    """
#    print"Creation des fichiers properties\n"
#    with open("%s/indexer.properties" % (datadir), "w") as txtfile:
#        txtfile.write("TimeAttribute=time \nElevationAttribute=elevation \
#        \nSchema=*the_geom:Polygon,location:String,time:java.util.Date,elevation:Integer \
#        \nPropertyCollectors=TimestampFileNameExtractorSPI[timeregex](time)")
#
#    with open("%s/timeregex.properties" % (datadir), "w") as txtfile:
#        txtfile.write("regex=[0-9]{8}\n")
#        
#    print"Creation du store\n"
#    command = "curl -u %s:%s -v -XPUT -H 'Content-type: text/plain' \
#     -d %s %s/%s/coveragestores/%s/external.imagemosaic?coverageName=%s&configure=all"\
#     % (login, password, datadir, url, workspace, store, store)
#    os.system(command)
#    
#    coverage_xml = CoverageXML(store)
#    
#    print"Modification des parametre de la mosaic\n"
#    command = "curl -u %s:%s -v -XPUT -H \
#    'Content-type: application/xml' -d %s \
#    %s/%s/coveragestores/%s/coverages/%s.xml" %\
#    (login, password, coverage_xml, url, workspace, store, store)
#    os.system(command)

     
#def GeoPublish(url, workspace, store, login, password, datadir):
#        '''
#        Cree un workspace, puis un entrepot de donnees temporelle 's'ils
#        n'existent pas) et publie une image dedans.
#
#        '''
#
#        # Check if workspace exists
#        Headers = {'content-type': 'text/xml'}
#        urlWorkspace = "%s/%s" % (url, workspace)
#        urlStore = "%s/coveragestores/%s" % (urlWorkspace, store)
#        
#        r = requests.get(urlWorkspace, headers=Headers, auth=(login, password))
#
#        if not r.ok:
#            command = "curl -u %s:%s -XPOST -H 'content-type: text/xml' \
#            -d '<workspace><name>%s</name></workspace>' %s" \
#            % (login, password, workspace, urlWorkspace)
#            os.system(command)
#            
#            print "Creation du workspace."
#        else:
#            print "Le workspace existe."
#
#        r = requests.get(urlStore, headers=Headers, auth=(login, password))
#
#        if r.ok:
#            print "Le store existe"
#            # test les dates existantes
#            command = "curl -v -u %s:%s -XGET \
#            '%s/coverages/%s/index/granules.xml'" % (login, password, urlStore, store)
#            indexStoreTuple = commands.getstatusoutput(command)
#            indexStore = str(indexStoreTuple)
#            
#            # liste les rasters dans le datadir et leur date
#            for path, dossiers, rasters in os.walk(datadir):
#                for raster in rasters :
#                    if ".tif" in raster :
#                        date = raster[3:-8]+"-"+raster[7:-6]+"-"+raster[9:-4]
#                        if indexStore.find(date) == -1:
#                            UpdateStore(login, password, path+"/"+raster, urlStore)
#
#        else:
#            print "Le store n'existe pas, impossible de publier"
#            sys.exit()
#            #CreateStore(datadir, login, password, store, workspace, url)
#        
#        print "Fin de la publication"
#        return
  
def UpdateStore(login, password, raster, urlStore):
    """
    Publie un nouveau raster sur un store.
    
    in :
        login : string
                login
        password : string
                   mot de passe
        raster : string
                 chemin du raster a publier et qui est sur le geoserver
        urlStore : string
                   url du store ou publier le raster
    """
    command = "curl -v -u %s:%s -XPOST -H 'Content-type: text/plain' -d 'file://%s' '%s/external.imagemosaic'" % \
    (login, password, raster, urlStore)
    os.system(command)  
    print "L'entrepot a ete mis a jour"

      
def GeoPublish(url, workspace, store, login, password, datadir):
    '''
    Recupere toutes les dates des images sur un store pour ensuite publier
    les images qui ne l'ont pas encore ete
    
    in :
        url : string 
              url du geoserver
        workspace : string
                    workspace sur lequel publier les images
        store : string
                store sur lequel publier les images
        login : string
                login pour publier
        password : string
                   mot de passe pour publier
        datadir : string
                  dossier dans lequel se situent les images a publier

    '''
    
    # genere l'url du workspace
    urlWorkspace = "%s/%s" % (url, workspace)
    # genere l'url du store
    urlStore = "%s/coveragestores/%s" % (urlWorkspace, store)
    # liste toutes les dates disponibles sur le geoserver
    command = "curl -v -u %s:%s -XGET \
    '%s/coverages/%s/index/granules.xml'" % (login, password, urlStore, store)
    indexStoreTuple = commands.getstatusoutput(command)
    indexStore = str(indexStoreTuple)
    
    # liste les rasters dans le datadir et leur date
    for path, dossiers, rasters in os.walk(datadir):
        for raster in rasters :
            if ".tif" in raster :
                date = raster[3:-8]+"-"+raster[7:-6]+"-"+raster[9:-4]
                # si le raster n'est pas deja publie (d'apres sa date)
                if indexStore.find(date) == -1:
                    # publie le raster
                    UpdateStore(login, password, path+"/"+raster, urlStore)

    print "Fin de la publication"
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
                            
        args = parser.parse_args()
    
    # Recupere le login et password dans un fichier    
    with open(args.login, "r") as coFile:
        reader = csv.reader(coFile)
        for row in reader:
            login = row[0].split(":")[0]
            password = row[0].split(":")[1]
            break
        
    GeoPublish(args.url, args.wspace, args.store, login, password, args.datadir)
