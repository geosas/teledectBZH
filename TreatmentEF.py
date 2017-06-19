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
import datetime
import Functions
from scipy.stats import linregress
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
    command = "gdal_rasterize -burn 1 %s %s"%(ShapeBretagne, \
                "%s/%s_%s_raw2.tif" % (out, filename, name))
    os.system(command)
    
    # Conserve uniquement les valeurs se situant sur le departement
    BandMath([InRaster, "%s/%s_%s_raw2.tif" % (out, filename, name)], \
                "%s/%s_%s_raw3.tif" % (out, filename, name), \
                "im2b1==0?0:im1b1")
    
    # Supprime les fichiers intermediaires
    os.remove(InRaster)
    os.remove("%s/%s_%s_raw2.tif" % (out, filename, name))    
    
    return "%s/%s_%s_raw3.tif" % (out, filename, name)
    
def ExtractClip(fichier, out, dataType, ShapeBretagne):
    """
    Extract, clip and reproject hdf files.
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
            RastClip = "%s/%s_%s_raw.tif" % (out, filename, name)
            RastReproject = "%s/%s_%s_rproj.tif" % (out, filename, name)
            
            # Decoupe le raster et le converti au format tif
            command = "gdal_translate -ot Float32 \
            -projwin -386371 5533708 -3708 5211341 \
            HDF4_EOS:EOS_GRID:'%s':MOD_Grid_250m_Surface_Reflectance:sur_refl_b0%s \
            %s" % (fichier, int(i)+1, RastClip)
            os.system(command)
            
            # Reprojete le raster en EPSG:2154
            command = "gdalwarp -t_srs EPSG:2154 %s %s" % (RastClip, RastReproject)
            os.system(command)
            
            # Masque les valeurs inutiles et aberrantes
            OutRaster = DataMask(RastReproject, out, filename, name, ShapeBretagne)
            
            # Applique le scale factor           
            BandMath([OutRaster], \
                        "%s/%s_%s.tif" % (out, filename, name), \
                        "im1b1*0.0001")
            
            os.remove(RastClip)
            os.remove(OutRaster)
            
        elif dataType == "Temp":
            RastClip = "%s/%s_%s_raw.tif" % (out, filename, name)
            RastReproject = "%s/%s_%s_rproj.tif" % (out, filename, name)
            
            # Decoupe le raster et le converti au format tif
            command = "gdal_translate -ot Float32 -r nearest -tr 231.656 231.656\
            -projwin -386371 5533108 -3976 5211056 \
            HDF4_EOS:EOS_GRID:'%s':MODIS_Grid_8Day_1km_LST:LST_%s_1km \
            %s" % (fichier, name, RastClip)            
            os.system(command)
            
            # Reprojete le raster en EPSG:2154
            command = "gdalwarp -t_srs EPSG:2154 %s %s" % (RastClip, RastReproject)
            os.system(command)
            
            # Masque les valeurs inutiles et aberrantes
            OutRaster = DataMask("%s" % (RastReproject), \
                        out, filename, name, ShapeBretagne)
            
            # Applique le scale factor
            BandMath([OutRaster], \
                        "%s/%s_%s.tif" % (out, filename, name), \
                        "im1b1*0.02")
                        
            os.remove(RastClip)           
            os.remove(OutRaster)   
            
        ListFilesNames.append(out+"/"+filename+"_%s.tif" % (name))
    return ListFilesNames, filename
    

def CalcNDVI(ListFilesBands, out, filenameBand):
    """
    Calcule le NDVI et ne conserve que les valeurs entre 0 et 1 (necessaire 
    a cause des valeurs se situant sur la mer).
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
    Calcule le Fractional Vegetation Cover.
    """
    Data, Xsize, Ysize, Projection, Transform, RasterBand = Functions.RastOpen(raster, 1)
    FVC = ((Data - np.min(Data))/(np.max(Data)-np.min(Data)))**2
    Functions.RastSave(out, Xsize, Ysize, Transform, FVC, Projection, gdal.GDT_Float32)
    return FVC


def CalcTjTn(ListFilesTemp, out):
    """
    Calcule Tj - Tn et, pour les pixels n'ayant aucune donnée sur une des
    images, supprime les même pixels sur l'autre. Cela évite d'avoir des
    temperatures aberrantes suite a la soustraction.
    """
    # Ouvre les raster de temperature de jour et de nuit
    Tj, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj, RasterBand_Tj = \
        Functions.RastOpen(ListFilesTemp[0], 1)
    Tn, Xsize_Tn, Ysize_Tn, Projection_Tn, Transform_Tn, RasterBand_Tn = \
        Functions.RastOpen(ListFilesTemp[1], 1) 
    # Identifie les cellules en nodata et supprime leur equivalent dans les deux images
    Tj[np.where(Tn==0)]=np.nan
    Tn[np.where(Tj==0)]=np.nan 
    # Applique Tj_Tn
    TjTn = Tj - Tn  
    # Enregistre l'image
    Functions.RastSave(out, Xsize_Tj, Ysize_Tj, Transform_Tj, TjTn, \
                        Projection_Tj, gdal.GDT_Float32)
    return TjTn, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj, Tj, Tn


def courbes_phi(indice, temp, nb_interval=25, pourcentage=1):
    """Renvoie les points (et leur moyenne) composants les bords humide et sec.

    La valeur de phi est calculée par double interpolation en fonction du 
    nombre d'intevalles choisi et du pourcentage de point dans ces intervalles.
    La fonction renvoie, pour les bords humide et sec, les points ainsi que
    leur moyenne pour chaque intervalle.

    Arguments
    ---------
    indice : numpy.array
             indice de végétation choisi en abscisse
    temp : numpy.array
           température choisie en ordonnée
    nb_interval : int
                  nombre d'intervalle de découpage des données (10 par défaut)
    pourcentage : float
                  pourcentage de points utilisés dans la méthode exprimé en % (5 par défaut)
    Returns
    -------
    tuple : (numpy.array, numpy.array), (numpy.array, numpy.array)
            Renvoie un tuple de 2 tuples :
                - tous les points composants les bords humides (pts_inf) et sec (pts_sup)
                - les points moyens composants les bords humides (pts_inf_mean) et sec (pts_sup_mean)
    """
    # On retire les valeurs NaN dans chaque tableau et leur équivalent dans l'autre tableau
    ind_nan = np.logical_not(np.logical_or(np.isnan(temp), np.isnan(indice)))
    indice = indice[ind_nan]
    temp = temp[ind_nan]

    # Pour chaque intervalle, on ne garde que les pourcentages des valeurs supérieures et inférieures
    intervals = np.linspace(indice.min(), indice.max(), nb_interval+1)
    for i in range(nb_interval):
        # Points contenus dans l'intervalle considéré
        if i == nb_interval-1:
            cond = (indice>=intervals[i]) & (indice<=intervals[i+1])
        else:
            cond = (indice>=intervals[i]) & (indice<intervals[i+1])
        x = indice[cond]
        y = temp[cond]
        if x.size > 0:
            print("Intervalle %d : nombre de points = %d" % (i, x.size),
                  "- temp mini = %f - temp maxi = %f" % (np.min(y), np.max(y)))#(y[0], y[-1]))
        else:
            print("Il n'y a pas de points dans l'intervale",  i)

        # On trie les données selon la température pour ne garder que les points supérieurs et inférieurs
        ind_sort_temp = np.argsort(y)
        x = x[ind_sort_temp]
        y = y[ind_sort_temp]

        # Calcul du nombre de points dans l'intervalle
        nb_val = int(x.size * pourcentage / 100)

        # Attention au cas où il n'y a aucun point dans un intervalle
        if nb_val >= 1:
            x_inf = x[:nb_val]
            x_sup = x[-nb_val:]
            y_inf = y[:nb_val]
            y_sup = y[-nb_val:]
            x_mid = intervals[i] + (intervals[i+1]-intervals[i])/2

            # Pour tous les points l'array créé à 3 lignes et nb_val colonnes.
            # np.transpose le transforme en un array de nb_val lignes et 3 colonnes.
            # La troisième colonne représente le numéro de l'intervalle.
            arr_inf = np.transpose(np.array([x_inf, y_inf, np.zeros(x_inf.size, dtype=np.float32)+i]))
            arr_sup = np.transpose(np.array([x_sup, y_sup, np.zeros(x_inf.size, dtype=np.float32)+i]))
            mean_inf = np.array([x_mid, y_inf.mean(), i])
            mean_sup = np.array([x_mid, y_sup.mean(), i])

            if i == 0:
                pts_inf = arr_inf
                pts_sup = arr_sup
                pts_inf_mean = mean_inf
                pts_sup_mean = mean_sup
            else:
                pts_inf = np.vstack((pts_inf, arr_inf))
                pts_sup = np.vstack((pts_sup, arr_sup))
                pts_inf_mean = np.vstack((pts_inf_mean, mean_inf))
                pts_sup_mean = np.vstack((pts_sup_mean, mean_sup))

    return (pts_inf, pts_sup), (pts_inf_mean, pts_sup_mean)
    
    
def Graph(nbInterval, pourcentage, pts_inf_mean, pts_sup_mean, pts_inf, pts_sup, out):
    """
    Genere un graphique permettant d'identifier des intervalles de temperatures
    mini et maxi avec des droites de regressions.
    """
    # Liste de couleurs pour l'affichage des points des intervalles
    color_list = plt.cm.Set1(np.linspace(0, 1, nbInterval))
    
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.suptitle("Estimation du coefficient de Priestley-Taylor \n par \
    double interpolation", fontsize=20)
    x_reg = np.array([0, 1])
    
    # Points moyens
    print("*** Régression avec les points moyens ***")
    reg_h_moy = linregress(pts_inf_mean[:, 0], pts_inf_mean[:, 1])
    print("Bord humide : R2 = %f - pente = %f - intersect = %f" % 
          (reg_h_moy[2] ** 2, reg_h_moy[0], reg_h_moy[1]))
    y_inf = reg_h_moy[0]*x_reg + reg_h_moy[1]
    
    # Affichage des points moyens du bord humide
    ax.scatter(pts_inf_mean[:, 0], pts_inf_mean[:, 1], zorder=10, c="k")
    
    # Affichage de la régression des points moyens du bord humide
    ax.plot(x_reg, y_inf,'k-')
    reg_s_moy = linregress(pts_sup_mean[:, 0], pts_sup_mean[:, 1])
    print("Bord sec : R2 = %f - pente = %f - intersect = %f" %
          (reg_s_moy[2] ** 2, reg_s_moy[0], reg_s_moy[1]))
    y_sup = reg_s_moy[0]*x_reg + reg_s_moy[1]
    
    # Affichage des points moyens du bord sec
    pts = ax.scatter(pts_sup_mean[:, 0], pts_sup_mean[:, 1], c="k", zorder=10, label="Points moyens")
    
    # Affichage de la régression des points moyens du bord sec
    reg_moy, = ax.plot(x_reg, y_sup, 'k-', label="Regression des points moyens")
    
    # Affichage doite du bord humide
    temp_hum = pts_inf_mean.copy()
    arg = np.argsort(temp_hum[:, 1])
    y_min_hum = temp_hum[:, 1][arg][1]
    plot_reg_humide, = ax.plot(x_reg, [y_min_hum, y_min_hum],'r-', lw=2, label="Droite du bord humide")
    
    # Tous les points
    print("*** Régression avec l'ensemble des points ***")
    reg_h_tot = linregress(pts_inf[:, 0], pts_inf[:, 1])
    print("Bord humide : R2 = %f - pente = %f - intersect = %f" %
          (reg_h_tot[2] ** 2, reg_h_tot[0], reg_h_tot[1]))

    y_inf = reg_h_tot[0]*x_reg + reg_h_tot[1]
    
    # Affichage de tous les points du bord humide
    ax.scatter(pts_inf[:, 0], pts_inf[:, 1], color=color_list[pts_inf[:, 2].astype(int)],
               alpha=0.2, edgecolor='none')
               
    # Affichage de la régression de tous les points du bord humide
    ax.plot(x_reg, y_inf, 'b-')
    reg_s_tot = linregress(pts_sup[:, 0], pts_sup[:, 1])
    print("Bord sec : R2 = %f - pente = %f - intersect = %f" %
          (reg_s_tot[2] ** 2, reg_s_tot[0], reg_s_tot[1]))   
    y_sup = reg_s_tot[0]*x_reg + reg_s_tot[1]
    
    # Affichage de tous les points du bord sec
    ax.scatter(pts_sup[:, 0], pts_sup[:, 1], color=color_list[pts_sup[:, 2].astype(int)],
               alpha=0.2, edgecolor="none")
               
    # Affichage de la régression de tous les points du bord sec
    plot_reg_tot, = ax.plot(x_reg, y_sup,'b-', label="Regression de l'ensemble des points")
    
    ax.set_title("\nNombre d'intervalle = %d - Pourcentage = %.1f%%"  % (nbInterval, pourcentage), fontsize=16)
    ax.set_xlabel("FVC", fontsize=16)
    ax.set_ylabel("Tj - Tn", fontsize=16)
    plt.legend(handles=[pts, reg_moy, plot_reg_tot, plot_reg_humide])
    # Sauvegarde de la figure au format png
    plt.savefig(out, dpi=300)
    plt.show()

    return y_min_hum, reg_s_tot[0], reg_s_tot[1]


def CalcEF(FVC, SlopeSec, InterceptSec, TjTn, Tj, Tn, TminHumide, out, \
    Date, Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj):
    """
    """
    Tmax = SlopeSec * FVC + InterceptSec
    Phi = ((Tmax - TjTn)/(Tmax - TminHumide)*1.26)
    print("Nombre de valeurs négative : %d" % (Phi < 0).sum())
    print("Nombre de valeurs > 1,26 : %d" % (Phi > 1.26).sum())
    tmoy = (Tj + Tn)/2
    ESatTa = 1000 * np.exp(52.57633 - (6790.4985 / tmoy) - 5.02808 * np.log(tmoy))
    delta = (ESatTa / tmoy) * ((6790.4985 / tmoy) - 5.02808)
    EF = (delta/(delta+66))*Phi

    # Enregistre l'image
    Functions.RastSave(out+"/EF_%s.tif" % (Date), Xsize_Tj, Ysize_Tj, \
                        Transform_Tj, EF, Projection_Tj, gdal.GDT_Float32)
    
    
def BandMath(inFiles, outFile, expr):
    """
    Application Bandmath de l'orpheo tools box
    """
    BandMath = otb.Registry.CreateApplication("BandMath")   
    BandMath.SetParameterStringList("il", inFiles)
    BandMath.SetParameterString("out", outFile)
    BandMath.SetParameterString("exp", expr)
    BandMath.ExecuteAndWriteOutput()
    return outFile


def Main(datas, out, ShapeBretagne):
    """
    Fonction consistant a lister tous les fichiers MODIS se trouvant dans un
    dossier. Puis, trie par ordre chronologique ces fichiers, puis utilise
    ceux-ci pour :
    1/ effectuer un decoupage selon la zone d'etude et un reechantillonnage
    pour avoir la meme resolution spatiale entre les images.
    2/ calculer le NDVI
    3/ calculer Tj-Tn
    4/ calculer l'Evaporative Fractionf
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
        
            
        # Extrait la date au format anneejour pour faire une date ymd
        YDate = datetime.datetime.strptime(filenameTemp[9:16], "%Y%j")
        Date = datetime.datetime.strftime(YDate, "%Y%m%d")
    
        # Calcule le NDVI
        NDVI = CalcNDVI(ListFilesBands, out, filenameBand)
        
        # Calcule le FVC               
        FVC = CalcFVC(NDVI, out+"/"+filenameTemp+"_FVC.tif")   
        
        # Calcule Tj - Tn
        TjTn, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj, Tj, Tn \
            = CalcTjTn(ListFilesTemp, out+"/"+filenameTemp+"_TjTn.tif")
        
        # Supprime les valeurs de FVC ou la temperature n'est pas disponible
        FVC[np.where(TjTn==0)]=np.nan

        # Calcule les donnees necessaires pour calculer les droites de regression)
        (PtsInf, PtsSup), (PtsInfMean, PtsSupMean) = courbes_phi(FVC, TjTn)
        
        # Calcule les droites de regression et les donnees necessaire pour calculer EF
        TminHumide, SlopeSec, InterceptSec = Graph(25, 1, PtsInfMean, PtsSupMean, \
            PtsInf, PtsSup, out+"/"+filenameTemp+"_Phi_%s_%s.png" % (25, 1))
        
        # Calcul d'EF
        CalcEF(FVC, SlopeSec, InterceptSec, TjTn, Tj, Tn, TminHumide, out, \
            Date, Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj)

        
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