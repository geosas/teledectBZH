# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 18:11:32 2016

@author: Mounirsky
"""

import json
import yaml
import os
import requests
import datetime


class SearchDownloadLandsat8():
    '''
    Cette Classe comport les méthodes nécessaire pour la recherche, la création
    de base d'information JSON, le téléchargement des images landsat8 en utilisant
    comme information de base le (PATH, ROW) de chaque scenne.
    '''


    def __init__(self):
        """
        méthode init (constructeur)
        """

    def dict_to_json(self, dict_in, dir_out, json_name):
        """
        Celle méthode ecrit le résultat de la recherce (dict)
        sur un ficher base au format  json.
        Elle renvoit le chemain du fichier
        """
        json_file_dir = '%s/%s.json' % (dir_out, json_name)
        with open(json_file_dir, 'w') as f:
            json.dump(dict_in, f, indent=4, sort_keys=True)
        return json_file_dir



    def json_to_dict(self, json_file_dir):
        """
        Celle méthode permet de lire un ficjier json et renvoit un dict
        """
        with open(json_file_dir, 'r') as f:
            landsat_dict_base = yaml.load(f)
        return landsat_dict_base



    def get_L8_bands(self, pathRow, scene_id, band_list, out_dir):
        '''
        Cette méthode permet de télécharger une liste de bandes
        Landsat8 depuis la source https://s3-us-west-2.amazonaws.com
        En utilisant les arguments suivant:

         - path/Row (String), Exp : '202/026'
         - scene_id (String), Exp : 'LC82020262013189LGN00'
         - band_list (List), Exp : ['b4', 'b3', 'b2']
         - out_dir (String), Exp : '/tmp/tmp_images'

        La méthode retourne une liste de chemins, de la fiche de métadonnées et
        des différentes bandes téléchargées.
        '''
        start = datetime.datetime.now()
        output_list = []
        baseUrl = 'https://s3-us-west-2.amazonaws.com/landsat-pds/L8'

        separator = pathRow[3]
        if separator != '/':
            pathRow = pathRow.replace(separator, '/')

        scene_meta = scene_id + '_MTL.txt'
        meta_url = "%s/%s/%s/%s" % (baseUrl, pathRow, scene_id, scene_meta)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        output_meta = "%s/%s" % (out_dir, scene_meta)

        if not os.path.exists(output_meta):
            r = requests.get(url=meta_url)
            data = r.content
            with open(output_meta, 'wb') as f:
                f.write(data)

        for band in band_list:
            if band.upper() == 'MLT':
                scene_bande = '%s_%s.txt' % (scene_id, band.upper())
            else:
                scene_bande = '%s_%s.TIF' % (scene_id, band.upper())

            final_url = '%s/%s/%s/%s' % (baseUrl, pathRow, scene_id, scene_bande)
            #print(final_url)

            output_band = '%s/%s' % (out_dir, scene_bande)

            # ajouter les chemins des bandes à la liste "output_list"
            output_list.append(output_band)

            if not os.path.exists(output_band):
                print("\nDownloading : {0}".format(scene_bande))
                # Do the GET request
                r = requests.get(url=final_url)
                # Download data and wri
                data = r.content
                with open(output_band, 'wb') as f:
                    f.write(data)


            else:
                print("\n{0} exsists".format(output_band))
        # Calculat time
        delta = datetime.datetime.now() - start
        print "\nTotal download time : {0}\n".format(delta)
        return output_list


    def date_to_yearJulian(self, str_date, fmt):
        '''
        Cette methode permet de convertir une date (en spécifiant son format)
        a une année et jour Julien.
        Elle retourne un string de l'année et le jour Julien, Exp : 2017001
        '''
        dt = datetime.datetime.strptime(str_date, fmt)
        tt = dt.timetuple()
        yj = '%d%03d' % (tt.tm_year, tt.tm_yday)
        return yj


    def search_l8_AWS(self, path, row, date, format_date):
        '''
        Cette methode permet de chercher une scene sur la base AWS à partir
        de son path, row, date. Si la scene recherché existe, la méthode
        retournera un dict dont ont aura les information de celle-ci, si non
        elle retournera None.
        '''
        yj = self.date_to_yearJulian(date, format_date)

        year = str(datetime.datetime.strptime(date, format_date).year)

        scene_id = 'LC8%s%s%sLGN00' % (path, row, yj)

        aws_uri = 'https://s3-us-west-2.amazonaws.com/landsat-pds/L8'

        usgs_uri = 'https://earthexplorer.usgs.gov/browse/landsat_8'

        index_query = '%s/%s/%s/%s/index.html' % (aws_uri, path, row, scene_id)

        thumb_usgs = '%s/%s/%s/%s/%s.jpg' % (usgs_uri, year, path, row, scene_id)

        r = requests.get(index_query)

        print('Searching...')

        # Si la requete retourne un code 200 (OK)
        if r.ok:
            # Récolte des informations sur la métadonée de la scenne
            meat_query = '%s/%s/%s/%s/%s_MTL.txt' % (aws_uri, path, row, scene_id, scene_id)
            r_meta = requests.get(meat_query)
            meta_str = r_meta.content
            meta = meta_str.replace('\n','')
            index = meta.find('CLOUD_COVER')
            cloud_str = meta[index:index+19]
            cloud = cloud_str.replace(' ','')
            cloud_val = cloud.split('=')[1]
            formated_date = datetime.datetime.strptime(date, format_date).strftime('%d/%m/%Y')
            # Collecte des informations de la scenne à mettre en base JSON
            result = {'sceneID': scene_id,
                      'sat_type': 'L8',
                      'path': path,
                      'row': row,
                      'thumbnail': thumb_usgs,
                      'date': formated_date,
                      'cloud': cloud_val,
                      'url_aws': index_query}
            r_meta.close
        else:
            result = None
        return result


