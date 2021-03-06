import time
import shelve
from collections import defaultdict
from conversion import conversion,lon2x,lat2y,transfoinverse
import numpy as np
import matplotlib.pyplot as plt
import math
from creer_liste_clients import creer_clients_csv
from newmaptograph import graph,coor_point,trouvpoint,grosgraph,approx
from classes import *
from pyproj import Transformer
from optimisation_des_tournees import Clarke
from mig_algo_energie_final import Velo
import random

from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image
#transformer_to_lamb = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
#transformer_to_lat_long = Transformer.from_crs( "EPSG:2154","EPSG:4326", always_xy=True)



def init_carte(min_lat,min_lon,max_lat,max_lon,save):
    """carte : image png du cadre de l'algorithme
       bords : [x1,y1,x2,y2] les bords du rectangle"""
    def deg2num(lat_deg, lon_deg, zoom):
      lat_rad = math.radians(lat_deg)
      n = 2.0 ** zoom
      xtile = int((lon_deg + 180.0) / 360.0 * n)
      ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
      return (xtile, ytile)

    def num2deg(xtile, ytile, zoom):
      n = 2.0 ** zoom
      lon_deg = xtile / n * 360.0 - 180.0
      lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
      lat_deg = math.degrees(lat_rad)
      return (lat_deg, lon_deg)



    def getImageCluster(lat_deg, lon_deg, delta_lat,  delta_long, zoom):
        smurl = r"http://a.tile.openstreetmap.org/{0}/{1}/{2}.png"
        xmin, ymax = deg2num(lat_deg, lon_deg, zoom)
        xmax, ymin = deg2num(lat_deg + delta_lat, lon_deg + delta_long, zoom)
        latmin,longmin = num2deg(xmin,ymax+1,zoom)
        latmax,longmax = num2deg(xmax+1,ymin,zoom)

        Cluster = Image.new('RGB',((xmax-xmin+1)*256-1,(ymax-ymin+1)*256-1) ) 
        for xtile in range(xmin, xmax+1):
            for ytile in range(ymin,  ymax+1):
                imgurl=smurl.format(zoom, xtile, ytile)
                req = Request(imgurl, headers={'User-Agent': "AppleWebKit/537.36"})
                print("Opening: " + imgurl)
                imgstr = urlopen(req).read()
                tile = Image.open(BytesIO(imgstr))
                Cluster.paste(tile, box=((xtile-xmin)*256 ,  (ytile-ymin)*255))

        return (Cluster,latmin,latmax,longmin,longmax)


    lat = 43.6942
    longi = 7.2652
    delta_lat = 0.00746
    delta_lon = 0.0149
    lat = min_lat
    longi = min_lon
    delta_lat = max_lat - min_lat
    delta_lon = max_lon - min_lon
    zoom = 16

    #a = getImageCluster(lat,longi,delta_lat,delta_lon,zoom)
    a = save['clus']
    #save['clus'] = a
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('white')
    tab = np.asarray(a[0])
    xmin = lon2x(a[3])
    ymax = lat2y(a[1])
    #xmin,ymax = conversion(a[1],a[3])
    xmax = lon2x(a[4])
    ymin = lat2y(a[2])
    print(xmin,xmax,ymin,ymax)
    ax.imshow(tab,extent = [xmin,xmax,ymax,ymin])
    #xmax, ymin = conversion(a[2],a[4])
    echelles = [xmin,xmax,ymin,ymax]
    return echelles,ax

def actualiser_carte(liste_tripo,echelles,trouver_point): 
    """liste_tripo : liste d'objets de type triporteur"""
    for elt in liste_tripo:
        xy = Triporteur.convert(elt.pos[0],elt.pos[1],echelles)
        if elt.liste_tournee != []:
            print("pierre est lent, ",xy)
            xy = trouver_point(elt.last_dv_point,elt.liste_tournee[0],elt.prop_arrete) 
            print("c bon ", xy)
            latlon = [xy.latitude,xy.longitude]
            xy = Triporteur.convert(latlon[0],latlon[1],echelles)
        #print(elt," je vais en ",xy)
        elt.dot.set_offsets([xy[0],xy[1]])

