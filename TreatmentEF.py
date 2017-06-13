# -*- coding: utf-8 -*-
"""
Script pour calculer l'evaporative fraction (EF)
"""

import os
import sys
import numpy as np
import otbApplication as otb
import argparse
import glob
import gdal
import ogr
import Functions
from scipy import stats
import matplotlib.pyplot as plt

def DataMask(InRaster, out, filename, name, ShapeBretagne):
    """
    Masque des valeurs en dehors du territoire breton.
    """
    # Initialise un raster vide
    BandMath([InRaster], \
                "%s/%s_%s_raw2.tif" % (out, filename, name), \
                "im1b1*0")
    # Initialise a 1 l'emplacement du departement
    command = "gdal_rasterize -burn 1 %s %s"%(ShapeBretagne, "%s/%s_%s_raw2.tif" % (out, filename, name))
    os.system(command)
    
    # Conserve uniquement les valeurs se situant sur le departement
    BandMath([InRaster, "%s/%s_%s_raw2.tif" % (out, filename, name)], \
                "%s/%s_%s_raw3.tif" % (out, filename, name), \
                "im2b1==0?0:im1b1")
    
    os.remove(InRaster)
    os.remove("%s/%s_%s_raw2.tif" % (out, filename, name))    
    
    return "%s/%s_%s_raw3.tif" % (out, filename, name)
    
def ExtractClip(fichier, out, dataType, ShapeBretagne):
    """
    Extract and clip hdf files.
    """
    # Extrait les bandes du red et nir de l'archive hdf et decoupe les images
    # sur l'emprise de la bretagne.
    filename = os.path.basename(fichier)[:-4]
    if dataType == "Bands":
        dataName = ["Red", "Nir"]
    elif dataType == "Temp":
        dataName = ["Day", "Night"]
        
    ListFilesNames = []
    for i, name in zip(range(2), dataName):
        if dataType == "Bands":
            command = "gdal_translate -ot Float32 \
            -projwin -389844.619168 5439224.00949 -69235.6801105 5251930.23507 \
            HDF4_EOS:EOS_GRID:'%s':MOD_Grid_250m_Surface_Reflectance:sur_refl_b0%s \
            %s/%s_%s_raw.tif" % (fichier, int(i)+1, out, filename, name)
            os.system(command)
            
            # Masque les valeurs inutiles et aberrantes
            OutRaster = DataMask("%s/%s_%s_raw.tif" % (out, filename, name), out, filename, name, ShapeBretagne)
            
            # Applique le scale factor           
            BandMath([OutRaster], \
                        "%s/%s_%s.tif" % (out, filename, name), \
                        "im1b1*0.0001")

            os.remove(OutRaster)
            
        elif dataType == "Temp":
            command = "gdal_translate -ot Float32 -r nearest -tr 231.656 231.656\
            -projwin -389844.619168 5439224.00949 -69235.6801105 5251930.23507 \
            HDF4_EOS:EOS_GRID:'%s':MODIS_Grid_8Day_1km_LST:LST_%s_1km \
            %s/%s_%s_raw.tif" % (fichier, name, out, filename, name)            
            os.system(command)
            
            # Masque les valeurs inutiles et aberrantes
            OutRaster = DataMask("%s/%s_%s_raw.tif" % (out, filename, name), out, filename, name, ShapeBretagne)
            
            
            BandMath([OutRaster], \
                        "%s/%s_%s.tif" % (out, filename, name), \
                        "im1b1*0.02")
                        
            os.remove(OutRaster)   
            
        ListFilesNames.append(out+"/"+filename+"_%s.tif" % (name))
    return ListFilesNames, filename
    

def CalcNDVI(ListFilesBands, out, filenameBand):
    """
    """
    # Calcule le NDVI
    NDVITemp = BandMath(ListFilesBands, \
                    out+"/"+filenameBand+"_NdviTemp.tif", \
                    "ndvi(im1b1, im2b1)") 
                       
    # Supprime valeurs aberrantes du NDVI causee par la mer              
    NDVI = BandMath([NDVITemp], \
                    out+"/"+filenameBand+"_Ndvi.tif", \
                    "im1b1<0||im1b1>1?0:im1b1")        
                    
    # Supprime le fichier intermediaire                
    os.remove(out+"/"+filenameBand+"_NdviTemp.tif")
    return NDVI
    
    
def CalcFVC(raster, out):
    """
    """
    Data, Xsize, Ysize, Projection, Transform, RasterBand = Functions.RastOpen(raster, 1)
    FVC = ((Data - np.min(Data))/(np.max(Data)-np.min(Data)))**2
    Functions.RastSave(out, Xsize, Ysize, Transform, FVC, Projection, gdal.GDT_Float32)
    return FVC


