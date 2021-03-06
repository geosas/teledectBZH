#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Cree le 2017/06/07
Script pour le telechargement et l'enregistrement d'images MODIS
"""

import sys
import os
import argparse
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup


def DateAndYJ(date):
    '''
    Converti une date YYYY-MM-DD en YYYY-MM-DD HH:MM:SS.MS (si besoin) puis en
    YYYYJJJ
    '''
    year = date.year
    month = date.strftime('%m')
    day = date.strftime('%d')
    dayYear = date.timetuple().tm_yday
    return year, month, day, dayYear


def ListUrlDates(url):
    """
    Liste les urls des dates.
    """
    # requete l'url
    r = requests.get(url)
    # recupere toutes les informations de la page
    soup = BeautifulSoup(r.content, "html.parser")
    # liste toutes les dates disponibles
    listDates = [link.get("href") for link in soup.findAll("a")]
    return listDates
    

def ListLinksModis(url):
    """
    Liste les urls des images a telecharger.
    """
    # requete l'url
    r = requests.get(url)
    # recupere toutes les informations de la page
    soup = BeautifulSoup(r.content, "html.parser")
    # recupere les url des images a telecharger selon la tuile et l'extension
    listUrls = [link.get("href") for link in soup.findAll("a") if "h17v04"\
                in link.get("href") and ".hdf" in link.get("href")]
    return listUrls


def Download(ListUrls, Path, netrc):
    """
    Utilise curl pour telecharger les images (d'apres la doc usgs).
    Rq : obligation d'utiliser un fichier .netrc car la methode visant
    a rentrer directement le login:mdp ne fonctionne pas.
    """
    dwnld = False
    # enrgistre les images dans un dossier nomme usgs
    if not os.path.exists(Path+"/usgs/"):
        os.mkdir(Path+"/usgs/")
    
    # pour chaque url
    for url in ListUrls:
        # liste les urls des images correspondant a la tuile et 
        # l'extension a telecharger
        ListFiles = ListLinksModis(url)
        
        # pour chaque image
        for dl in ListFiles:
            # ouvre le fichier listant toutes les images deja telechargees
            fichier = open(Path+"/usgs/log_images.txt", "r+") 
            for ligne in fichier:
                if os.path.basename(dl) in ligne :
                    break
            else :
                # si elle n'existe pas deja, telecharge avec curl
                if not os.path.exists(Path+"/usgs/"+os.path.basename(dl)):
                    print "Telechargement de l'image %s" % (dl)
                    # les cookies sont necessaires car l'identification se passe
                    # sur un autre site
                    command = "curl --netrc-file %s -L -c %s.cookies -b %s.cookies %s --output %s"\
                                % (netrc, Path+"/usgs/", Path+"/usgs/", url+dl, Path+"/usgs/"+os.path.basename(dl))
                    os.system(command)
                    dwnld = True
                fichier.write(os.path.basename(dl)+"\n") 
            fichier.close()

    return dwnld


def Main(Path, netrc, dateStart, dateEnd=datetime.date.today()):
    """
    Fonction pour telecharger des produits MODIS
    """
    # defini la periode de recherche de donnees et genere une liste de dates
    listDates = []
    dateRange = pd.date_range(dateStart, dateEnd)
    for d in dateRange:
        year, month, day, dateYJ = DateAndYJ(pd.to_datetime(d))
        listDates.append("%s.%s.%s" % (year, month, day))

    # initialise les urls pour telecharger les donnees MODIS
    baseUrlMOD09Q1 = 'https://e4ftl01.cr.usgs.gov/MOLT/MOD09Q1.006/'
    baseUrlMOD11A2 = 'https://e4ftl01.cr.usgs.gov/MOLT/MOD11A2.006/'

    # liste toutes les dates disponibles pour les donnees MODIS
    #print "Liste les dates disponibles"
    listDatesMOD09Q1 = ListUrlDates(baseUrlMOD09Q1)
    listDatesMOD11A2 = ListUrlDates(baseUrlMOD11A2)
    
    # genere une liste contenant les dates que l'on souhaite et qui sont
    # disponibles
    #print "Listage des dates voulus"
    listDatesDl1 = [date1 for date1 in listDatesMOD09Q1 \
                            for date2 in listDates if date2 in date1]
    listDatesDl2 = [date1 for date1 in listDatesMOD11A2 \
                            for date2 in listDates if date2 in date1]
    
    if listDatesDl1 == [] and listDatesDl2 == [] :
        print "\nAucune image disponible à partir du %s jusqu'au %s. ARRET"\
                % (dateStart, dateEnd)
        sys.exit()
        
    # genere une liste des urls des images a telecharger
    #print "Generation des urls des images"
    listUrlsDl1 = [baseUrlMOD09Q1+date for date in listDatesDl1]
    listUrlsDl2 = [baseUrlMOD11A2+date for date in listDatesDl2]
    
    # telechargement des images   
    Download(listUrlsDl1, Path, netrc)
    dwnld = Download(listUrlsDl2, Path, netrc)

    if dwnld == False:
        print("Aucune nouvelle image de disponible")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", prog, " --help"
        print "        or : ", prog, " -h"
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description="Script permettant de\
            telecharger des images MODIS necessaires pour calculer des indices\
            a diffuser sur geobretagne.")

        parser.add_argument("-path", dest="path", action="store",
                            help="Directory where download datas")
                            
        parser.add_argument("-netrc", dest="netrc", action="store",
                            help="Netrc file where url, login and password are\
                            stored")

        parser.add_argument("-fdate", dest="fdate", action="store",
                            default=datetime.date.today(),
                            help="First date to download datas : YYYY-MM-DD")
                            
        parser.add_argument("-ldate", dest="ldate", action="store",
                            default=datetime.date.today(),
                            help="Last date to download datas : YYYY-MM-DD")

        args = parser.parse_args()

    # Converti une chaine de texte en date au besoin
    for i in [args.fdate, args.ldate]:
        if isinstance(i, str):
            if i == args.fdate:
                fdate = datetime.datetime.strptime(i, "%Y-%m-%d")
            else :
                ldate = datetime.datetime.strptime(i, "%Y-%m-%d")
        elif isinstance(i, datetime.date):
            if i == args.fdate:
                fdate = i
            else :
                ldate = i
                
    print("Etape 1 : Recherche et telechargement d'images MODIS")

    Main(args.path, args.netrc, fdate, ldate)
