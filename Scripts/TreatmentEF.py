# -*- coding: utf-8 -*-
"""
Script pour calculer les indices (NDVI, EF, temperatures jour et nuit)
"""

import os
import sys
import numpy as np
import argparse
import glob
import gdal
import datetime
from scipy.stats import linregress
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
    projection = raster.GetProjectionRef()
    transform = raster.GetGeoTransform()
    xsize = raster.RasterXSize
    ysize = raster.RasterYSize
    
    # convert raster to an array
    datas = rasterBand.ReadAsArray()
    
    return datas, xsize, ysize, projection, transform
    

def SaveRaster(name, xsize, ysize, transform, datas, projection, encode):
    """
    Save an array to a raster.
    
    in :
        name : string
               raster name
        xsize : string
                xsize of raster to be created
        ysize : string
                ysize of raster to be created
        transform : string
                    coordinates and pixel size of raster to be created
        data : array
               data of raster to be created
        projection : string
                     projection of raster to be created
        encode : string
                 encode of raster (gdal.GDT_UInt32, gdal.GDT_Byte) 
    """
    driver = gdal.GetDriverByName("GTiff")
    outRaster = driver.Create(name, xsize, ysize, 1, encode)
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(datas)
    outRaster.SetProjection(projection)
    outRaster.SetGeoTransform(transform)

    del outRaster, outband
    return name
    

def cloudMask(raster, mask):
    """
    Fonction pour supprimer les nuages d'une image selon l'image qualite
    mis a disposition dans le produit MOD09Q1. Ne prendre que les valeurs <220
    Rq : Pour convertir les valeurs en bit :
    np.array(map(bin, data.flatten())).reshape(data.shape)
    
    in : 
        raster : string
                 chemin du raster avec les nuages a supprimer
        mask : string
               chemin du raster renseignant sur la qualite des mesures
    """
    # ouvre le raster sur lequel supprimer des nuages
    dataRaster, xsize, ysize, projection, transform = OpenRaster(raster, 1)
    # ouvre le raster de qualite pour generer le masque de nuage
    dataMask, xsize, ysize, projection, transform = OpenRaster(mask, 1)
    # genere et appliquer le masque
    rasterWithoutCloud = np.where(dataMask>220, np.nan, dataRaster)
    # ecrase l'ancien fichier
    rasterMask = SaveRaster(raster, xsize, ysize, transform, rasterWithoutCloud, \
        projection, gdal.GDT_Float32)
    
    
def DataMask(inRaster, out, filename, name, maskShp, clipShp):
    """
    Decoupe un raster avec un shapefile et masque des valeurs avec un
    shapefile.
    
    in : 
        inRaster : string
                   raster a traiter
        out : string 
              nom repertoire ou enregistrer les donnees
        filename : string
                   nom du produit modis utilise
        name : string
               nom de l'indice
        maskShp : string
                  shapefile utilise pour masquer des valeurs
        clipShp : string
                  shapefile pour decouper le raster
        
    out : 
        raster du produit en cours decoupee, avec des valeurs masquees.
    """
    clipfile = os.path.dirname(inRaster)+"/clip.tif"
    # decoupe le raster selon un shapefile
    command = "gdalwarp -cutline %s -crop_to_cutline %s %s" % (clipShp, inRaster, clipfile)
    os.system(command)
    # Initialise un raster vide
    data, xsize, ysize, projection, transform = OpenRaster(clipfile, 1)
    dataZero = data * 0
    rasterMask = SaveRaster("%s/%s_%s_raw2.tif" % (out, filename, name), xsize,\
                            ysize, transform, dataZero, projection, gdal.GDT_Byte)
    # Initialise a la valeur 1 l'emplacement du departement
    command = "gdal_rasterize -burn 1 %s %s"%(maskShp, "%s" % (rasterMask))
    os.system(command)
    # Conserve uniquement les valeurs se situant sur le departement
    dataMask, xsizeMask, ysizeMask, projectionMask, transformMask = OpenRaster(rasterMask, 1)
    dataDprtmnt = np.where(dataMask==0, 0, data)
    # Supprime les fichiers intermediaires
    os.remove(inRaster)
    os.remove(clipfile)
    os.remove(rasterMask)    
    
    return dataDprtmnt, xsize, ysize, projection, transform
    
    
