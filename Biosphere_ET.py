
# coding: utf-8

# In[22]:


# Réinitialise le notebook
get_ipython().magic('reset -f')


# In[23]:


from __future__ import division, print_function, unicode_literals
import os
import numpy as np
from scipy.stats import linregress
import matplotlib.pyplot as plt
import gdal
from glob import glob
import rasterio
get_ipython().magic('matplotlib inline')


# In[24]:


# On n'affiche aucun avertissement pour les erreurs lors de division.
np.seterr(all="ignore");


# # Définition des données en entrée

# In[25]:


# Source des images en entrées : L8 (Landsat 8) ou S2 (Sentinel 2)
source = "L8"

# Choix du groupe : Gr1, Gr2, Gr3, Gr4, Tot (image entière)
groupe = "Tot"

# Extrait
extrait = 2


# # Images

# In[26]:


if groupe == "Tot":
    # Images Landsat 8
    path_zone_l8 = "../Bretagne/DONNEES_BRUTES/Landsat8/Dos_zone"
    l8 = {"red": os.path.join(path_zone_l8, "l8_zone_B4.TIF"),
          "nir": os.path.join(path_zone_l8, "l8_zone_B5.TIF"),
          "swir2": os.path.join(path_zone_l8, "l8_zone_B7.TIF")}
    l8_th = os.path.join(path_zone_l8, "l8_zone_B11.TIF")
    # Images Sentinel 2
    path_zone_s2 = "../Bretagne/DONNEES_BRUTES/Sentinel2/Dos/"
    s2 = {"red": os.path.join(path_zone_s2, "S2_B04.tif"),
          "nir": os.path.join(path_zone_s2, "S2_B08.tif"),
          "swir2": os.path.join(path_zone_s2, "S2_B12.tif")}
    # Chemins par défaut
    path_indice = "../Bretagne/ANALYSES/Tot/Indices/%s" % source
    path_tiff = "../Bretagne/ANALYSES/Tot/Indices/%s/tiff" % source
else:
    # Images Landsat 8
    path_zone = "../Bretagne/ANALYSES/%s/Extraits%d" % (groupe, extrait)
    l8 = {"red": os.path.join(path_zone, "l8_zone_B4.TIF"),
          "nir": os.path.join(path_zone, "l8_zone_B5.TIF"),
          "swir2": os.path.join(path_zone, "l8_zone_B7.TIF")}
    l8_th = os.path.join(path_zone, "l8_zone_B11.TIF")
    # Images Sentinel 2
    s2 = {"red": os.path.join(path_zone, "S2_B04.tif"),
          "nir": os.path.join(path_zone, "S2_B08.tif"),
          "swir2": os.path.join(path_zone, "S2_B12.tif")}
    # Chemins par défaut
    path_indice = "../Bretagne/ANALYSES/%s/Indices/%s/Extraits%d" % (groupe, source, extrait)
    path_tiff = "../Bretagne/ANALYSES/%s/Indices/%s/Extraits%d/tiff" % (groupe, source, extrait)

if source == "L8":
    images = l8
elif source == "S2":
    images = s2
else:
    images = None


# # Données météo

# In[29]:


if groupe == "Tot":
    path_zone = "../Bretagne/DONNEES_BRUTES/Meteo_France/"
# Température atmosphérique en Kelvin
meteo_t_11 = os.path.join(path_zone, "T2M_16072016_11h.tif")
meteo_t_12 = os.path.join(path_zone, "T2M_16072016_12h.tif")

# Humidités relatives
meteo_h_11 = os.path.join(path_zone, "U2m_16072016_11h.tif")
meteo_h_12 = os.path.join(path_zone, "U2m_16072016_12h.tif")

# Rayonemment global
meteo_rg_11 = os.path.join(path_zone, "Fluxsolaire_16072016_11h.tif")
meteo_rg_12 = os.path.join(path_zone, "Fluxsolaire_16072016_12h.tif")


# # Fonctions

# ### Récupération d'une bande du jeu de données brutes

