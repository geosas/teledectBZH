#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 18:11:32 2016

@author: Mounirsky
"""

import os
import argparse
import datetime
from shutil import rmtree as RMTREE
from search_download_landsat8 import  SearchDownloadLandsat8
from image_processes import ImageProcesses

parser = argparse.ArgumentParser(
    description="main_job.py -d <day> -m <month> -y <year>",
    prog='./main_job.py')

requiredNamed = parser.add_argument_group('Inputs arguments')


requiredNamed.add_argument(
    '-d',
    default=1,
    metavar='DAY',
    type=int,
    required=False,
    help='Start day')
requiredNamed.add_argument(
    '-m',
    default=11,
    metavar='MONTH',
    type=int,
    required=False,
    help='Start month')
requiredNamed.add_argument(
    '-y',
    default=2013,
    metavar='YEAR',
    type=int,
    required=False,
    help='Start year')

args = vars(parser.parse_args())

day = args['d']
month = args['m']
year = args['y']



class Main():

    def __init__(self):

        #==============================================================================
        # init ShearchDownloadLandsat8
        #==============================================================================
        self.l8proc = SearchDownloadLandsat8()

        #==============================================================================
        # Instantiation de la classe ImageProcesses
        #==============================================================================
        self.ip = ImageProcesses()

        # recupérer le contenu du fichier config.json
        config = self.ip.gl.config

        # recupérer les valeurs du fichier config.json
        self.processing_path = config["processing_path"]
        self.database_path = config["database_path"]
        self.output_images = '%s/images_out' % (self.processing_path)

        self.geoserver_data_dir = config["geoserver_info"]["geoserver_data_dir"]
        self.url_geoserver = config["geoserver_info"]["url_geoserver"]
        self.workspace_geoserver = config["geoserver_info"]["workspace"]
        self.login_geoserver =  config["geoserver_info"]["login"]
        self.password_geoserver = config["geoserver_info"]["password"]

        # récupérer le chemin des scripts (current dir)
        self.scripts_dir = os.path.dirname(os.path.realpath(__file__))

        # creation du repertoir de base de données des scennes si il existe pas
        if not os.path.exists(self.database_path):
            os.mkdir(self.database_path)

        # declaration des path, row des scennes à tréter (cas de Bretagne)
        self.pathRow_database = {'202_026' : self.database_path + '/landsat_base_202_026.json',
                                '202_027' : self.database_path + '/landsat_base_202_027.json',
                                '203_026' : self.database_path + '/landsat_base_203_026.json',
                                '203_027' : self.database_path + '/landsat_base_203_027.json'}
        return


    def make_RGB_work(self, pathRow, scene_id, short_date, format_date):
        '''
        Cette méthode permet de lancer les méthodes de traitement souhaitées
        pour la création et la publication de la mosaique temporelle de
        composition colorées.
        '''
##==============================================================================
#        # Dans le cas du calcule du DOS, où on veut utiliser tout le bande et la métadonnée et la .BQA
#        bands = ['MTL', 'BQA', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10', 'b11' ]
#
#        # Récupération des chemins vers le fichier de métadoné et sa suppréssion de la liste
#        meta_data = output_list.pop(0)
#
#        # Récupération des chemins vers l'image BQA (nuages) et sa suppréssion de la liste
#        cloud_BQA = output_list.pop(0)
#
#        #==============================================================================
#        # Correction atmosphérique DOS
#        #==============================================================================
#        # i.landsat.toar
#        ip.landsat_dos(bands_names_list=bands_names_list, scene_id=scene_id, meta_data=meta_data)
#
#        # Récupérer la list des noms de bandes corrigées
#        dos_names_list = gp.dos_names_list
##==============================================================================

        # liste des bandes pour la composition colorée et le pansharpning
        bands = ['b2', 'b3', 'b4', 'b8']

        images_out_dir = "%s/%s" % (self.output_images, pathRow)

        # Créer le repertoir si il existe pas
        if not os.path.exists(images_out_dir):
            os.makedirs(images_out_dir)

        # download bands
        output_list = self.l8proc.get_L8_bands(pathRow = pathRow,
                                              scene_id = scene_id,
                                              band_list = bands,
                                              out_dir = images_out_dir)

        #==============================================================================
        # Importing bands into grass
        #==============================================================================
        # r.in.gdal
        self.ip.import_gdal(all_band_list = output_list, scene_id = scene_id)

        bands_names_list = self.ip.bands_names_list

        #==============================================================================
        # Composition colorée
        #==============================================================================

        self.ip.RGB_pansharp_composit(bands_names_list)

        #==============================================================================
        # Création de la composition colorée pansharpnée avec Grass
        #==============================================================================
        geoserver_images_out = '%s/RGB_Mosaic_%s' % (self.geoserver_data_dir, pathRow)

        if not os.path.exists(geoserver_images_out):
            os.makedirs(geoserver_images_out)

        # Exporting
        rgb_name = 'RGB_%s' % (short_date)

        self.ip.export_rgb_gdal(rgb_name_out=rgb_name,
                           dir_out=geoserver_images_out)

        # Autre méthode de pour la création de la composition colorée pansharpnée avec GDAL
        #rgb_name = self.ip.pansharp_rgb_composit(scripts_dir, scene_id, images_out_dir, geoserver_images_out)

        #==============================================================================
        # Création et publication de la mosaic RBG sur geoserver
        #==============================================================================
        nom_mosaic = "RGB_%s" % (pathRow)
        titre_mosaic = "Landsat-8 RGB %s" % (pathRow)


        self.ip.generate_mosaic(workspace = self.workspace_geoserver,
                               login = self.login_geoserver,
                               password = self.password_geoserver,
                               url = self.url_geoserver,
                               nom_mosaic = nom_mosaic,
                               titre = titre_mosaic,
                               mosaic_dir = geoserver_images_out,
                               nom_image = rgb_name,
                               in_trans_color = '#000000')

        #==============================================================================
        # Nettoyage des fichiers et repertoire intermédiaires
        #==============================================================================
        # Suprimer le répertoir temporel de l'instance grass
        self.ip.gl.cleanEnv()
        # Remove the folder where all downloaded files are
        RMTREE(images_out_dir)

        # initialiser pour créer une nouvelle instance grass (répertoir Mapset)
        self.__init__()

        return


    def capsulate_base(self, all_scenes_result):
        '''
        Methode permetant de mettre à jour ces informations sur la base json:
        - le nombre total des scennes et
        - la date de la dernière scenne trétée.
        '''
        total_base = {}
        total = '{0}'.format(len(all_scenes_result))
        total_base['total'] = total
        total_base['scenes'] = all_scenes_result

        last_scene = sorted(total_base['scenes'].keys())[-1]
        total_base['last_scene'] = last_scene
        return total_base


    def main_job(self, year, month, day):
        '''
        Creation ou mise à jour des 4 bases des 4 scenes de bretagne et lencement
        du traitement "make_RGB_work" pour chaque date en commancant par "startdate"
        jusqu'à aujourd'hui. par défaut ça commance avec la première date du lancement
        du satellit landsat 8.
        '''
        # déclaration de la date de commencement
        print("Starting date is : %d/%d/%d" % (day, month, year))
        startdate = datetime.date(int(year), int(month), int(day))

        today = datetime.date.today()

        delta = today - startdate

        for pathRow, base_file in self.pathRow_database.iteritems():

            path = pathRow.split('_')[0]
            row = pathRow.split('_')[1]
            all_result = {}

            # Pour créer rapidement les 4 bases (prendre en cempte l'interval de 16 jours)
            if not os.path.exists(base_file):
                total_days = delta.days + 1
                for i in range(total_days):
                    dt = startdate + datetime.timedelta(days = i)
                    date = dt.strftime('%d/%m/%Y')
                    date_short = dt.strftime('%Y%m%d')
                    result = self.l8proc.search_l8_AWS(path, row, date, '%d/%m/%Y')
                    if result:
                        all_result['scenes'] = {}
                        for x in range(i, total_days, 16):
                            dt = startdate + datetime.timedelta(days = x)
                            date = dt.strftime('%d/%m/%Y')
                            date_short = dt.strftime('%Y%m%d')
                            print(date)
                            result = self.l8proc.search_l8_AWS(path, row, date, '%d/%m/%Y')
                            all_result['scenes'][date_short] = result
                            scene_id = result['sceneID']
                            # make main job
                            self.make_RGB_work(pathRow=pathRow,
                                          scene_id=scene_id,
                                          short_date=date_short,
                                          format_date='%Y%m%d')

                        total_base = self.capsulate_base(all_result['scenes'])
                        base_name = 'landsat_base_%s' % (pathRow)
                        self.l8proc.dict_to_json(total_base, dir_out = self.database_path, json_name = base_name)
                        break
            else:
                all_result = self.l8proc.json_to_dict(base_file)
                last_date = all_result['last_scene']
                last_datetime = datetime.datetime.strptime(last_date, '%Y%m%d').date()
                small_delta = today - last_datetime

                for i in range(small_delta.days + 1):
                    dt = last_datetime + datetime.timedelta(days = i+1)
                    date = dt.strftime('%d/%m/%Y')
                    date_short = dt.strftime('%Y%m%d')
                    result = self.l8proc.search_l8_AWS(path, row, date, '%d/%m/%Y')
                    if result:
                        all_result['scenes'][date_short] = result
                        scene_id = result['sceneID']

                        # make main job
                        self.make_RGB_work(pathRow = pathRow,
                                      scene_id = scene_id,
                                      short_date = date_short,
                                      format_date = '%Y%m%d')
                        break
                    else:
                        print("No result on : %s for The PathRow %s" % (date, pathRow))

                total_base = self.capsulate_base(all_result['scenes'])
                base_name = 'landsat_base_%s' % (pathRow)
                self.l8proc.dict_to_json(total_base, dir_out = self.database_path, json_name = base_name)



#==============================================================================
# Execute main job
#==============================================================================
if __name__ == '__main__':
    # créer l'instance de la class Main
    main_class = Main()
    # Lencer la méthode main_job
    try:
        main_class.main_job(year=year, month=month, day=day)
    except:
        pass
    # Suprimer le répertoir temporel de l'instance grass
    main_class.ip.gl.cleanEnv()