def CalcTjTn(ListFilesTemp, out):
    """
    """
    # Ouvre les raster de temperature de jour et de nuit
    Tj, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj, RasterBand_Tj = Functions.RastOpen(ListFilesTemp[0], 1)
    Tn, Xsize_Tn, Ysize_Tn, Projection_Tn, Transform_Tn, RasterBand_Tn = Functions.RastOpen(ListFilesTemp[1], 1) 
    # Identifie les cellules en nodata et supprime leur equivalent dans les deux images
    Tj[np.where(Tn==0)]=np.nan
    Tn[np.where(Tj==0)]=np.nan 
    # Applique Tj_Tn
    TjTn = Tj - Tn  
    # Enregistre l'image
    Functions.RastSave(out, Xsize_Tj, Ysize_Tj, Transform_Tj, TjTn, Projection_Tj, gdal.GDT_Float32)
    return TjTn, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj
    
    
def CalcEFInterval(FVC, TjTn):
    """
    """
    Seuils = np.linspace(0,1,11)
    xmin = []
    xmax = []
    ymin = []
    ymax = []
    couleur = ["Red","Green","Blue","Yellow","Purple","Black","Orange","Cyan","Grey","Brown"]
    for i in range(10):
        IntervFVC = FVC[(FVC > Seuils[i]) & (FVC < Seuils[i+1])]
        IntervTemp = TjTn[(FVC > Seuils[i]) & (FVC < Seuils[i+1])]
        IndexSort = np.argsort(IntervTemp)
        FVCSort = IntervFVC[IndexSort]
        TjTnSort = IntervTemp[IndexSort]
        TjTnVal = int(TjTnSort.size * 0.05)
        
        FVCMin = FVCSort[:TjTnVal]
        FVCMax = FVCSort[-(TjTnVal):]
        TjTnMin = TjTnSort[:TjTnVal]
        TjTnMax = TjTnSort[-(TjTnVal):]

        if i==0:
            StackTjTnMin = TjTnMin
            StackTjTnMax = TjTnMax
            StackFVCMin = FVCMin
            StackFVCMax = FVCMax
        else:
            StackTjTnMin = np.hstack((TjTnMin, StackTjTnMin))
            StackTjTnMax = np.hstack((TjTnMax, StackTjTnMax))
            StackFVCMin = np.hstack((FVCMin, StackFVCMin))
            StackFVCMax = np.hstack((FVCMax, StackFVCMax))
        
        xmin.append(np.mean(FVCMin))
        xmax.append(np.mean(FVCMax))
        ymin.append(np.mean(TjTnMin))
        ymax.append(np.mean(TjTnMax))
        
        plt.scatter(FVCMin, TjTnMin, c=couleur[i], edgecolor = 'none')
        plt.scatter(FVCMax, TjTnMax, c=couleur[i], edgecolor = 'none')
        plt.scatter(np.mean(FVCMin), np.mean(TjTnMin), c=couleur[i])
        plt.scatter(np.mean(FVCMax), np.mean(TjTnMax), c=couleur[i])
    
    return xmin, xmax, ymin, ymax, StackTjTnMin, StackTjTnMax, StackFVCMin, StackFVCMax


def LineRegression(xmin, xmax, ymin, ymax, StackTjTnMin, StackTjTnMax, StackFVCMin, StackFVCMax):
    """
    """
    print "Calcul des droites de regression"
        
    SlopeMin, InterceptMin, RValueMin, PValueMin, STDErrMin = stats.linregress(xmin, ymin)
    print 'Droite moyenne humide'
    print 'R2 = ', RValueMin**2
    print  'P-value = ', PValueMin
    print 'Ecart type = ', STDErrMin
    LineMinFroid = SlopeMin*xmin[0] + InterceptMin
    LineMaxFroid = SlopeMin*xmin[-1] + InterceptMin
    
    SlopeMax, InterceptMax, RValueMax, PValueMax, STDErrMax = stats.linregress(xmax, ymax)
    print 'Droite moyenne sec'
    print 'R2 = ', RValueMax**2
    print  'P-value = ', PValueMax
    print 'Ecart type = ', STDErrMax
    LineMinSec = SlopeMax*xmax[0] + InterceptMax
    LineMaxSec = SlopeMax*xmax[-1] + InterceptMax
    
    SlopeAllMin, InterceptAllMin, RValueAllMin, PValueAllMin, STDErrAllMin = stats.linregress(StackFVCMin, StackTjTnMin)
    print 'Droite ensemble humide'
    print 'R2 = ', RValueAllMin**2
    print  'P-value = ', PValueAllMin
    print 'Ecart type = ', STDErrAllMin
    LineAllMinFroid = SlopeAllMin*StackFVCMin[0] + InterceptAllMin
    LineAllMaxFroid = SlopeAllMin*StackFVCMin[-1] + InterceptAllMin
    
    SlopeAllMax, InterceptAllMax, RValueAllMax, PValueAllMax, STDErrAllMax = stats.linregress(StackFVCMax, StackTjTnMax)
    print StackTjTnMax
    print 'Droite ensemble sec'
    print 'R2 = ', RValueAllMax**2
    print  'P-value = ', PValueAllMax
    print 'Ecart type = ', STDErrAllMax
    LineAllMinSec = SlopeAllMax*StackFVCMax[0] + InterceptAllMax
    LineAllMaxSec = SlopeAllMax*StackFVCMax[-1] + InterceptAllMax
    
    yminSort = np.sort(ymin)
    
    print "Affiche les droites"
    plt.plot([xmin[0], xmin[-1]], [LineMinFroid, LineMaxFroid])
    plt.plot([xmax[0], xmax[-1]],[LineMinSec, LineMaxSec])
    plt.plot([StackFVCMin[0], StackFVCMin[-1]],[LineAllMinFroid, LineAllMaxFroid])
    plt.plot([StackFVCMax[0], StackFVCMax[-1]],[LineAllMinSec, LineAllMaxSec])
    plt.plot([0,1],[yminSort[1],yminSort[1]])
    plt.show()
    
    return SlopeAllMax, InterceptAllMax, yminSort