# In[41]:


def get_band(band):
    """Exporte les données d'une image au format np.array

    Arguments
    ---------
    band : string
           chemin vers l'image
    Returns
    -------
    tuple : numpy.array
            Renvoie l'image au format np.array
    """
    if os.path.exists(band):
        with rasterio.open(band, "r") as src:
            print(src.meta)
            return src.read(1)
    else:
        print("L'image spécifiée (%s) n'existe pas." % band)


# ### Récupération d'un indice calculé

# In[31]:


def get_indice(indice, chemin=path_indice):
    """Exporte les données d'une image au format np.array

    Arguments
    ---------
    indice : string
             nom de l'image avec l'extension (ex : "ndvi.tif")
    path   : string
             chemin du dossier contenant les images des indices
    Returns
    -------
    tuple : numpy.array
            Renvoie l'image de l'indice au format np.array
    """
    fichier = os.path.join(chemin, indice)
    if os.path.exists(fichier):
        with rasterio.open(fichier, "r") as src:
            return src.read(1)
    else:
        print("L'image spécifiée (%s) n'existe pas." % fichier)


# ### Récupération des métadonnées des bandes du jeu de données brutes

# In[32]:


def get_meta(band=None):
    """Exporte les métadonnées d'une image.

    Toutes les bandes d'une scène ont les même caractéristiques (métadonnées).
    
    Arguments
    ---------
    band : string
           chemin vers l'image.
           Si aucune image n'est donnée, on utilise la bande rouge du jeu de données.
    Returns
    -------
    dictionnaire
        Renvoie un dictionnaire des métadonnées au format Rasterio.
    """
    if band is None:
        band = images["red"]
    with rasterio.open(s2["red"], "r") as src:
        return src.meta


# ### Création d'un tif avec des données calculées

# In[33]:


def create_tif(array_image, nom, dossier_out=path_tiff):
    """Sauvegarde un numpy.array au format tif.

    Arguments
    ---------
    array_image : numpy.array
                  array représentant l'image
    nom : string
          nom de l'image sans l'extension
    dossier : string
              chemin du dossier de sortie
    """
    # Récuparation des métadonnées si ça n'a pas encore été fait.
    if "meta" not in locals():
        meta = get_meta()
    # Si le dossier d'export n'exite pas, on le crée.
    if not os.path.isdir(dossier_out):
        os.makedirs(dossier_out)
        print("Le dossier de sortie des images (%s) a été créé." % dossier_out)
    with rasterio.open(os.path.join(dossier_out, "%s.tif" % nom), "w", **meta) as dst:
        dst.write(array_image.astype(meta["dtype"]), 1)


# ### Histogramme

# In[34]:


def hist_nan(array, bins=50):
    """Affiche l'histogramme d'un numpy.array"""
    plt.hist(array[np.logical_not(np.isnan(array))], bins=bins)
    plt.show()


# ### Calcul des points des bords humide et sec

# In[35]:


def courbes_phi(indice, temp, nb_interval=25, pourcentage=1):
    """Renvoie les points (et leur moyenne) composants les bords humide et sec.

    La valeur de phi est calculée par double interpolation
    en fonction du nombre d'intevalles choisi et du pourcentage de point dans ces intervalles.
    La fonction renvoie, pour les bords humide et sec, les points ainsi que leur moyenne pour chaque intervalle.

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
            print("Intervale %d : nombre de points = %d" % (i, x.size),
                  "- temp mini = %f - temp maxi = %f" % (y[0], y[-1]))
        else:
            print("Il n'y a pas de points dans l'intervale ",  i)

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


# ### Calcul de la pression de vapeur saturante à la température t, esat(t)

# In[36]:


def get_e_sat(t):
    """Renvoie la pression de vapeur saturante à la température t"""
    return 1000 * np.exp(52.57633 - (6790.4985 / t) - 5.02808 * np.log(t))


# ### Calcul des statisques pour une image

# In[37]:


def get_stats(array):
    """Renvoie les valeurs mini, maxi et moyenne d'un numpy array"""
    print("min : %.3f - max : %.3f - mean : %.3f" % (np.nanmin(array), np.nanmax(array), np.nanmean(array)))


