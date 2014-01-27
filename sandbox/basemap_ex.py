from mpl_toolkits.basemap import Basemap
from pylab import show

a = (0, 0)
b = (-95, 45)

m = Basemap(projection='ortho',
            # llcrnrlon=165, llcrnrlat=-79,
            # urcrnrlon=170, urcrnrlat=-77,
            lon_0=167, lat_0=-78)
# m = Basemap(projection='ortho',
#             lat_0=-77, lon_0=165)
m.drawcoastlines()

# lon1 = 95
# lat1 = 0
# lon2 = 0
# lat2 = 45
# m.drawgreatcircle(lon1, lat1, lon2, lat2)

show()