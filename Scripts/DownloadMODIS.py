#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Cree le 2017/06/07
Script pour le telechargement et l'enregistrement d'images (actuellement MODIS)
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
    Liste les urls des images a telecharger.
    """
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    listDates = [link.get("href") for link in soup.findAll("a")]
    return listDates
    

def ListLinksModis(url):
    """
    Liste les urls des images a telecharger.
    """
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    listUrls = [link.get("href") for link in soup.findAll("a") if "h17v04"\
                in link.get("href") and ".hdf" in link.get("href")]
    return listUrls


def Download(ListUrls, Path, netrc):
    """
    Use Curl method from usgs informations to download datas
    (https://lpdaac.usgs.gov/sites/default/files/public/get_data/docs/
    Command%20Line%20Access%20Tips%20for%20Utilizing%20Earthdata%20Login.docx)
    """
    if not os.path.exists(Path+"/usgs/"):
        os.mkdir(Path+"/usgs/")
        
    for url in ListUrls:
        ListFiles = ListLinksModis(url)
        for dl in ListFiles:
            if not os.path.exists(Path+"/usgs/"+os.path.basename(dl)):
                print "Telechargement de l'image %s" % (dl)
                command = "curl --netrc-file %s -L -c %s.cookies -b %s.cookies %s --output %s"\
                            % (netrc, Path+"/usgs/", Path+"/usgs/", url+dl, Path+"/usgs/"+os.path.basename(dl))
                os.system(command)


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
    print "Liste les dates disponibles"
    listDatesMOD09Q1 = ListUrlDates(baseUrlMOD09Q1)
    listDatesMOD11A2 = ListUrlDates(baseUrlMOD11A2)
    
    # genere une liste contenant les dates que l'on souhaite et qui sont
    # disponibles
    print "Listage des dates voulus"
    listDatesDl1 = [date1 for date1 in listDatesMOD09Q1 \
                            for date2 in listDates if date2 in date1]
    listDatesDl2 = [date1 for date1 in listDatesMOD11A2 \
                            for date2 in listDates if date2 in date1]
    
    if listDatesDl1 == [] and listDatesDl2 == [] :
        print "\nAucune image disponible pour et a partir du %s. ARRET"\
                % (dateStart)
        sys.exit()
        
    #genere une liste des urls des images a telecharger
    print "Generation des urls des images"
    listUrlsDl1 = [baseUrlMOD09Q1+date for date in listDatesDl1]
    listUrlsDl2 = [baseUrlMOD11A2+date for date in listDatesDl2]
    
    #telechargement des images

    # Create .netrc file to download datas. This file must be create at the place
    # where script was executed (/home/Donatien)
    #with open(Path+"/.netrc", "w") as netrcFile:
        #netrcFile.write("machine urs.earthdata.nasa.gov\n login \n password ")
        #netrcFile.close()
    
    Download(listUrlsDl1, Path, netrc)
    Download(listUrlsDl2, Path, netrc)


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
            telecharger des images MODIS necessaires pour calculer l'Evapora-\
            tive Fraction (EF) sur la Bretagne.")

        parser.add_argument("-path", dest="path", action="store",
                            help="Directory where download datas")
                            
        parser.add_argument("-netrc", dest="netrc", action="store",
                            help="Netrc file where url, login and password are\
                            stored")

        parser.add_argument("-fdate", dest="fdate", action="store",
                            default=datetime.date.today(),
                            help="Date a partir de laquelle telecharger des\
                            donnees (normalisee ainsi : YYYY-MM-DD)")
                            
        parser.add_argument("-ldate", dest="ldate", action="store",
                            default=datetime.date.today(),
                            help="Derniere date a laquelle telecharger des\
                            donnees (normalisee ainsi : YYYY-MM-DD)")

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
    
    Main(args.path, args.netrc, fdate, ldate)