# # 1 - Calcul du rayonnement atmosphérique, $ R_{a} $

# $ R_{a} = \epsilon_{ATM}\sigma Ta^{4} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ \epsilon_{ATM} $ : émissivité de l'atmosphère  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ \sigma = 5,67.10^{-8} (W.m^{-2}.K^{-4}) $ : constante de Stefan/Boltzman  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ T_{a} $: température de l'atmosphère

# ## 1a - Calcul de l'émissivité de l'atmosphère, $ \epsilon_{ATM} $
# $ \varepsilon_{ATM} = 1,24\left( \frac{e_{a}}{100.T_{a}} \right)^{\frac{ 1}{ 7}} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ e_{a} $ (Pa) : pression partielle de vapeur d'eau dans l'air  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Ta : température de l'atmosphère  
# $ e_{a} = \frac{  e_{sat}  H_{R}}{ 100} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ H_{R} $ (%) : humidité relative  de l'air  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ e_{sat}(T_{a}) $ : pression de vapeur saturante à la température atmosphérique   
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ e_{sat}(T_{a}) = 1000e^{52,57633 - \frac{6790,4985}{T} - 5,02808ln(T)} $

# In[15]:


m_t_11 = get_band(meteo_t_11)
m_t_12 = get_band(meteo_t_12)
temp_atmo = (m_t_11 + m_t_12) / 2
m_h_11 = get_band(meteo_h_11)
m_h_12 = get_band(meteo_t_12)
hum_atmo = (m_h_11 + m_h_12) / 2


# In[16]:


get_stats(temp_atmo)
get_stats(hum_atmo)


# In[17]:


hist_nan(temp_atmo)


# In[18]:


e_sat_ta = get_e_sat(temp_atmo)


# In[19]:


get_stats(e_sat_ta)


# In[20]:


e_atmo = e_sat_ta * hum_atmo / 100


# In[21]:


create_tif(e_sat_ta, "e_sat_ta.tif")
create_tif(e_atmo, "e_atmo.tif")


# In[ ]:


get_stats(e_atmo)


# In[ ]:


emissivite_atmo = 1.24 * ((e_atmo/(100*temp_atmo)) ** (1./7))


# In[ ]:


create_tif(emissivite_atmo, "emissivite_atmo.tif")


# In[ ]:


get_stats(emissivite_atmo)


# In[ ]:


del hum_atmo


# ## 1b - Calcul Ra

# In[ ]:


sigma = 5.67e-8


# In[ ]:


r_a = emissivite_atmo * sigma * temp_atmo**4


# In[ ]:


create_tif(r_a, "r_a.tif")


# In[ ]:


get_stats(r_a)


# In[ ]:


del emissivite_atmo


# # 2 - Calcul du rayonnement terrestre, $ R_{T} $
# $ R_{T} = \sigma T_{RAD}^{4} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ T_{RAD} $ (K) : température radiative

# In[ ]:


temp_rad = get_band(l8_th)


# In[ ]:


r_t = sigma * temp_rad**4


# In[ ]:


get_stats(r_t)


# In[ ]:


create_tif(r_t, "r_t.tif")


# # 3 - Calcul de l'émissivité de surface, $ \epsilon_{SURF} $
# $ \epsilon_{SURF} $ =  
# * 0,973 si NDVI < 0,2
# * 0,99 si NDVI < 0 ou NDVI > 0,5
# * $ 0,017P_{V} + 0,973 $ si 0,2 < NDVI < 0,5
# 
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ P_{V} = \left( \frac{NDVI - NDVI_{min}}{NDVI_{max} - NDVI_{min}} \right)^{2} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; avec $ NDVI_{min} = 0,2 $ et $ NDVI_{max} = 0,5 $  
# <br>
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ NDVI = \frac{NIR - RED}{NIR + RED} $

