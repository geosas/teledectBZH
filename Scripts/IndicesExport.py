# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 16:34:49 2017

@author: donatien
"""
import os
import sys
import subprocess
import argparse
import csv

def exportRasters(inUrl, inServer, outUrl, outServer, login, password):
    """
	Exporte les indices calcules sur un serveur vers un autre
    """
    # repertoires a exporter
    indices = {"Day":"tempjour_modis_bretagne", "Night":"tempnuit_modis_bretagne",\
            "NDVI":"ndvi_modis_bretagne", "EF":"ef_modis_bretagne"}
    
    #liste tous les dossiers/fichiers
    for path, dossiers, rasters in os.walk(inServer):
        #pour chaque fichier
        for raster in rasters :
            #s'il fait parti des fichiers a exporter
            if (indice in raster for indice in indices.keys()) :	
                indice = raster[:-13]
                # existe t'il dans le dossier de destination ?
                resp = subprocess.call(['sshpass', '-p', "%s" % (password), 'ssh',\
                '%s@%s' % (login, outUrl), 'test', '-e',\
                '%s/%s/%s' %(outServer, indices[indice], raster)])
                #si non, exporte le fichier
                if resp == 1:
                    print ("Export")
                    command = 'sshpass -p "%s" scp %s@%s:%s/%s/%s %s@%s:%s/%s/%s'\
                    % (password, login, inUrl, inServer, indice, raster, login, outUrl, outServer, indices[indice], raster)
                    os.system(command)
                #si oui, ne fait rien
                elif resp == 0 :
                    print "Fichier %s deja exporte" % (raster)
                #sinon, code erreur et arret
                else :
                    print "Code erreur ssh, arret"
                    print resp
                    sys.exit()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", prog, " --help"
        print "        or : ", prog, " -h"
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description="Script pour calculer\
        l'evaporative fraction (EF) a partir de donnees MODIS.")
        
        parser.add_argument("-inurl", dest="inUrl", action="store",
                            help="Calc server url")
                            
        parser.add_argument("-indst", dest="inServer", action="store",
                            help="Datas directory in server")

        parser.add_argument("-outurl", dest="outUrl", action="store",
                            help="Geoserver server url")
                            
        parser.add_argument("-outdst", dest="outServer", action="store",
                            help="Datas directory out server")

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
            
        exportRasters(args.inUrl, args.inServer, args.outUrl, args.outServer, login, password)
        
        print "\nExport Terminee"