def dicos():
    list_coor=np.genfromtxt('liste_coordonees.csv',delimiter=',')
    list_route=np.genfromtxt('liste_adjacence.csv',delimiter=',')
    dico_points={}
    for i,point in enumerate(list_coor):
        dico_points[(point[0],point[1])] = [(list_coor[int(j)][0],list_coor[int(j)][1]) for j in list_route[i] if not np.isnan(j)]
    def route(i,j):
        if j in dico_points[i]:
            return 1
        else:
            return 0
    altitude_route=np.genfromtxt('altitude_route.csv',delimiter=',')
    altitude={}
    for i,point in enumerate(list_coor):
        altitude[(point[0],point[1])] = altitude_route[i]
    
    return dico_points, altitude

def liste_provisoire(nb_clients,altitude):
    l = []
    for i in range(nb_clients):
        l.append(random.choice(list(altitude.items())))
    return l


def boucle(n,v,nb_clients,t,capacity,charge,elp):
    """n : nombre de triporteurs
       clients : liste d'objets de classe delivery_point
       dist : dist[i][j] renvoit la distance entre i et j"""

    d = {}
    dict_temps = {}
    save = shelve.open('sauvegarde')
    #liste_clients = creer_clients_csv(nb_clients,csv = "shops.csv")
    #save['liste_clients'] = liste_clients
    liste_clients = save['liste_clients']
    liste2 = liste_clients.copy()
    liste2.append(elp)
    liste_lat = [elt.latitude for elt in liste2]
    liste_lon = [elt.longitude for elt in liste2]
    min_lat = np.min(liste_lat)
    min_lon = np.min(liste_lon)
    max_lat = np.max(liste_lat)
    max_lon = np.max(liste_lon)
    echelles,ax = init_carte(min_lat,min_lon,max_lat,max_lon,save)
    bornes = []
    xy = Triporteur.convert(elp.latitude,elp.longitude,echelles)

    dico_points,altitude = dicos()
    res_points = coor_point(dico_points)
    grosave = grosgraph(res_points,altitude,Velo(400))
    """#on adaapte liste2 aux points proches
    pliste = [Point(elt.latitude,elt.longitude) for elt in liste2]
    pliste = approx(pliste,coor_point(dico_points))
    g = coor_point(dico_points)
    for i in range(len(liste2)):
        liste2[i].latitude = pliste[i].latitude
        liste2[i].longitude = pliste[i].longitude
    #...
    """

    p_dist = save['pdist']
    #p_dist = graph(coor_point(dico_points),altitude,liste2,bornes,Velo(400))
    #save['pdist'] = p_dist
    liste2 = save['liste2']
    #save['liste2'] = liste2
    #print(p_dist)
    elpa = elp
    elp = liste2[len(liste2)-1]
    #print("elp : ", elpa," et ", elp)
    for elt in liste_clients:
        xy = Triporteur.convert(elt.latitude,elt.longitude,echelles)
        ax.scatter(xy[0],xy[1],marker = 's',s = 30,c = "red")

    xy = Triporteur.convert(elp.latitude,elp.longitude,echelles)
    ax.scatter(xy[0],xy[1],s = 110 ,marker = "X")
    dist = defaultdict(dict)
    for client in liste2:
        for client2 in liste2:
            pkey = Point(client.latitude,client.longitude)
            p2key = Point(client2.latitude,client2.longitude)
            dist[client][client2] = p_dist[pkey][p2key]
    liste_client = liste2.copy()
    elp = liste2[len(liste2)-1]
    del liste_client[len(liste2)-1]
    #print ("dist : ",dist)
    #print("liste ; ",liste_client)
    
    """dist = defaultdict(dict)
    for elt in liste2:
        for elt2 in liste2:
           dist[elt][elt2] = Poids(100,10,True)
"""
    def trouver_point(depart,arrivee,prop):
        #temps = prop*dist[depart][arrivee].duree
        #print(temps)
        return trouvpoint(grosave[0],depart,arrivee,prop,altitude,Velo(400),res_points,d,dict_temps)
    liste_tripo = [Triporteur(capacity, charge, elp,v,echelles) for i in range(n)]
    #liste_tripo[0].liste_tournee = liste_clients
    
    while 1:
        liste_client = Clarke(liste_tripo,dist,liste_client,elp)
        i = 0
        for elt in liste_tripo:
            if elt.liste_tournee != []:
                elt.avancer(dist,t)
        actualiser_carte(liste_tripo,echelles,trouver_point)
        plt.pause(t)
nb_clients = 7
elp = DeliveryPoint(43.701760, 7.269595)
boucle(3,10,nb_clients,0.01,10,100,elp)