def ExtractClip(fichier, out, dataType, clipShp, maskShp, date):
    """
    Exporte, reprojete, decoupe, reechantillonne, masque les produits MODIS au format hdf.
    
    in : 
        fichier : string
                  produit modis au format hdf
        out : string
              chemin ou enregistrer les fichiers exporte
        dataType : string
                   type de donnees pour savoir si l'on genere des bandes, 
                   des temperatures ou le masque de nuages
        clipShp : string
                  shapefile pour decouper le raster
        maskShp : string
                  shapefile pour supprimer des valeurs
        date : string
               date de l'image
        
    out : fichier tif decoupee, masquee
    """
    # Determine le nom des fichiers qui vont etre a generer
    filename = os.path.basename(fichier)[:-4]
    if dataType == "Bands":
        dataName = ["Red", "Nir"]
    elif dataType == "Temp":
        dataName = ["Day", "Night"]
    elif dataType == "State":
        dataName = ["State"]
    
    # pour chaque données    
    ListFilesNames = []
    for i, name in zip(range(len(dataName)), dataName):
        # si ce sont les bandes du rouge et pir 
        if dataType == "Bands":
            if not os.path.exists(out+"/"+name):
                os.mkdir(out+"/"+name)
            outTif = out+"/"+name    
            RastClip = "%s/%s_%s_raw.tif" % (outTif, filename, name)
            RastReproject = "%s/%s_%s_rproj.tif" % (outTif, filename, name)
            # Exporte au format tif le raster
            command = "gdal_translate -ot Float32 \
            HDF4_EOS:EOS_GRID:'%s':MOD_Grid_250m_Surface_Reflectance:sur_refl_b0%s \
            %s" % (fichier, int(i)+1, RastClip)
            os.system(command)
            # Reprojete le raster en EPSG:2154
            command = "gdalwarp -t_srs EPSG:2154 %s %s" % (RastClip, RastReproject)
            os.system(command)
            # Masque les valeurs inutiles et aberrantes
            data, xsize, ysize, projection, transform = DataMask(RastReproject,\
                outTif, filename, name, maskShp, clipShp)           
            # Applique le scale factor d'apres l'usgs
            dataScaled = data*0.0001
            outRaster = SaveRaster("%s/%s_%s_uncompressed.tif" % (outTif, name, date), xsize,\
                        ysize, transform, dataScaled, projection, gdal.GDT_Float32)
            # compresse le fichier produit
            command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s/%s_%s.tif"\
                        % (outRaster, outTif, name, date)
            os.system(command)
            
            os.remove(outRaster)            
            os.remove(RastClip)
            
            outRaster = "%s/%s_%s.tif" % (outTif, name, date)
        
        # si ce sont les bandes des temperatures
        elif dataType == "Temp":
            if not os.path.exists(out+"/"+name):
                os.mkdir(out+"/"+name)
            outTif = out+"/"+name
            RastClip = "%s/%s_%s_raw.tif" % (outTif, filename, name)
            RastReproject = "%s/%s_%s_rproj.tif" % (outTif, filename, name)
            
            # Decoupe le raster et le converti au format tif
            command = "gdal_translate -ot Float32 \
            HDF4_EOS:EOS_GRID:'%s':MODIS_Grid_8Day_1km_LST:LST_%s_1km \
            %s" % (fichier, name, RastClip)            
            os.system(command)
            # Reprojete le raster en EPSG:2154
            command = "gdalwarp -t_srs EPSG:2154 -r near -tr 243.134 -243.057 %s %s" % (RastClip, RastReproject)
            os.system(command)
            # Masque les valeurs inutiles et aberrantes
            data, xsize, ysize, projection, transform = DataMask(RastReproject,\
                outTif, filename, name, maskShp, clipShp)
            # Applique le scale factor
            dataScaled = data*0.02
            outRaster = SaveRaster("%s/%s_%s_%s.tif" % (outTif, filename, name, date), xsize,\
                        ysize, transform, dataScaled, projection, gdal.GDT_Float32)
            os.remove(RastClip)             
        
        # si c'est le produit qualite pour les nuages
        elif dataType == "State" :            
            if not os.path.exists(out+"/"+name):
                os.mkdir(out+"/"+name)
            outTif = out+"/"+name    
            RastClip = "%s/%s_%s_raw.tif" % (outTif, filename, name)
            RastReproject = "%s/%s_%s_rproj.tif" % (outTif, filename, name)
            #fichier qualite donnees pour generer masque nuage
            command = "gdal_translate -ot Int16 \
            HDF4_EOS:EOS_GRID:'%s':MOD_Grid_250m_Surface_Reflectance:sur_refl_state_250m \
            %s" % (fichier, RastClip)
            os.system(command)
            # Reprojete le raster en EPSG:2154
            command = "gdalwarp -t_srs EPSG:2154 %s %s" % (RastClip, RastReproject)
            os.system(command)
            # Masque les valeurs inutiles et aberrantes
            data, xsize, ysize, projection, transform = DataMask(RastReproject,\
                outTif, filename, name, maskShp, clipShp)
            # exporte et compresse le raster
            outRaster = SaveRaster("%s/%s_%s_uncompressed.tif" % (outTif, name, date), xsize,\
                        ysize, transform, data, projection, gdal.GDT_Int16)
            command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s/%s_%s.tif"\
                        % (outRaster, outTif, name, date)
            os.system(command)
            os.remove(outRaster)            
            os.remove(RastClip)
            
            outRaster = "%s/%s_%s.tif" % (outTif, name, date)
        
        # ajoute le nom du raster dans une liste permettant d'utiliser ces
        # fichiers pour calculer les indices
        ListFilesNames.append(outRaster)
    return ListFilesNames, filename
    

