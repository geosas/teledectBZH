# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 15:06:35 2017

@author: Mounirsky
"""

import os
import calendar
import datetime
import requests
from grass_location_config import GrassLocationConfig
from search_download_landsat8 import SearchDownloadLandsat8


# Déclarer les variable d'environnement de Grass
GrassLocationConfig().set_all_envs()

from grass.script import core as gc


class ImageProcesses():
    '''
    Classe comporte les différents methodes de traitements d'images landsat8
    jusqu'a leur publication dans une mosaic temporelle sur geoserver.
    '''

    def __init__(self):
        '''
        Constructeur de la classe Grass_processes
        '''
        # instanciation de SearchDownloadLandsat8
        self.l8process = SearchDownloadLandsat8()

        # Création et initialisation du Mapset temporaire de Grass
        self.gl = GrassLocationConfig()
        self.gl.initEnv()
        self.Mapset = self.gl.grassMapset
        self.gl._windFile(self.Mapset)

        # variables globales de chaque méthode
        self.bands_names_list = []
        self.dos_names_list = []
        self.path_out_list = []

        # Method for pan sharpening. Options: brovey, ihs, pca
        self.pan_method = 'brovey'
        self.pansharp_composit = 'rgb_pan_brovey_grey255'

        return


    def colors_equalizer(self, bands_to_equalize):
        '''
        Cette méthode Grass permet de modifier /créer une table de couleur de
        la liste d'images (bandes) en entrée.
        '''

        bands = ','.join(bands_to_equalize)

        # r.colors - Creates/modifies the color table associated with a raster map.
        gc.run_command('r.colors',
                       quiet=True,
                       overwrite=True,
                       flags='e',
                       map=bands,
                       color='grey')
        return


    def RGB_pansharp_composit(self, bands_names_list):
        '''
        Cette méthode permet d'appliqué un pansharpning (affinier la résolution)
        et de créer une composition coloré (vrais couleurs)
        Elle prand en entrée un liste comprenant 4 bandes respectivement :
        Bleu, vert, rouge et panchromatique. La composition colorée en sortie
        et une image d'une bande avec une palette de couleur assosiée.
        '''

        band_blue = bands_names_list[0]
        band_green = bands_names_list[1]
        band_red = bands_names_list[2]
        band_pan = bands_names_list[3]


        gc.run_command('g.region', quiet=True, flags='d', raster=band_pan)

        for band in  [band_blue, band_green, band_red, band_pan]:

            # r.info get raster min,max pixels values
            min_max = gc.parse_command('r.info',
                                       map=band,
                                       flags='r')

            min_val = min_max['min'].encode('ascii','ignore')
            max_val = min_max['max'].encode('ascii','ignore')

            min_max_vals = "%s,%s" % (min_val, max_val)

            out_name = '255_%s' % (band)

            # r.rescale - Rescales the range of category values in a raster map layer.
            gc.Popen(["r.rescale",
                      "--o",
                      "input=%s" % (band),
                      "from=%s" % (min_max_vals),
                      "to=0,255",
                      "output=%s" % (out_name)
                      ])

        reclass_red = '255_%s' % (band_red)
        reclass_green = '255_%s' % (band_green)
        reclass_blue = '255_%s' % (band_blue)
        reclass_pan = '255_%s' % (band_pan)

        # i.pansharpen - Image fusion algorithms to sharpen multispectral with
        # high-res panchromatic channels
        basename = 'pan_%s' % (self.pan_method)
        gc.run_command('i.pansharpen',
                       quiet=True,
                       overwrite=True,
                       red=reclass_red,
                       green=reclass_green,
                       blue=reclass_blue,
                       pan=reclass_pan,
                       method=self.pan_method,
                       output=basename)

        pan_red = '%s_red' % (basename)
        pan_green = '%s_green' % (basename)
        pan_blue = '%s_blue' % (basename)

        self.colors_equalizer([pan_red, pan_green, pan_blue])

#        # i.colors.enhance - Performs auto-balancing of colors for RGB images. flags='p'
#        gc.run_command('i.colors.enhance',
#                       quiet=False,
#                       overwrite=True,
#                       red=pan_red,
#                       green=pan_green,
#                       blue=pan_blue)

        # r.composite - Combines red, green and blue raster maps into a single composite raster map.
        gc.run_command('r.composite',
                       quiet=False,
                       overwrite=True,
                       red=pan_red,
                       green=pan_green,
                       blue=pan_blue,
                       output=self.pansharp_composit)

        return



    def import_gdal(self, all_band_list, scene_id):
        '''
        Cette méthode permet d'importer une liste d'images (bandes) sur une
        instance Grass et de retourner une liste des noms interne des ces images.
        '''
        for i in range(len(all_band_list)):
            band_in = all_band_list[i]

            band_id = '{0}_B{1}'.format(scene_id, i+1)

            # r.in.gdal
            gc.run_command('r.in.gdal',
                           quiet=True,
                           overwrite=True,
                           flags='oke',
                           input=band_in,
                           output=band_id)
            if i == 0:
                # fit region to image
                gc.run_command('g.region', quiet=True, flags='d', raster=band_id)

            self.bands_names_list.append(band_id)
        return


    def landsat_dos(self, bands_names_list, scene_id, meta_data):
        '''
        i.landsat.toar - Calculates top-of-atmosphere radiance or reflectance
        and temperature for Landsat MSS/TM/ETM+/OLI
        Cette méthode permet d'importer une liste d'images (bandes) sur une
        instance Grass et de retourner une liste des noms interne des ces images.
        Remarque : "bands_names_list" doit comporté tout les bandes de 1 à 11.
        '''
        prefix_in = '{0}_B'.format(scene_id)
        prefix_out = 'Dos_{0}'.format(prefix_in)

        bands_8 = '{0}_B8'.format(scene_id)
        # fit region to image
        gc.run_command('g.region', quiet=True, flags='d', raster=bands_8)

        # i.landsat.toar - Calculates top-of-atmosphere radiance or reflectance
        # and temperature for Landsat MSS/TM/ETM+/OLI
        gc.run_command('i.landsat.toar',
                       quiet=True,
                       overwrite=True,
                       input=prefix_in,
                       output=prefix_out,
                       metfile=meta_data,
                       sensor='oli8',
                       method='dos4',
                       scale=100)

        for i in range(len(bands_names_list)):
            dos_out = '{0}{1}'.format(prefix_out, i+1)
            self.dos_names_list.append(dos_out)
        return


    def julian_date_to_date(self, scene_id):
        '''
        Cette méthode permet de convertir le nom d'une scene landsat8
        et date. Elle retourne un string de date au format yyyymmdd.
        '''
        jd = int(scene_id[13:-5])
        y = int(scene_id[9:-8])
        month = 1
        while jd - calendar.monthrange(y,month)[1] > 0 and month <= 12:
            jd = jd - calendar.monthrange(y,month)[1]
            month += 1
        date = datetime.date(y,month,jd).strftime("%Y%m%d")
        return date


    def pansharp_rgb_composit(self, scripts_dir, scene_id, data_dir, output_dir):
        '''
        Cette méthode permet de lancer un script shell afin de créer la
        composition coloré et appliqué un pansharpning à une image landsat8.
        Le script exécute que des commandes GDAL:
        - gdalbuildvrt
        - gdal_landsat_pansharp
        - gdal_translate
        '''

        scene_date = self.julian_date_to_date(scene_id)

        # méthode 1
        #rgb_app = '%s/landsat_rgb_pan_processing.sh' % (scripts_dir)

        # méthode 2
        rgb_app = '%s/landsat_vrt_rgb_pan.sh' % (scripts_dir)

        p = gc.Popen([rgb_app,
                      scene_id,
                      scene_date,
                      data_dir,
                      output_dir])

        p.communicate()

        RGB_out_name = "RGB_%s.TIF" % (scene_date)

        return RGB_out_name


    def generate_mosaic(self, workspace, login, password, url, nom_mosaic, titre, mosaic_dir, nom_image='', in_trans_color=''):
        '''
        Cette méthode permet de créer un workspace si il existe pas,
        de créer un entropot de mosaic temporelle. si l'entropot exist, la
        nouvelle image sera automatiquement ajoutée à la mosaic.

        '''
        workspace_url = "{0}/rest/workspaces/{1}".format(url, workspace)

        # Check if workspace exists
        headers = {'content-type': 'text/xml'}
        r = requests.get(workspace_url, headers=headers, auth=(login, password))


        if not r.ok:
            workspace_cmd = "curl -u {0}:{1} -XPOST -H 'content-type: text/xml' -d '<workspace><name>{2}</name></workspace>' {3}/rest/workspaces".format(login, password, workspace, url)
            gc.call(workspace_cmd, shell=True)
            print ("Creation du workspace: %s" % (workspace_cmd))
        else:
            print ("Le workspace: %s existe." % (workspace))

        mosaic_url = "{0}/rest/workspaces/{1}/coveragestores/{2}/coverage.xml".format(url,
                                                                                        workspace,
                                                                                        nom_mosaic)
        r = requests.get(mosaic_url, headers=headers, auth=(login, password))

        # Si la mosaic exist, mettre à jour l'entropot et lui ajouter la nouvelle image
        if r.ok:
            harvast_cmd = 'curl -u {0}:{1} -XPOST -H "Content-type: text/plain" -d "file://{2}/{3}.TIF" {4}/rest/workspaces/{5}/coveragestores/{6}/external.imagemosaic'.format(login, password, mosaic_dir, nom_image, url, workspace, nom_mosaic)

            print ("Ajout de l'image: %s" % (nom_image))
            gc.call(harvast_cmd, shell=True)

        else:
            # Création des fichiers '.properties' de la mosaic pour la gestion de "time"
            print("Création des fichiers 'properties' ...\n")
            with open("{0}/indexer.properties".format(mosaic_dir), "w") as f:
            	f.write("TimeAttribute=RGB_date \nCanBeEmpty=true \nSchema=*the_geom:Polygon,location:String,RGB_date:java.util.Date:Integer \nPropertyCollectors=TimestampFileNameExtractorSPI[timeregex](RGB_date)")


            with open("{0}/timeregex.properties".format(mosaic_dir), "w") as f:
            	f.write("regex=[0-9]{8}\n")

            coverage_xml = '''\
                            <coverage>\
                                <title>'''+ titre +'''</title>\
                                <metadata>\
                                    <entry key="time">\
                                        <dimensionInfo>\
                                            <enabled>true</enabled>\
                                            <presentation>LIST</presentation>\
                                            <units>ISO8601</units>\
                                            <defaultValue/>\
                                        </dimensionInfo>\
                                    </entry>\
                                </metadata>\
                                <parameters>\
                                    <entry>\
                                        <string>InputTransparentColor</string>\
                                        <string>''' + in_trans_color + '''</string>\
                                    </entry>\
                                </parameters>\
                            </coverage>'''
            # Enlever les doubles espaces
            coverage_xml = coverage_xml.replace("  ", "")

            # Creation de la mosaique
            mosaic_cmd = "curl -u {0}:{1} -v -XPUT -H 'Content-type: text/plain' -d 'file://{2}' {3}/rest/workspaces/{4}/coveragestores/{5}/external.imagemosaic?coverageName={5}&configure=all".format(login, password, mosaic_dir, url, workspace, nom_mosaic)

            print ("Creation de la mosaique : %s" % (mosaic_cmd))
            gc.call(mosaic_cmd, shell=True)

            # Modification des parameters de la mosaic
            parameters_cmd = "curl -u {0}:{1} -v -XPUT -H 'Content-type: application/xml' -d '{2}' {3}/rest/workspaces/{4}/coveragestores/{5}/coverages/{5}.xml".format(login, password, coverage_xml, url, workspace, nom_mosaic)

            print("Modification des parameters  : %s" % (parameters_cmd))
            gc.call(parameters_cmd, shell=True)

        return


    def export_rgb_gdal(self, rgb_name_out, dir_out):
        '''
        Cette méthode permet d'exporter en GeoTIF l'image RGB créé par l'instance
        Grass avec une projection "EPSG:32630", de créer des overviews à cette
        image et de suprimer les fichier temporaires.
        '''
        grass_rgb = self.pansharp_composit
        path_out_tmp = '%s/%s.TIF' % (self.gl.tempPath, grass_rgb)

        # r.out.gdal
        gc.run_command('r.out.gdal',
                       quiet=False,
                       overwrite=True,
                       flags='f',
                       input=grass_rgb,
                       output=path_out_tmp)

        path_out = '%s/%s.TIF' % (dir_out, rgb_name_out)

        # Compresser et définir la projection du rgb "EPSG:32630"
        p = gc.Popen(["gdal_translate",
                      "-co",
                      "COMPRESS=DEFLATE",
                      "-a_srs",
                      "EPSG:32630",
                      path_out_tmp,
                      path_out])

        print("Compress and projection processing...")
        p.communicate()

        # remove temporar outputs
        os.remove(path_out_tmp)

        # Créer les overviews du rgb
        p = gc.Popen(["gdaladdo",
                      "--config",
                      "COMPRESS_OVERVIEW",
                      "DEFLATE",
                      path_out,
                      "2",
                      "4",
                      "8",
                      "16"])

        print("Overview processing...")
        p.communicate()

        aux_file = "%s.aux.xml" % (path_out)
        # remove aux.xml file si non l'upload sur geoserver bug
        if os.path.exists(aux_file):
            os.remove(aux_file)

        return path_out


    def export_gdal(self, names_out_list, dir_out):
        '''
        Cette méthode permet d'exporter une liste d'images (bandes) depuis
        l'instance Grass et de retourner une liste de chemins vers ces images.
        '''

        for file_out in names_out_list:
            path_out_tmp = '%s/%s.TIF' % (self.gl.tempPath, file_out)

            # r.out.gdal
            gc.run_command('r.out.gdal',
                           quiet=False,
                           overwrite=True,
                           flags='f',
                           input=file_out,
                           output=path_out_tmp)

            path_out = '%s/%s.TIF' % (dir_out, file_out)
            # Compresser et définir la projection du rgb "EPSG:32630"
            p = gc.Popen(["gdal_translate",
                          "-co",
                          "COMPRESS=DEFLATE",
                          "-a_srs",
                          "EPSG:32630",
                          path_out_tmp,
                          path_out])

            print("Compress and projection processing...")
            p.communicate()

            # remove temporar outputs
            os.remove(path_out_tmp)

            self.path_out_list.append(path_out)
        return
