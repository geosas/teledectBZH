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
from datetime import datetime


def DateToYJ(date):
    '''
    Converti une date YYYY-MM-DD en YYYY-MM-DD HH:MM:SS.MS (si besoin) puis en
    YYYYJJJ
    '''
    year = date.year
    month = date.strftime('%m')
    day = date.strftime('%d')
    dayYear = date.timetuple().tm_yday
    return year, month, day, dayYear


def DownloadMODIS(wd, date):
    """
    Fonction pour telecharger des produits MODIS necessaires pour calculer EF
    """
    listImages = []
    year, month, day, dateYJ = DateToYJ(date)
    baseUrlMOD09Q1 = 'https://e4ftl01.cr.usgs.gov/MOLT/MOD09Q1.006/%s.%s.%s/MOD09Q1.A%s%s.h17v04.006' % (year, month, day, year,dateYJ)
    baseUrlMOD11A2 = 'https://e4ftl01.cr.usgs.gov/MOLT/MOD11A2.006/%s.%s.%s/MOD11A2.A%s%s.h17v04.006' % (year, month, day, year,dateYJ)
    print wd, baseUrlMOD09Q1


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

        parser.add_argument("-date", dest="date", action="store",
                            default=datetime.now(),
                            help="Date a partir de laquelle telecharger des\
                            donnees")

        args = parser.parse_args()

    DownloadMODIS(args.path, args.date)