def CalcNDVI(ListFilesBands, out, filenameBand, date):
    """
    Calcule le NDVI 
    
    in : 
        ListFilesBands : list
                         liste contenant les bandes du rouge et pir
        out : string
              dossier ou enregistrer le fichier
        filenameBand : list
                       nom du produit modis correspondant aux bandes
        date : string
               date
    
    out : 
        - raster correspondant au NDVI a publier
        - retourne un array contenant uniquement des valeurs entre 0 et 1
            (necessaire pour calculer EF)
    """
    # ouvre les rasters
    red, xsize, ysize, projection, transform = OpenRaster(ListFilesBands[0], 1)
    nir, xsize, ysize, projection, transform = OpenRaster(ListFilesBands[1], 1)   
    # calcule le ndvi a enregister
    ndviTemp = ((nir-red)/(nir+red))
    # centre le ndvi entre -1 et 1 a cause de valeurs aberrantes
    ndviTemp2 = np.where(((ndviTemp<=-1) | (ndviTemp>1) | (np.isnan(ndviTemp))), -999, ndviTemp)   
    # calcule le ndvi a utiliser pour calculer EF
    ndvi = np.where(((ndviTemp<=0) | (ndviTemp>1)), 0, ndviTemp)       
    # enregistre en compresse le NDVI
    outRaster = SaveRaster(out+"/"+filenameBand+"_Ndvi.tif", xsize,\
                        ysize, transform, ndviTemp2, projection, gdal.GDT_Float32)
    command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s/NDVI_%s.tif"\
               % (outRaster, out, date)
    os.system(command)
    
    os.remove(outRaster)
    return ndvi, xsize, ysize, transform, projection
    
    
def CalcFVC(ndvi, xsize, ysize, transform, projection, out):
    """
    Calcule le Fractional Vegetation Cover (FVC).
    
    in : 
        ndvi : array
               variable contenant le ndvi
        xsize, ysize, transform, projection : information pour enregistrer le FVC
        out : string
              dossier ou enregistrer le fvc
    """
    # calcule le FVC en forçant le minimum a 0
    fvc = ((ndvi - 0)/(np.nanmax(ndvi)-0))**2
    # enregistre le fvc
    outRaster = SaveRaster(out+"_uncompressed.tif", xsize, ysize, transform, fvc, projection, gdal.GDT_Float32)
    command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s"\
               % (outRaster, out+".tif")
               
    os.system(command)
    os.remove(outRaster)
    return fvc


