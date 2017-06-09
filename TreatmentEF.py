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

def ExtractClip(fichier, out, dataType):
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
            -projwin -390689.706353 5484046.86307 -90843.2433257 5198819.47034 \
            HDF4_EOS:EOS_GRID:'%s':MOD_Grid_250m_Surface_Reflectance:sur_refl_b0%s \
            %s/%s_%s.tif" % (fichier, int(i)+1, out, filename, name)            
        elif dataType == "Temp":
            command = "gdal_translate -ot Float32 \
            -projwin -390689.706353 5484046.86307 -90843.2433257 5198819.47034 \
            HDF4_EOS:EOS_GRID:'%s':MODIS_Grid_8Day_1km_LST:LST_%s_1km \
            %s/%s_%s.tif" % (fichier, name, out, filename, name)            
        os.system(command)
        ListFilesNames.append(out+"/"+filename+"_%s.tif" % (name))
    return ListFilesNames

    
def BandMath(indata, outdata):
    """
    """
    BandMath = otb.Registry.CreateApplication("BandMath")   
    BandMath.SetParameterStringList("il", ['verySmallFSATSW_r.tif', 'verySmallFSATSW_nir.tif', 'verySmallFSATSW.tif'])
    BandMath.SetParameterString("out", "apTvUtBandMathOutput.tif")
    BandMath.SetParameterString("exp", "cos(im1b1) > cos(im2b1) ? im3b1 : im3b2")
    BandMath.ExecuteAndWriteOutput()

def Main(datas, out):
    """
    
    """
    # Liste les fichiers reflectance et temperature
    ListFilesBands = glob.glob(datas+"/*%s*.hdf" % ("MOD09Q1"))
    ListFilesTemp = glob.glob(datas+"/*%s*.hdf" % ("MOD11A2"))
    
    #pour chaque fichier, calcul le NDVI
    for FilesBands, FilesTemp in zip(ListFilesBands, ListFilesTemp):
        ListFilesBands = ExtractClip(FilesBands, out, "Bands")
        ListFilesTemp = ExtractClip(FilesTemp, out, "Temp")
        print ListFilesBands
        print ListFilesTemp
        
        
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

        args = parser.parse_args()
    
    if not os.path.exists(args.out):
        os.mkdir(args.out)
        
    Main(args.datas, args.out)