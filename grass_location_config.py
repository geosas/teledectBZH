# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 15:06:35 2017

@author: Mounirsky inspired from PyWPS Grass module
"""
import os
import tempfile
import sys
import json
import yaml
from shutil import rmtree as RMTREE

TEMPDIRPREFIX="grass-instance"

current_dir = os.path.dirname(os.path.realpath(__file__))

class GrassLocationConfig():
    """ GRASS initialization interface """

    locationDir = ""
    locationName = ""
    mapsetDir = ""
    mapsetName = ""
    gisbase = ""
    grassMapset = ""

    def  __init__(self):
        """ Initialization of GRASS environmental variables (except GISRC).  """

        self.location= None
        self.workingDir = ""
        self.dirsToBeRemoved = []
        self.dirsToBeRemoved_wd = []
        self.gisdbase = os.path.split(os.path.abspath(os.path.curdir))[0]
        self.grassMapset = ""

        # Point to the folder where config.json is
        os.chdir(current_dir)
        self.config_path = '%s/config.json' % (current_dir)

        # Load config file
        read_config = open(self.config_path).read()
        conf = json.dumps(json.loads(read_config))
        self.config = yaml.load(conf)

        # Set grass environement variables and tempPath from the config.json
        self.envs = self.config["grass_config_envs"]
        self.tempPath =  self.config["tempPath"]

        return


    def set_all_envs(self):
        # put env
        for key, val in self.envs.iteritems():
            self.setEnv(key, val)
            print("GRASS environment variable %s set to %s" % (key, val))

        # GIS_LOCK
        self.setEnv('GIS_LOCK', str(os.getpid()))
        print("GRASS GIS_LOCK set to %s" % str(os.getpid()))
        return


    def mkMapset(self, location):
        """
        Create GRASS mapset in current directory. Mapsets name is 'mapset'.
        At the end, GRASS will believe, it has run correctly.

        Returns name of new created mapset. location!=None, this mapset
        should be deleted!

        Arguments:
            location     -  Should the new mapset be created in the some old
                            location, which is already on this server?
                            Default: only mapset within
                            /tmp/grasstmpSOMEHTIN/
                            will be created
        """

        if self.location == None:
            self.locationDir = self.workingDir

            self.mapsetDir = tempfile.mkdtemp(prefix="pywps",dir=self.locationDir)
            self.mapsetName = os.path.split(self.mapsetDir)[1]
            self.locationName = os.path.split(self.locationDir)[1]

            # create new WIND file
            self._windFile(self.mapsetName)

            # create mapset PERMANENT
            os.mkdir("PERMANENT")
            self._windFile("PERMANENT")

            self.gisdbase = os.path.split(os.path.abspath(os.path.curdir))[0]


        # GRASS creates a temp dir for the display driver.
        # Add it to dirsToBeRemoved
        try:
            grassTmpDir = os.path.join(tempfile.gettempdir(),
                                       "grass70"+\
                                       "-"+os.getenv("USERNAME")+\
                                       "-"+str(os.getpid()))
            self.dirsToBeRemoved.append(grassTmpDir)
        except :
            pass

        self.setEnv('MAPSET', self.mapsetName)
        self.setEnv('LOCATION_NAME',self.locationName)
        self.setEnv('GISDBASE', self.gisdbase)

        # gisrc
        gisrc = open(os.path.join(self.workingDir,"grassrc"),"w")
        gisrc.write("LOCATION_NAME: %s\n" % self.locationName)
        gisrc.write("MAPSET: %s\n" % self.mapsetName)
        gisrc.write("DIGITIZER: none\n")
        gisrc.write("GISDBASE: %s\n" % self.gisdbase)
        gisrc.write("OVERWRITE: 1\n")
        gisrc.write("GRASS_GUI: text\n")
        gisrc.close()

        print("GRASS MAPSET set to %s" % self.mapsetName)
        print("GRASS LOCATION_NAME set to %s" % self.locationName)
        print("GRASS GISDBASE set to %s" % self.gisdbase)

        self.setEnv("GISRC",os.path.join(self.workingDir,"grassrc"))
        print("GRASS GISRC set to %s" % os.path.join(self.workingDir,"grassrc"))

        return self.mapsetName

    def _windFile(self,mapset):
        """ Create default WIND file """

        if mapset == "PERMANENT":
            windname = "DEFAULT_WIND"
        else:
            windname = "WIND"

        wind =open(
                os.path.join(
                    os.path.abspath(self.workingDir),mapset,windname),"w")
        wind.write("""proj:       0\n""")
        wind.write("""zone:       0\n""")
        wind.write("""north:      1000\n""")
        wind.write("""south:      0\n""")
        wind.write("""east:       1000\n""")
        wind.write("""west:       0\n""")
        wind.write("""cols:       1000\n""")
        wind.write("""rows:       1000\n""")
        wind.write("""e-w resol:  1\n""")
        wind.write("""n-s resol:  1\n""")
        wind.close()

        return

    def setEnv(self, key, value):
        """Set GRASS environmental variables """
        os.putenv(key, value)
        os.environ[key] = value

        if key == 'GISBASE':
            sys.path.append(os.path.join(value, 'etc', 'python'))


    def initEnv(self):
        """Create process working directory, initialize GRASS environment,
        if required.

        """

        # find out number of running sessions
        tempPath = self.tempPath

        dirs = os.listdir(tempPath)
        pyWPSDirs = 0
        for dir in dirs:
            if dir.find(TEMPDIRPREFIX) == 0:
                pyWPSDirs += 1


        # create temp dir
        self.workingDir = tempfile.mkdtemp(prefix=TEMPDIRPREFIX, dir=tempPath)

        self.workingDir = os.path.join(self.tempPath, self.workingDir)

        os.chdir(self.workingDir)
        self.dirsToBeRemoved_wd.append(self.workingDir)

        # init GRASS
        try:
            self.grassMapset = self.mkMapset(self.location)

        except Exception,e:
            self.cleanEnv()
            print("Could not init GRASS: %s" % e)
        return

    def cleanEnv(self):
        """ Removes temporary created files and dictionaries
        """
        os.chdir(self.gisdbase)
        def onError(*args):
            print("Could not remove temporary dir")

        for i in range(len(self.dirsToBeRemoved_wd)):
            dir = self.dirsToBeRemoved_wd[0]
            if os.path.isdir(dir) and dir != "/":
                RMTREE(dir, onerror=onError)
                pass
            self.dirsToBeRemoved_wd.remove(dir)
        return