def CalcTjTn(ListFilesTemp, out, date):
    """
    Calcule Tj - Tn et, pour les pixels n'ayant aucune donnée sur une des
    images, supprime les même pixels sur l'autre. Cela évite d'avoir des
    temperatures aberrantes suite a la soustraction.
    
    in :
        ListFilesTemp : list
                        liste contenant les rasters temperatures
        out : string
              dossier ou enregistrer le raster
        date : string
               date
    """
    # Ouvre les raster de temperature de jour et de nuit
    Tj, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj = \
        OpenRaster(ListFilesTemp[0], 1)
    Tn, Xsize_Tn, Ysize_Tn, Projection_Tn, Transform_Tn = \
        OpenRaster(ListFilesTemp[1], 1) 

    # Identifie les cellules en nodata et supprime leur equivalent 
    # dans les deux images
    Tj[np.where(Tn==0)]=np.nan
    Tn[np.where(Tj==0)]=np.nan
	
    #converti tous les 0 en nodata
    Tj[np.where(Tj==0)]=np.nan
    Tn[np.where(Tn==0)]=np.nan

    if np.all(np.isnan(Tj)) or np.all(np.isnan(Tn)):
	print "Temperature sans donnees, EF incalculable"
	os.remove(ListFilesTemp[0])
	os.remove(ListFilesTemp[1])
	return False, False, False, False, False, False, False

    # Calcule Tj_Tn
    TjTn = Tj - Tn  
    # Enregistre l'image et la compresse
    outRaster = SaveRaster(out+"/TjTn/TjTn_uncompressed.tif", Xsize_Tj, Ysize_Tj, Transform_Tj, TjTn, \
                        Projection_Tj, gdal.GDT_Float32)
    command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s"\
               % (outRaster, out+"/TjTn/TjTn_"+date+".tif")
    os.system(command)  
    #modifie les valeurs nan en valeur aberrante pour nodata
    Tj[np.isnan(Tj)] = -999
    Tn[np.isnan(Tn)] = -999
    #supprime les temperatures non compressee
    os.remove(ListFilesTemp[0])
    os.remove(ListFilesTemp[1])
    #enregistre les images avec ces nouvelles valeurs
    outTj = SaveRaster("%s/Day.tif" % (out+"/Day"), Xsize_Tj,\
                        Ysize_Tj, Transform_Tj, Tj, Projection_Tj, gdal.GDT_Float32)
    outTn = SaveRaster("%s/Night.tif" % (out+"/Night"), Xsize_Tj,\
                        Ysize_Tj, Transform_Tj, Tn, Projection_Tj, gdal.GDT_Float32)
    #compresse les images                        
    command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s/Day_%s.tif"\
                        % (outTj, out+"/Day", date)
    os.system(command)   
    os.remove(outTj)           
    command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s/Night_%s.tif"\
                        % (outTn, out+"/Night", date)
    os.system(command)                    
    os.remove(outTn)
    
    os.remove(outRaster)

    return TjTn, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj, Tj, Tn


