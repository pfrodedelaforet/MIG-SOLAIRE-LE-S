import matplotlib.pyplot as plt
from conversion import *




class Point :
    def __init__(self, lat, lon):
        self.latitude = lat
        self.longitude = lon
        xy = conversion(lat,lon)
        self.x = xy[0]
        self.y = xy[1]
        #self.alti = cartalt[round((self.x-xo) / pas)][round((self.y-yo) / pas)]
    
    def __repr__(self) :
        return (f"point de latitude {self.latitude}, de longitude {self.longitude}")
    
    def __eq__(self, other):
        return ((self.latitude == other.latitude) and (self.longitude == other.longitude))
    def __hash__(self):
        return hash(str(self))

class DeliveryPoint(Point):
    def __init__(self, lat, lon, t1 = None, t2= None ,masse = None):
        Point.__init__(self, lat, lon)
        self.t1 = t1
        self.t2 = t2
        self.masse = masse #masse du colis a livrer en kg
    def __repr__(self):
        return (Point.__repr__(self)+f", il veut etre livre entre {self.t1} et {self.t2}")
    
    def __eq__(self, other):
        return ((self.latitude, self.longitude, self.t1, self.t2, self.masse)==(other.latitude, other.longitude, other.t1, oter.t2, other.masse))

    def __hash__(self):
        return hash(str(self))


class Triporteur:
    def convert(latitude,longitude,echelles):
        y,x = conversion_aff(latitude,longitude)
        xmin,xmax,ymin,ymax = echelles
        res = [x,y]
        return res
    def __init__(self, capacity, charge, elp, v, echelles, puissance_batterie = 1000,puissance_moteur=1000,batterie_capacity=10000):
        self.capacity = capacity #flottant : poids qu'il peut porter
        self.charge = charge #flottant : charge du triporteur : en w.h
        self.pos = [elp.latitude,elp.longitude]
        self.liste_tournee = [] #Liste de DeliveryPoint
        self.last_dv_point = elp #de type point : elp de départ du triporteur
        self.vitesse = v #en m/s 
        self.taille_arrete = -1
        self.prop_arrete = 0
        self.puissance_batterie=puissance_batterie
        self.puissance_moteur=puissance_moteur
        self.batterie_capacity=batterie_capacity
        self.time_to_be_fully_charged=(batterie_capacity-charge)/puissance_batterie
        xy = Triporteur.convert(self.pos[0],self.pos[1],echelles)
        self.dot = plt.scatter(xy[0],xy[1],s=100)
        self.taille_arrete = -1
        self.last_dv_point = elp
        self.prop_arrete = 0
    def avancer(self,dist,t):
        #print(self.liste_tournee)
        if self.taille_arrete == -1 and self.liste_tournee != []:
            self.taille_arrete = dist[self.last_dv_point][self.liste_tournee[0]].energie 
        #print("je vais vers : ",self.liste_tournee[0].latitude," , ",self.liste_tournee[0].longitude, "OR MORE LIKE ",self.liste_tournee[0].x," , ",self.liste_tournee[0].y)
        proptot = self.vitesse*t/self.taille_arrete + self.prop_arrete
        print("jen suis a : ",self.prop_arrete)
        if proptot < 1 and self.taille_arrete not in (float("inf"),0) :
            self.prop_arrete = proptot
            self.pos = [self.last_dv_point.latitude + (self.liste_tournee[0].latitude-self.last_dv_point.latitude)*self.prop_arrete,self.last_dv_point.longitude + (self.liste_tournee[0].longitude-self.last_dv_point.longitude)*self.prop_arrete]
        else:
            self.last_dv_point = self.liste_tournee[0]
            self.pos = [self.last_dv_point.latitude,self.last_dv_point.longitude]
            del self.liste_tournee[0]
            reste = (proptot-1)*self.taille_arrete/self.vitesse
            self.taille_arrete = -1
            self.prop_arrete = 0
            if self.liste_tournee != []:
                self.avancer(dist,reste) 
        
    def __repr__(self):
        str(self.position)
"""class Bornes(Point):
    def __init__(self, lat, lon, priseslibres, charges):
        Point.__init__(self, lat, lon)
        self.priseslibres = priseslibres #tableau de booleen: à chaque case du tableau est associée une prise
        self.charges = charges #tableau en Wh des charges de chacune des batteries 
    def reserv(self):
        for i in range(len(priseslibres)):
            if priseslibres[i] & :# ajouter condition de choix fixée par romain et Jeremy
                priseslibres[i] = False #on choisit la prise 
                return i
        return None #ie c'est tout réservé déjà
    def dereserv(self, i, chargetriporteuravant):
        priseslibres[i] = True 
        charges[i] = chargetriporteuravant #ie on a remplacé la batterie par la notre          
""" 
class Poids:
    def __init__(self, energienecess, t, faisable):
        self.energie = energienecess
        self.duree = t
        self.faisable = faisable #un booléen 
    def __add__(self,other): #Commutatif
        return Poids(self.energie+other.energie,self.duree + other.duree, self.faisable and other.faisable)
    
    def __sub__(self,other):
        return Poids(self.energie-other.energie,self.duree - other.duree, self.faisable)

    def __repr__(self):
        return (f"{self.energie} et {self.duree} et {self.faisable}")

#C'est pour le programme de Jeremy    
def _tourns(clients,dist,i,j,elp): #C'est un Poids ,s permet l'optimisation des tournees c'est une matrice len(pts)� ,i et j sont des indices, clients une liste de DeliveryPoint
    return(dist(clients[i],elp) + dist(elp,clients[j]) - dist(clients[i],clients[j]))

class Tournee:
    def __init__(self,i0,elp,dist,clients):#i0 est un indice, elp un point et dist une fonction de la forme i -> j -> poids ou i et j sont des points, clients est une liste de DeliveryPoint
        self.poids = dist(elp,clients[i0]) + dist(clients[i0],elp)
        self.elp = elp
        self.indices = [i0] #il est implicite qu'une tournee commence et finit par l'elp, il faut prendre cela en compte, les points sont un couple DeliveryPoint, heure d'arrivee presumee(en secondes, on suppose qu'on est a l'elp a t = 0)
        self.temps = [dist(elp,clients[i0]).duree]
        self.clients = clients
        self.dist = dist
        self.masse = clients[i0].masse
    
    def __add__(self,other):#Pas du tout commutatif
        tmp = Tournee(self.indices[0],self.elp,self.dist,self.clients)
        ot = other.temps.copy()
        tcop = self.temps.copy()
        elp = self.elp
        i = self.indices[-1]
        ti = self.temps[-1]
        j = other.indices[0]
        clients = self.clients
        for k in range(len(ot)): #il faut changer le moment de passage de la deuxieme tournee
            ot[k] += self.dist(clients[i],clients[j]).duree + ti - self.dist(elp,clients[j]).duree
        tmp.indices = self.indices + other.indices    
        tmp.temps = tcop + ot
        tmp.poids = self.poids + other.poids - _tourns(self.clients,self.dist,self.indices[-1],other.indices[0],elp)
        tmp.masse = self.masse + other.masse
        return (tmp)
