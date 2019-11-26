from pyproj import Transformer
import math
transformer_to_lamb= Transformer.from_crs("EPSG:4326", "EPSG:2157", always_xy=True)

lat = 43.6942
longi = 7.2652

delta_lat = 0.00746
delta_lon = 0.0149
x_0,y_0=transformer_to_lamb.transform(lon,lat)
x_fin,y_fin=transformer_to_lamb.transform(lon + delta_lon,lat + delta_lat)

#x_0,y_0=transformer_to_lamb.transform(
#x_fin,y_fin=transformer_to_lamb.transform(7.28018,43.70168)

def conversion(lat,longi):
    x_lamb,y_lamb=transformer_to_lamb.transform(lat,longi)
    return (x_lamb-x_0,y_lamb-y_0)

def conv2(lat_deg,lon_deg):
  n = 2**zoom
  lat_rad = math.radians(lat_deg)
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)

  return x,y

#lat = 43.69795
#longi = 7.26763
#print(conversion(lat,longi),conv2(lat,longi))


