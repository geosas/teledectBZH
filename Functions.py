# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 09:34:16 2017

@author: donatien
"""
import os
import sys
import gdal
import ogr


def RastOpen(raster, bande):
    """
    Open raster and return some information about it.
    
    in :
        name : raster name
    out :
        datas : numpy array from raster dataset
        xsize : xsize of raster dataset
        ysize : ysize of raster dataset
        projection : projection of raster dataset
        transform : coordinates and pixel size of raster dataset
    """    
    RasterDs = gdal.Open(raster, 0)
    RasterBand = RasterDs.GetRasterBand(bande)
    
    #property of raster
    Projection = RasterDs.GetProjectionRef()
    Transform = RasterDs.GetGeoTransform()
    Xsize = RasterDs.RasterXSize
    Ysize = RasterDs.RasterYSize
    
    #convert raster to an array
    Data = RasterBand.ReadAsArray()
    
    return Data, Xsize, Ysize, Projection, Transform, RasterBand
    
def RastSave(Name, Xsize, Ysize, Transform, Data, Projection, Encode):
    """
    Save an array to a raster.
    
    in :
        name : raster name
        xsize : xsize of raster to be created
        ysize : ysize of raster to be created
        transform : coordinates and pixel size of raster to be created
        data : data of raster to be created
        projection : projection of raster to be created
        encode : encode of raster (gdal.GDT_UInt32, gdal.GDT_Byte) 
    """
    Driver = gdal.GetDriverByName("GTiff")
    outRaster = Driver.Create(Name, Xsize, Ysize, 1, Encode)
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(Data)
    outRaster.SetProjection(Projection)
    outRaster.SetGeoTransform(Transform)

    del outRaster, outband