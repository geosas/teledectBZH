# -*- coding: utf-8 -*-
"""
Script pour publier des images sur un geoserver.
"""

import os
import sys
import argparse
import requests
import csv
import xml.etree.ElementTree as ET


def UpdateMviewer(xml, date):
    """
    
    """
    tree = ET.parse(xml)
    root = tree.getroot()
    layer = root.findall("./themes/theme/layer")
    for l in layer:
        dates = l.get("timevalues")
        newDates = dates +","+ date
        l.set("timevalues",newDates)
    tree.write(open(xml, "w"))
    print "Fichier xml mis a jour"


def CreateMviewer(xml, date):
    """
    
    """
    tree = ET.parse(xml)
    root = tree.getroot()
    layer = root.findall("./themes/theme/layer")
    for l in layer:
        dates = l.get("timevalues")
        newDates = dates +","+ date
        l.set("timevalues",newDates)
    tree.write(open(xml, "w"))
    print "Fichier xml mis a jour"
    
    
def CoverageXML(store):
    """
    """
    coverage_xml = '''\
                    <coverage>\
                        <title>'''+ store +'''</title>\
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
                                <string>SORTING</string>\
                                <string>'''"time D"'''</string>\
                            </entry>\
                        </parameters>\
                    </coverage>'''
                    
    # Enlever les doubles espaces
    coverage_xml = coverage_xml.replace("  ", "")
    return coverage_xml
    
    
def UpdateStore(login, password, raster, urlStore, xml):
    """
    
    """
    command = "curl -v -u %s:%s -XPOST -H 'Content-type: text/plain' \
    -d '%s' '%s/external.imagemosaic'" % \
    (login, password, raster, urlStore)
    os.system(command)
    date = os.path.basename(raster).split("_")[-1][:-4]
    UpdateMviewer(xml, date)
    
    print "L'entrepot et le viewer ont ete mis a jour"

def CreateStore(datadir, login, password, store, workspace, url):
    """
    """
    print"Creation des fichiers properties\n"
    with open("%s/indexer.properties" % (datadir), "w") as txtfile:
        txtfile.write("TimeAttribute=time \nElevationAttribute=elevation \
        \nSchema=*the_geom:Polygon,location:String,time:java.util.Date,elevation:Integer \
        \nPropertyCollectors=TimestampFileNameExtractorSPI[timeregex](time)")

    with open("%s/timeregex.properties" % (datadir), "w") as txtfile:
        txtfile.write("regex=[0-9]{8}\n")
        
    print"Creation du store\n"
    command = "curl -u %s:%s -v -XPUT -H 'Content-type: text/plain' \
     -d %s %s/%s/coveragestores/%s/external.imagemosaic?coverageName=%s&configure=all"\
     % (login, password, datadir, url, workspace, store, store)
    os.system(command)
    
    coverage_xml = CoverageXML(store)
    
    print"Modification des parametre de la mosaic\n"
    command = "curl -u %s:%s -v -XPUT -H \
    'Content-type: application/xml' -d %s \
    %s/%s/coveragestores/%s/coverages/%s.xml" %\
    (login, password, coverage_xml, url, workspace, store, store)
    os.system(command)
    
    #CreateMviewer(xml, date)
        
def GeoPublish(url, workspace, store, login, password, raster, datadir, xml):
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

        if r.ok:
            UpdateStore(login, password, raster, urlStore, xml)
            
        else:
            CreateStore(datadir, login, password, store, workspace, url)
        
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
        
        parser.add_argument("-raster", dest="raster", action="store",
                            help="Raster to import")
        
        parser.add_argument("-xml", dest="mviewer", action="store",
                            help="Mviewer xml file")
                            
        args = parser.parse_args()
    
    # Recupere le login et password dans un fichier    
    with open(args.co, "r") as coFile:
        reader = csv.reader(coFile)
        for row in reader:
            login = row[0].split(":")[0]
            password = row[0].split(":")[1]
            break
        
    GeoPublish(args.url, args.workspace, args.store, login, password, args.raster, args.datadir, args.mviewer)