# ## 3.1 - Calcul de $ P_{V} $  

# In[42]:


red = get_band(images["red"])
nir = get_band(images["nir"])


# In[40]:


get_stats(nir)


# In[ ]:


ndvi_min_pv = 0.2
ndvi_max_pv = 0.5


# In[ ]:


ndvi = (nir - red) / (nir + red)


# In[ ]:


create_tif(ndvi, "ndvi.tif")


# In[ ]:


p_v = ((ndvi - ndvi_min_pv) / (ndvi_max_pv - ndvi_min_pv)) ** 2


# In[ ]:


create_tif(p_v, "p_v.tif")


# In[ ]:


e_s = 0.973
e_v = 0.99
em_surf = np.where(np.logical_or(ndvi < 0, ndvi > ndvi_max_pv), e_v,
                   np.where(ndvi < ndvi_min_pv, e_s, 0.017 * p_v + 0.973))


# In[ ]:


get_stats(em_surf)


# In[ ]:


create_tif(em_surf, "em_surf.tif")


# In[ ]:


del p_v


# # 4 - Calcul de l'albédo
# Calcul suivant la méthode de Brest (1987)  
# $ seuil = \frac{swir2}{nir} $  
# $ Si\, seuil > 2 : albédo = 0.526*nir + 0.362*swir2 + 0.112*0.5*swir2 $  
# $ Si\, seuil <= 2 : albédo = 0.526*nir + 0.474*swir2 $

# In[ ]:


swir2 = get_band(images["swir2"])
seuil = swir2/nir


# In[ ]:


albedo = np.where(seuil > 2, 0.526*nir + 0.362*swir2 + 0.112*0.5*swir2,
                  0.526*nir + 0.474*swir2)


# In[ ]:


get_stats(albedo)


# In[ ]:


create_tif(albedo, "albedo.tif")


# In[ ]:


del swir2


# # 5 - Calcul de la densité de flux de chaleur latente, G
# $ G = (0,1f_{v} + (1-f_{v})0,5)R_{N} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ f_{v} $ : fraction de végétation   
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ R_{N} $ : rayonnement net

# ## 5.1 Calcul de $ f_{v} $
# $ f_{v} = 1,62SAVI - 0,37 $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ SAVI = \frac{NIR - RED}{NIR + RED + 0,5} $

# In[ ]:


savi = (nir - red) / (nir + red + 0.5)
f_v = 1.62 * savi - 0.37


# In[ ]:


get_stats(f_v)


# In[ ]:


create_tif(f_v, "f_v.tif")
create_tif(savi, "savi.tif")


# In[ ]:


del red, nir, savi


# ## 5.2 Calcul de $ R_{N} $
# $ R_{N} = (1 - albedo)R_{G} + \epsilon _{SURF}R_{a} - R_{T}$

# In[ ]:


rg_11 = get_band(meteo_rg_11)
rg_12 = get_band(meteo_rg_12)
r_g = (rg_12 - rg_11) / 3600


# In[ ]:


r_n = (1-albedo) * r_g + em_surf * r_a - r_t
r_n = r_n.astype(np.float32)


# In[ ]:


get_stats(r_n)


# In[ ]:


hist_nan(r_n, bins=100)


# In[ ]:


create_tif(r_n, "r_n.tif")


# In[ ]:


del albedo


# ## 5.3 Calcul de G
# $ G = (0,1f_{v} + (1-f_{v})0,5)R_{N} $ 

# In[ ]:


g = (-0.4 * f_v + 0.5) * r_n


# In[ ]:


get_stats(g)


# In[ ]:


create_tif(g, "g.tif")


# In[ ]:


del f_v


# # 7 - Calcul de EF

# ## 7.1 - Calcul de FVC
# $ FVC = \left( \frac{NDVI - NDVI_{min}}{NDVI_{max} - NDVI_{min}} \right)^2 $  

# In[ ]:


min_ndvi = ndvi[ndvi>=0].min()
max_ndvi = np.nanmax(ndvi)
fvc = ((ndvi - 0) / (max_ndvi - 0)) ** 2


