# -*- coding: utf-8 -*-
"""
Script pour generer un profil phenologique selon un repertoire contenant
une serie d'images temporelles et un shapefile correspondant a la zone pour
laquelle generer les profils (moyen, min, max)
"""
import os
import sys
import numpy as np
import argparse
import glob
import gdal
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def OpenRaster(inRaster, band):
    """
    Open raster and return some information about it.
    
    in :
        name : string
               raster name
    out :
        datas : array
                numpy array from raster dataset
        xsize : string
                xsize of raster dataset
        ysize : string
                ysize of raster dataset
        projection : string
                     projection of raster dataset
        transform : string
                    coordinates and pixel size of raster dataset
    """    
    raster = gdal.Open(inRaster, 0)
    rasterBand = raster.GetRasterBand(band)
    
    # property of raster
    #projection = raster.GetProjectionRef()
    #transform = raster.GetGeoTransform()
    xsize = raster.RasterXSize
    ysize = raster.RasterYSize
    
    # convert raster to an array
    datas = rasterBand.ReadAsArray()
    
    return datas, xsize, ysize, #projection, transform
    
def listRasters(datas):
    """
    fdate.strftime('%m-%d-%Y')

    """
    lRasters = []
    for path, dossiers, rasters in os.walk(datas):
        for raster in rasters :
            # extrait la date du fichier XXX_YYYYMMDD.tif
            date = raster[-12:-4]
            try:
                datetime.datetime.strptime(date, "%Y%m%d")
            except ValueError :
                print "L'image %s n'est pas au format XXX_YYYYMMDD.tif" % (raster)
                sys.exit()
            lRasters.append(path+"/"+raster)
    lRasters.sort()
    return lRasters
            dstack
def main(datas, out, roi):
    """
    """
    # Liste tous les fichiers rasters et teste s'ils ont tous une information
    # temporelle dans leur nom
    lRasters = listRasters(datas)
    
    # Initialise un tableau en 3 dimensions selon la dimension d'une image et
    # le nombre d'images
    data, xsize, ysize = OpenRaster(lRasters[0],1)
    del data
    matrix = np.empty((xsize,ysize,len(lRasters)))
    
    # Ajoute les donnees de chacune des images dans la matrice en 3D
    for raster in lRasters:
        data = OpenRaster(raster, 1)
        
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", prog, " --help"
        print "        or : ", prog, " -h"
        sys.exit(-1)
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description="Script generer un graphique\
        permettant de suivre l'evolution d'une zone d'etude avec une serie\
        d'images raster.")
        
        parser.add_argument("-d", dest="datas", action="store",
                            help="Datas directory")

        parser.add_argument("-o", dest="out", action="store",
                            help="Out directory")
        
        parser.add_argument("-roi", dest="roi", action="store", 
                            help="Shapefile de la zone d'interet")
                            
        args = parser.parse_args()
        
    np.seterr(divide='ignore', invalid='ignore')
    if not os.path.exists(args.out):
        os.mkdir(args.out)
        
    main(args.datas, args.out, args.roi)
    
    print "\nGraphique genere"
