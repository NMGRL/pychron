from mpl_toolkits.basemap import Basemap
from pylab import show

a = (0, 0)
b = (-95, 45)

m = Basemap()
m.drawcoastlines()

lon1 = 95
lat1 = 0
lon2 = 0
lat2 = 45
m.drawgreatcircle(lon1, lat1, lon2, lat2)

show()