def CalcEF(FVC, SlopeAllMax, InterceptAllMax, TjTn, yminSort, out, filenameTemp, Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj):
    """
    """
    Tmax = SlopeAllMax * FVC + InterceptAllMax
    Phi = ((Tmax - TjTn)/(Tmax - yminSort[1]))*1.26
    e_sat_ta = 1000*np.exp(52.57633-(6790.4985/TjTn)-5.02808*np.log(TjTn))
    delta = (e_sat_ta/TjTn)*((6790.4985/TjTn)-5.02808)
    EF = (delta/(delta+66))*Phi
    
    # Enregistre l'image
    Functions.RastSave(out+"/"+filenameTemp+"_EF.tif", Xsize_Tj, Ysize_Tj, Transform_Tj, EF, Projection_Tj, gdal.GDT_Float32)
    
    
def BandMath(inFiles, outFile, expr):
    """
    """
    BandMath = otb.Registry.CreateApplication("BandMath")   
    BandMath.SetParameterStringList("il", inFiles)
    BandMath.SetParameterString("out", outFile)
    BandMath.SetParameterString("exp", expr)
    BandMath.ExecuteAndWriteOutput()
    return outFile


def Main(datas, out, ShapeBretagne):
    """  
    """
    # Liste les fichiers reflectance et temperature
    ListFilesBands = glob.glob(datas+"/*%s*.hdf" % ("MOD09Q1"))
    ListFilesTemp = glob.glob(datas+"/*%s*.hdf" % ("MOD11A2"))
    ListFilesBands.sort()
    ListFilesTemp.sort()
    
    #pour chaque fichier
    for FilesBands, FilesTemp in zip(ListFilesBands, ListFilesTemp):
        # Extract au format tif et clip les bandes et temperatures
        ListFilesBands, filenameBand = ExtractClip(FilesBands, out, "Bands", ShapeBretagne)
        ListFilesTemp, filenameTemp = ExtractClip(FilesTemp, out, "Temp", ShapeBretagne)
        
        # Calcule le NDVI
        NDVI = CalcNDVI(ListFilesBands, out, filenameBand)
        
        # Calcule le FVC               
        FVC = CalcFVC(NDVI, out+"/"+filenameTemp+"_FVC.tif")   
        
        # Calcule Tj - Tn
        TjTn, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj = CalcTjTn(ListFilesTemp, out+"/"+filenameTemp+"_TjTn.tif")
        
        # Supprime les valeurs de FVC ou la temperature n'est pas disponible
        FVC[np.where(TjTn==0)]=np.nan
        
#        Plot nuage de points
#        plt.scatter(FVC, TjTn)
#        plt.title('Representation du nuage points Tj-Tn / FVC')
#        plt.xlabel('FVC')
#        plt.ylabel('Tj-Tn')
#        plt.show()
        
        # Calcule les donnees necessaires pour calculer les droites de regression
        xmin, xmax, ymin, ymax, StackTjTnMin, StackTjTnMax, StackFVCMin, StackFVCMax = CalcEFInterval(FVC, TjTn)

        # Calcule les droites de regression et les donnees necessaire pour calculer EF
        SlopeAllMax, InterceptAllMax, yminSort = LineRegression(xmin, xmax, ymin, ymax, StackTjTnMin, StackTjTnMax, StackFVCMin, StackFVCMax)

        # Calcul d'EF
        CalcEF(FVC, SlopeAllMax, InterceptAllMax, TjTn, yminSort, out, filenameTemp, Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj)
        
        # Convert kelvin to celsius
        #BandMath(image, out, "im1b1-273.15")
        
        
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
        
        parser.add_argument("-d", dest="datas", action="store",
                            help="Datas directory")

        parser.add_argument("-out", dest="out", action="store",
                            help="Out directory")
        
        parser.add_argument("-shp", dest="shp", action="store",
                            default = "/home/donatien/ProjectGeoBretagne/Datas/Bretagne.shp", 
                            help="Shapefile de la Bretagne")
                            
        args = parser.parse_args()
    
    if not os.path.exists(args.out):
        os.mkdir(args.out)
        
    Main(args.datas, args.out, args.shp)