def courbes_phi(indice, temp, nb_interval=25, pourcentage=1):
    """Renvoie les points (et leur moyenne) composants les bords humide et sec.

    La valeur de phi est calculée par double interpolation en fonction du 
    nombre d'intevalles choisi et du pourcentage de point dans ces intervalles.
    La fonction renvoie, pour les bords humide et sec, les points ainsi que
    leur moyenne pour chaque intervalle.

    in :
        indice : numpy.array
                 indice de végétation choisi en abscisse
        temp : numpy.array
               température choisie en ordonnée
        nb_interval : int
                      nombre d'intervalle de découpage des données (10 par défaut)
        pourcentage : float
                      pourcentage de points utilisés dans la méthode exprimé en % (5 par défaut)
    out :
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
                  "- temp mini = %f - temp maxi = %f" % (np.nanmin(y), np.nanmax(y)))#(y[0], y[-1]))
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
            mean_inf = np.array([x_mid, np.nanmean(y_inf), i])
            mean_sup = np.array([x_mid, np.nanmean(y_sup), i])

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
    mini et maxi avec des droites de regressions pour calculer les bords
    humides et sec.
    
    in :
        nbInterval : string
                     nombre d'intervalles de valeurs a prendre en compte
        pourcentage : string
                      pourcentage de points a prendre aux extremes
        pts_inf_mean :  array
                        points moyens inferieurs
        pts_sup_mean :  array
                        points moyens superieurs
        pts_inf :  array
                   points inferieurs 
        pts_inf :  array
                   points superieurs 

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
    plot_reg_humide = ax.plot(x_reg, [y_min_hum, y_min_hum],'r-', lw=2, label="Droite du bord humide")
    
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
    
    ax.set_title("\nNombre d'intervalle = %d - Pourcentage = %s"  % (nbInterval, pourcentage), fontsize=16)
    ax.set_xlabel("FVC", fontsize=16)
    ax.set_ylabel("Tj - Tn", fontsize=16)
    plt.legend([pts, reg_moy, plot_reg_tot, plot_reg_humide], ["Points moyens","Regression des points moyens","Regression de l'ensemble des points","Droite du bord humide"])
    # Sauvegarde de la figure au format png
    plt.savefig(out, dpi=300)
    #plt.show()

    return y_min_hum, reg_s_tot[0], reg_s_tot[1]


def CalcEF(FVC, SlopeSec, InterceptSec, TjTn, Tj, Tn, TminHumide, out, \
    Date, Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj):
    """
    Calcul l'evaporative fraction
        
    in : 
        FVC : array
              array du FVC
        SlopeSec : string
                   valeur de la pente du bord sec
        InterceptSec : string
                       valeur du bord sec
        TjTn : array
               temperature tj-tn
        Tj : array
             temperature de jour
        Tn : array
             temperature de nuit
        TminHumide : string
                     temperature minimale du bord humide
        out : string
              dossier ou enregistrer ef
        Date : string
               date
        Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj : information pour
            produire le raster
    """
    Tmax = SlopeSec * FVC + InterceptSec
    Phi = ((Tmax - TjTn)/(Tmax - TminHumide)*1.26)
    print("Nombre de valeurs négative : %d" % (Phi < 0).sum())
    print("Nombre de valeurs > 1,26 : %d" % (Phi > 1.26).sum())
    tmoy = (Tj + Tn)/2
    ESatTa = 1000 * np.exp(52.57633 - (6790.4985 / tmoy) - 5.02808 * np.log(tmoy))
    delta = (ESatTa / tmoy) * ((6790.4985 / tmoy) - 5.02808)
    EF = (delta/(delta+66))*Phi
    EF[np.isnan(EF)] = -999
    # Enregistre l'image
    outRaster = SaveRaster(out+"/Temporaire.tif", Xsize_Tj, Ysize_Tj, \
                        Transform_Tj, EF, Projection_Tj, gdal.GDT_Float32)
    command = "gdal_translate -co 'TILED=YES' -co COMPRESS=DEFLATE %s %s/EF_%s.tif"\
               % (outRaster, out, Date)
    os.system(command)
    
    os.remove(outRaster)


def Main(datas, out, clipShp, maskShp):
    """
    Fonction consistant a lister tous les fichiers MODIS se trouvant dans un
    dossier. Puis, trie par ordre chronologique ces fichiers pour :
    1/ effectuer des pretraitements
    2/ calculer le NDVI
    3/ calculer Tj-Tn
    4/ calculer le FVC
    5/ calculer l'Evaporative Fraction
    """
    # Liste les fichiers reflectance et temperature
    ListFilesBands = glob.glob(datas+"/*%s*.hdf" % ("MOD09Q1"))
    ListFilesTemp = glob.glob(datas+"/*%s*.hdf" % ("MOD11A2"))
    ListFilesBands.sort()
    ListFilesTemp.sort()
    
    #pour chaque fichier
    for FilesBands, FilesTemp in zip(ListFilesBands, ListFilesTemp):
        
        # Teste si la date a deja ete traitee
        filename = os.path.basename(FilesBands)[:-4]
        
        # Extrait la date au format anneejour pour faire une date ymd
        YDate = datetime.datetime.strptime(filename[9:16], "%Y%j")
        Date = datetime.datetime.strftime(YDate, "%Y%m%d")
        
        if not os.path.exists(out+"/EF"):
            os.mkdir(out+"/EF")

        #if not os.path.exists(out+"/EF/EF_%s.tif" % (Date)):
        fichier = open(out+"/log_produits.txt", "r+")
        for ligne in fichier :
            if "EF_%s.tif" % (Date) in ligne :
                break
        else :
            # Extract au format tif et clip les bandes et temperatures
            ListFilesBands, filenameBand = ExtractClip(FilesBands, out, "Bands", clipShp, maskShp, Date)
            ListFilesTemp, filenameTemp = ExtractClip(FilesTemp, out, "Temp", clipShp, maskShp, Date)
            ListFilesCloud, filenameCloud = ExtractClip(FilesBands, out, "State", clipShp, maskShp, Date)
            
            # Supprime les nuages des bandes
            for bande in ListFilesBands :
                cloudMask(bande, ListFilesCloud[0])            
            for bande in ListFilesTemp :
                cloudMask(bande, ListFilesCloud[0])
                
            # Calcule le NDVI
            if not os.path.exists(out+"/NDVI"):
                os.mkdir(out+"/NDVI")
                
            ndvi, xsize, ysize, transform, projection = \
            CalcNDVI(ListFilesBands, out+"/NDVI", filenameBand, Date)
            
            # Calcule le FVC       
            if not os.path.exists(out+"/FVC"):
                os.mkdir(out+"/FVC")
                
            fvc = CalcFVC(ndvi, xsize, ysize, transform, projection, out+"/FVC/FVC_"+Date)   
            
            # Calcule Tj - Tn
            if not os.path.exists(out+"/TjTn"):
                os.mkdir(out+"/TjTn")
            TjTn, Xsize_Tj, Ysize_Tj, Projection_Tj, Transform_Tj, Tj, Tn \
                = CalcTjTn(ListFilesTemp, out, Date)
            
    	    # si une date ne contient aucune donnee de temperature, ne calcule pas EF
    	    try:
    	        if TjTn == False:
    		    print "Aucune temperature disponible a la date du %s" %(Date)
    	            continue
    	    except ValueError :
                # Supprime les valeurs de FVC ou la temperature n'est pas disponible
                fvc[np.where(TjTn==0)]=np.nan
        
                # Calcule les donnees necessaires pour calculer les droites de regression)
                # Initialise le pourcentage de points à prendre a 1 et l'incremente au besoin
                pourcentPoints = 1
                nbPoints = False
                
                #gere les erreurs si aucun point ne se situe dans l'intervalle choisi
                while nbPoints == False:
                    try :
                        (PtsInf, PtsSup), (PtsInfMean, PtsSupMean) = courbes_phi(fvc, TjTn, 25, pourcentPoints)
                        nbPoints = True
                    except UnboundLocalError :
                        pourcentPoints += 1       
            
            # Calcule les droites de regression et les donnees necessaire pour calculer EF
            if not os.path.exists(out+"/graphiques"):
                os.mkdir(out+"/graphiques")
            TminHumide, SlopeSec, InterceptSec = Graph(25, "%s" % (pourcentPoints), PtsInfMean, PtsSupMean, \
                PtsInf, PtsSup, out+"/graphiques/Phi_%s_%s_%s.png" % (25, "%s" % (pourcentPoints), Date))
            
            # Calcul d'EF
            CalcEF(fvc, SlopeSec, InterceptSec, TjTn, Tj, Tn, TminHumide, out+"/EF", \
                Date, Xsize_Tj, Ysize_Tj, Transform_Tj, Projection_Tj)

            fichier.write("EF_%s.tif\n" % (Date))
        fichier.close()
	#else :
	    #print "La date %s a deja ete traitee" % (Date)
    fichiers = glob.glob(datas+"/*")
    for fichier in fichiers :
        if os.path.basename(fichier) != "log_images.txt":
            os.remove(fichier)
        
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
        
        parser.add_argument("-clipshp", dest="clipShp", action="store", 
                            help="Shapefile de decoupage")

        parser.add_argument("-maskshp", dest="maskShp", action="store",
                            help="Shapefile de masquage")
                            
        args = parser.parse_args()
    np.seterr(divide='ignore', invalid='ignore')
    if not os.path.exists(args.out):
        os.mkdir(args.out)
    
    print("\nEtape 2 : traitement des images")
    
    if glob.glob(args.datas+"/*.hdf") == [] :
        print("Aucune image a traiter, arret")
        sys.exit()

    Main(args.datas, args.out, args.clipShp, args.maskShp)