# In[ ]:


# hist_nan(fvc, 100)


# In[ ]:


get_stats(fvc)


# In[ ]:


create_tif(fvc, "fvc.tif")


# In[ ]:


del ndvi


# ## 7.2 - Calcul du coeficient de Priestley-Taylor, $ \phi $

# ### 7.2.1 - Calcul de $ T_{s} - T_{a} $
# $ T_{S} = T_{RAD} (E_{SURF})^{\frac{-1}{4}}  $

# In[ ]:


# Suppression des valeurs aberrantes
temp_rad[temp_rad < 200] = np.nan
get_stats(temp_rad)


# In[ ]:


temp_surf = temp_rad * (em_surf ** (-1./4.))
get_stats(temp_surf)


# In[ ]:


# Suppression des valeurs aberrantes
temp_surf[temp_surf < 200] = np.nan


# In[ ]:


hist_nan(temp_surf, 100)


# In[ ]:


create_tif(temp_surf, "temp_surf.tif")


# In[ ]:


# Suppression des valeurs aberrantes
temp_atmo[temp_atmo < 200] = np.nan
get_stats(temp_atmo)


# In[ ]:


del temp_rad


# ### 7.2.2 Equations des bords humide et sec

# In[ ]:


ts_ta = temp_surf - temp_atmo


# In[ ]:


nb_interval = 25
pourcentage = 1


# In[ ]:


(pts_inf, pts_sup), (pts_inf_mean, pts_sup_mean) = courbes_phi(fvc, ts_ta,
                                                               nb_interval=nb_interval,
                                                               pourcentage=pourcentage)


# In[ ]:


# Liste de couleurs pour l'affichage des points des intervalles
color_list = plt.cm.Set1(np.linspace(0, 1, nb_interval))

fig, ax = plt.subplots(figsize=(14, 10))
fig.suptitle("Estimation du coefficient de Priestley-Taylor \n par double interpolation", fontsize=20)
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
reg_moy, = ax.plot(x_reg, y_sup,'k-', label="Régression des points moyens")
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
slope_sec = reg_h_tot[0]
y_inf = reg_h_tot[0]*x_reg + reg_h_tot[1]
# Affichage de tous les points du bord humide
ax.scatter(pts_inf[:, 0], pts_inf[:, 1], color=color_list[pts_inf[:, 2].astype(int)],
           alpha=0.2, edgecolor='none')
# Affichage de la régression de tous les points du bord humide
ax.plot(x_reg, y_inf,'b-')
reg_s_tot = linregress(pts_sup[:, 0], pts_sup[:, 1])
print("Bord sec : R2 = %f - pente = %f - intersect = %f" %
      (reg_s_tot[2] ** 2, reg_s_tot[0], reg_s_tot[1]))

y_sup = reg_s_tot[0]*x_reg + reg_s_tot[1]
# Affichage de tous les points du bord sec
ax.scatter(pts_sup[:, 0], pts_sup[:, 1], color=color_list[pts_sup[:, 2].astype(int)],
           alpha=0.2, edgecolor="none")
# Affichage de la régression de tous les points du bord sec
plot_reg_tot, = ax.plot(x_reg, y_sup,'b-', label="Régression de l'ensemble des points")

ax.set_title("\nNombre d'intervalle = %d - Poucentage = %.1f%%"  % (nb_interval, pourcentage), fontsize=16)
ax.set_xlabel("FVC", fontsize=16)
ax.set_ylabel("Ts - Ta", fontsize=16)
plt.legend(handles=[pts, reg_moy, plot_reg_tot, plot_reg_humide])
# Sauvegarde de la figure au format png
plt.savefig(os.path.join(path_indice, "phi_%d_%.1f.png" % (nb_interval, pourcentage)), dpi=300)
plt.show()


# In[ ]:


t_min_hum = y_min_hum
slope_sec = reg_s_tot[0]
intercept_sec = reg_s_tot[1]


