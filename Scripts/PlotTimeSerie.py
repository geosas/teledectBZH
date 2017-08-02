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
import ogr
import osr
import gdal
import datetime
import matplotlib
import operator as op
#matplotlib.use('Agg')
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
    projection = raster.GetProjectionRef()
    transform = raster.GetGeoTransform()
    xsize = raster.RasterXSize
    ysize = raster.RasterYSize
    
    # convert raster to an array
    datas = rasterBand.ReadAsArray()
    
    return datas, xsize, ysize, projection, transform
    
def listRasters(datas):
    """
    fdate.strftime('%m-%d-%Y')

    """
    lRasters = []
    lDates = []
    for path, dossiers, rasters in os.walk(datas):
        rasters.sort()
        for raster in rasters :
            # extrait la date du fichier XXX_YYYYMMDD.tif
            date = raster[-12:-4]
            try:
                dateConvert = datetime.datetime.strptime(date, "%Y%m%d")
                lDates.append(dateConvert)
            except ValueError :
                sys.exit("L'image %s n'est pas au format XXX_YYYYMMDD.tif" % (raster))
            lRasters.append(path+"/"+raster)
    return lRasters, lDates
    
def extractArea(shape, nodata, xsize, ysize, projection, transform):
    """
    """
    # Ouverture du shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if not os.path.exists(shape):
        sys.exit("Le fichier shape indique n'existe pas")        
    dtSource = driver.Open(shape, 0)    
    if dtSource is None:
        sys.exit("Impossible d'ouvrir le shapefile")    
    layer = dtSource.GetLayer()
    feature = layer.GetNextFeature()
    
    # Variables du raster
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]
    
    # Etendue de l'entite du shapefile
    geom = feature.GetGeometryRef()
    if (geom.GetGeometryName() == 'MULTIPOLYGON'):
        count = 0
        pointsX = []; pointsY = []
        for polygon in geom:
            geomInner = geom.GetGeometryRef(count)
            ring = geomInner.GetGeometryRef(0)
            numpoints = ring.GetPointCount()
            for p in range(numpoints):
                lon, lat, z = ring.GetPoint(p)
                pointsX.append(lon)
                pointsY.append(lat)
            count += 1
    elif (geom.GetGeometryName() == 'POLYGON'):
        ring = geom.GetGeometryRef(0)
        numpoints = ring.GetPointCount()
        pointsX = []; pointsY = []
        for p in range(numpoints):
            lon, lat, z = ring.GetPoint(p)
            pointsX.append(lon)
            pointsY.append(lat)

    else:
        sys.exit("L'entite n'est pas un polygon")
        
    xmin = min(pointsX)
    xmax = max(pointsX)
    ymin = min(pointsY)
    ymax = max(pointsY)

    # Calcul l'emprise de l'entite selon la taille du raster
    xoff = int((xmin - xOrigin)/pixelWidth)
    yoff = int((yOrigin - ymax)/pixelWidth)
    xcount = int((xmax - xmin)/pixelWidth)+1
    ycount = int((ymax - ymin)/pixelWidth)+1
 
    return yoff, ycount, xoff, xcount

    
def main(datas, out, roi, nan, mean, mMean, title, ylabel):
    """
    """
    # Liste tous les fichiers rasters et teste s'ils ont tous une information
    # temporelle dans leur nom
    lRasters, lDates = listRasters(datas)
    
    # Initialise la combinaison de tous les rasters dans un seul array
    datas, xsize, ysize, projection, transform = OpenRaster(lRasters[0],1)
    datas[np.where(datas==-999)]=np.nan

    # Ajoute les donnees de chacune des images dans la matrice en 3D
    for raster in lRasters[1:]:
        data, xsize, ysize, projection, transform = OpenRaster(raster, 1)
	# Change les valeurs des nodata en nan
    	data[np.where(data==-999)]=np.nan
        datas = np.dstack((datas, data))
        
    # Calcule l'emprise de l'entite par rapport au raster
    yoff, ycount, xoff, xcount = extractArea(roi, nan, xsize, ysize, projection, transform)
    
    # Calcule la valeur moyenne pour chaque date
    yList = [np.nanmean(datas[yoff:yoff+ycount, xoff: xoff+xcount,i]) for i in range(len(lRasters))]
    
    if mMean==True:    
        yArray = np.asarray(yList)
        yMobile = yArray[0]
        for i in range(len(yList)-2):
            yMobile = np.append(yMobile, np.mean(yArray[0+i:3+i]))   
        yMobile = np.append(yMobile, yArray[-1])
        yMobileList = yMobile.tolist()

    # Calcule la valeur minimale pour chaque date
    #yMin = [np.nanmin(datas[yoff:yoff+ycount, xoff: xoff+xcount,i]) for i in range(len(lRasters))]
    
    # Calcule la valeur maximale pour chaque date
    #yMax = [np.nanmax(datas[yoff:yoff+ycount, xoff: xoff+xcount,i]) for i in range(len(lRasters))]
    
    # Calcule l'ecart type pour chaque date
    yStd = [np.nanstd(datas[yoff:yoff+ycount, xoff: xoff+xcount,i]) for i in range(len(lRasters))]
    yMinStd = [op.sub(i,j) for i, j in zip(yList, yStd)]
    yMaxStd = [sum(i) for i in zip(yList, yStd)]
    
    fig, ax = plt.subplots(figsize=(20, 10),sharex=True)
    
    if mean==True:
        plt.plot(lDates, yList, color="black", label="moyenne")
    plt.plot(lDates, yMinStd, color="green")
    plt.plot(lDates, yMaxStd, color="green")
    if mMean==True:
        plt.plot(lDates, yMobileList, color="red", label="moyenne glissante")
    
    ax.fill_between(lDates, yMinStd, yMaxStd, alpha=0.4, label="intervalle de confiance", color="green")
    plt.title(title, fontsize="24")
    plt.ylabel(ylabel, fontsize="20")
    plt.xlabel("Date", fontsize="20")
    plt.legend()
    plt.gcf().autofmt_xdate()
    plt.savefig(out+"/output.png", dpi=300)
    plt.show()
    
    
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
                            help="Datas directory", required="True")
                            
        parser.add_argument("-title", dest="title", action="store",
                            help="Title of graphic", required="True")
                            
        parser.add_argument("-ylabel", dest="ylabel", action="store",
                            help="Title of y axis", required="True") 
                            
        parser.add_argument("-o", dest="out", action="store",
                            help="Out directory", required="True")
        
        parser.add_argument("-roi", dest="roi", action="store", 
                            help="Shapefile de la zone d'interet", required="True")
                            
        parser.add_argument("-ndata", dest="nan", action="store", 
                            help="Valeur du nodata", required="True")
        
        parser.add_argument("-a", dest="mean", action="store_true", 
                            help="Plot mean ?", default="False") 
                            
        parser.add_argument("-b", dest="mMean", action="store_true", 
                            help="Plot mobile mean ?", default="False")                    
                            
        args = parser.parse_args()
        
    np.seterr(divide='ignore', invalid='ignore')
    if not os.path.exists(args.out):
        os.mkdir(args.out)
        
    main(args.datas, args.out, args.roi, args.nan, args.mean, args.mMean, args.title, args.ylabel)
    
    print "\nGraphique genere"