# **Equation du bord humide : temp = {{"%.5f" % y_min_hum}}  
# Equation du bord sec : temp = {{"%.2f" % reg_s_tot[0]}} * fvc + {{"%.2f" % reg_s_tot[1]}}**

# ### 7.2.3 Calcul de $ \Phi $
# $ \Phi = 1,26 \frac{T_{max}(FVC) - T}{T_{max}(FVC) - T_{min}}  $  
# $ T_{max} $  = équation du bord sec 

# In[ ]:


temp_max = slope_sec * fvc + intercept_sec


# In[ ]:


create_tif(temp_max, "temp_max_%d_%.1f.tif" % (nb_interval, pourcentage))


# In[ ]:


phi = 1.26 * (temp_max - ts_ta) / (temp_max - t_min_hum)


# In[ ]:


get_stats(phi)


# In[ ]:


create_tif(phi, "phi_%d_%.1f.tif" % (nb_interval, pourcentage))


# In[ ]:


print("Nombre de valeurs négative : %d" % (phi < 0).sum())
print("Nombre de valeurs > 1,26 : %d" % (phi > 1.26).sum())


# In[ ]:


# hist_nan(phi, bins=50)


# # 8 - Calcul de EF
# $ EF = \frac{\Delta}{\Delta + \gamma} \Phi  $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ \gamma = 66 Pa.K^{-1}$ (constante psychrométrique)  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ \Delta $ : tangente de la courbe $ e_{sat}(T) ~ avec~ e_{sat}(T) = 1000e^{52,57633 - \frac{6790,4985}{T} - 5,02808ln(T)} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ \Delta = \frac{d(e_{sat})}{dT} $  
# &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $ \Delta = e_{sat}(T)(\frac{6790,4985}{T^2} - \frac{5,02808}{T}) = \frac{e_{sat}(T)}{T} (\frac{6790,4985}{T} - 5,02808) $

# In[ ]:


tmoy = (temp_surf + temp_atmo)/2


# In[ ]:


delta = (get_e_sat(tmoy) / tmoy) * ((6790.4985 / tmoy) - 5.02808)


# In[ ]:


get_stats(delta)


# In[ ]:


# hist_nan(delta)


# In[ ]:


get_stats(e_sat_ta)


# In[ ]:


create_tif(delta, "delta_%d_%.1f.tif" % (nb_interval, pourcentage))


# In[ ]:


# gamma : constante psychométrique
gamma = 66
EF = delta * phi / (delta + gamma)


# In[ ]:


create_tif(EF, "EF_%d_%.1f.tif" % (nb_interval, pourcentage))


# In[ ]:


del e_sat_ta, temp_atmo, temp_hum, temp_max, temp_surf, delta


# # 9 - Calcul de $ \lambda $E
# $ \lambda E = EF(R_{N} - G)$

# In[ ]:


lambda_E = EF * (r_n - g)


# In[ ]:


get_stats(lambda_E)


# In[ ]:


# hist_nan(lambda_E, 50)


# In[ ]:


create_tif(lambda_E, "lambda_E_%d_%.1f.tif" % (nb_interval, pourcentage))
create_tif((r_n-g), "rn_g_%d_%.1f.tif" % (nb_interval, pourcentage))
create_tif(r_n, "r_n_%d_%.1f.tif" % (nb_interval, pourcentage))


# In[ ]:


del EF


# # 10 - Calcul de l'ETR
# $ ETR = \frac{\lambda E}{\lambda} c_{0} $ 

# In[ ]:


_lambda = 2.46e6
C0 = 0.368
ETR = (lambda_E / _lambda) * 3600 * 24 * C0


# In[ ]:


get_stats(ETR)


# In[ ]:


create_tif(ETR, "etr_%d_%.1f.tif" % (nb_interval, pourcentage))


# In[ ]:


del ETR, e_atmo, e_s, e_v, ts_ta


# In[ ]:


del em_surf, fvc, g, lambda_E, phi, r_a, r_n, r_t


# In[ ]:





# In[ ]:




