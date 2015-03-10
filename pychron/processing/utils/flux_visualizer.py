# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'
# ============= enthought library imports =======================
import csv
from pylab import show, meshgrid, zeros, \
    contourf, array, linspace, scatter, cm, xlabel, ylabel, \
    colorbar, rc, gcf
import math
# from itertools import groupby
import matplotlib.pyplot as plt
from pychron.core.regression.ols_regressor import MultipleLinearRegressor
from pychron.core.regression.flux_regressor import PlaneFluxRegressor

# ============= standard library imports ========================
# ============= local library imports  ==========================
def load_holder(holder):
    holes = []
    with open(holder, 'r') as rfile:
        reader = csv.reader(rfile, delimiter=',')
        reader.next()  # pop header

        for i, line in enumerate(reader):
            try:
                x, y = map(float, line)
                v = math.atan2(y, x)
#                print i + 1, v, x, y, math.degrees(v)
                holes.append((x, y, v))
            except Exception:
                pass
    return holes

def pt_factory(line, holes):
    '''
        return theta, r for each line
        theta is calculated from corresponding x,y 
        r is flux 
    '''
    try:
        hole, j, sample = line
#        if sample == 'FC-2':
        x, y, theta = holes[int(hole) - 1]
#        print hole, theta
        return x, y, theta, float(j)
    except Exception, e:
        print e

def get_column_idx(names, header):
    if not isinstance(names, (list, tuple)):
        names = (names,)

    for attr in names:
        for ai in (attr, attr.lower(), attr.upper(), attr.capitalize()):
            if ai in header:
                return header.index(ai)

def load_flux_xls(p, holes, header_offset=1):
    import xlrd
    wb = xlrd.open_workbook(p)
    sheet = wb.sheet_by_index(0)
    header = sheet.row_values(0)
    hole_idx = get_column_idx('hole', header)
    j_idx = get_column_idx('j', header)
    j_err_idx = get_column_idx(('j_error', 'j err'), header)

    data = []
    hole_ids = []
    for ri in range(sheet.nrows - header_offset):
        ri += header_offset
#         if ri % 2 == 0:
#             continue
        hole = sheet.cell_value(ri, hole_idx)
        if hole:
            hole = int(hole) - 1
            j = sheet.cell_value(ri, j_idx)
            je = sheet.cell_value(ri, j_err_idx)
            j, je = float(j), float(je)
            x, y, v = holes[hole]
            hole_ids.append(hole)
            data.append((x, y, j, je))

    data = array(data)
    return data.T, hole_ids

def flux_contour2d(xx, yy, z, ze, holes, hole_ids, fit_dev=False, age_space=0):
    x, y = zip(*[(x, y) for i, (x, y, v) in enumerate(holes)
                        if not i in hole_ids])

    n = z.shape[0]
    r = max(xx)
    XX, YY = make_grid(r, n)

    m = model_flux(n, xx, yy, XX, YY, z)
    if fit_dev:
        k = model_flux(n, xx[:22], yy[:22], XX, YY, z[:22], klass=MultipleLinearRegressor)
        zi = m - k
    else:
        zi = m

    if age_space:
        zi *= age_space

    r = max(xx)
    xi = linspace(-r, r, n)
    yi = linspace(-r, r, n)
    contourf(xi, yi, zi, 50, cmap=cm.jet)

    cb = colorbar()

    label = 'Delta-Age @28.02 (ka)' if age_space else 'J %'
    cb.set_label(label)

    scatter(x, y, marker='o',
            c='black',
            s=200,
            alpha=0.1
            )

    scatter(xx, yy, marker='o',
            cmap=cm.jet,
#                 lw=0,
#                 facecolor='None',
            c='black',
#                 c=z,
            s=200,
            alpha=0.5
#                 s=300
            )
#         draw_border(1)
#         draw_circular_grid(r, rings)
    f = gcf()
    f.set_size_inches((8, 8))
    plt.axes().set_aspect('equal')
    xlabel('X (mm)')
    ylabel('Y (mm)')
    rc('font', **{'size': 24})

def model_flux(n, xx, yy, XX, YY, z, klass=PlaneFluxRegressor):
    nz = zeros((n, n))
    xy = zip(xx, yy)
    reg = klass(xs=xy, ys=z)
    for i in xrange(n):
        for j in xrange(n):
            pt = (XX[i, j],
                  YY[i, j])
            v = reg.predict([pt])[0]
            nz[i, j] = v
    return nz

def flux_contour3d(xx, yy, z, ze):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.scatter(xx, yy , z, c=z,
               s=100,
               lw=0,
               cmap=cm.jet
               )

    # plot error bars
    for xj, yj, zj, ej in zip(xx, yy, z, ze):
        ax.plot([xj, xj], [yj, yj], [zj - ej, zj + ej],
                c='black')
#             ax.plot([xj, xj], [yj, yj], [zj, zj - ej])
#             print X.shape
#             contourf(xi, yi, zi, 25, cmap=cm.jet)

#         ax.contourf(XX, YY, zi,
#                     20,
#                     cmap=cm.jet)

    n = z.shape[0]
    r = max(xx)
    XX, YY = make_grid(r, n)
    ZZ = model_flux(n, xx, yy, XX, YY, z)

    p = ax.plot_surface(XX, YY, ZZ, cmap=cm.jet,
                    rstride=2, cstride=2,
                    linewidth=0, antialiased=False,
                    alpha=0.5
                    )

    ZZ = model_flux(n, xx[:22], yy[:22], XX, YY, z[:22],
                    klass=MultipleLinearRegressor)

    p = ax.plot_surface(XX, YY, ZZ, cmap=cm.jet,
                    rstride=2, cstride=2,
                    linewidth=0, antialiased=False,
                    alpha=0.5
                    )

    cb = fig.colorbar(p)
    cb.set_label('Delta-J %')


def visualize_flux_contour(p, holder, delim=','):
#    from traits.etsconfig.etsconfig import ETSConfig
#    ETSConfig.toolkit = 'qt4'
#    from pychron.core.regression.ols_regressor import MultipleLinearRegressor
    use_2d = True
    #use_2d = False
    fit_dev = False
    #     calc_dev = True
    #     calc_dev = False
#     age_space = 280.2
#     age_space = 0

    holes = load_holder(holder)

    (xx, yy, z, ze), hole_ids = load_flux_xls(p, holes)


    ze = (ze / z) * 100
    mz = min(z)
    z = z - mz
    z /= mz
    z *= 100

#     n = z.shape[0]
#     r = max(xx)
#     xi = linspace(-r, r, n)
#     yi = linspace(-r, r, n)
#     X = xi[None, :]
#     Y = yi[:, None]

#     zi = griddata((xx, yy), z, (X, Y),
# #                         method='linear',
#                     method='cubic',
# #                     fill_value=min(z)
#                     )
#     XX, YY = meshgrid(xi, yi)

    if use_2d:
        flux_contour2d(xx, yy, z, ze, holes, hole_ids, fit_dev=fit_dev)
    else:
        flux_contour3d(xx, yy, z, ze,)

    show()


def interpolate_flux(pholes, p, holder, delim=','):
    holes = load_holder(holder)

    (xx, yy, z, ze), hole_ids = load_flux_xls(p, holes)
    xy = zip(xx, yy)
    reg = PlaneFluxRegressor(xs=xy, ys=z, yserr=ze, error_calc_type='SEM')
    reg.calculate()
    output = []
    for hi in pholes:
        x, y, t = holes[hi - 1]

        j, je = 0, 0
        pt = [(x, y)]
        j = reg.predict(pt)[0]
        je = reg.predict_error([pt])[0]

        print hi, j, je
        #output.append((j,je))

        #n = z.shape[0]
        #r = max(xx)
        #XX, YY = make_grid(r, n)

        #ZZ = model_flux(n, xx, yy, XX, YY, z)


def make_grid(r, n):
    xi = linspace(-r, r, n)
    yi = linspace(-r, r, n)
    return meshgrid(xi, yi)

if __name__ == '__main__':
#     p = '/Users/ross/Sandbox/flux_visualizer/J_data_for_nm-258_tray_G_radial.txt'
    p = '/Users/ross/Sandbox/flux_visualizer/J_data_for_nm-258_tray_G2.txt'
    p = '/Users/ross/Sandbox/flux_visualizer/J_data_for_nm-258_tray_G3.txt'
    p = '/Users/ross/Sandbox/flux_visualizer/J_nm-258_tray_G.xls'
    p = '/Users/ross/Sandbox/flux_visualizer/J_nm-258_tray_G2.xls'
    p = '/Users/ross/Sandbox/flux_visualizer/J_NM-259A.xls'
    # p = '/Users/ross/Sandbox/flux_visualizer/J_NM-259A2.xls'
    # p = '/Users/ross/Sandbox/flux_visualizer/Tray_I_NM-261.xls'
    #     p = '/Users/ross/Sandbox/flux_visualizer/runid_contour.txt'
    #    p = '/Users/ross/Sandbox/flux_visualizer/J_data_for_nm-258_tray_G.txt'
    holder = '/Users/ross/Sandbox/flux_visualizer/irradiation_tray_maps/1_75mm_3level'
    #    visualize_flux(p, holder)
    #    visualize_flux_contour(p, holder)
    #    visualize_flux_contour(p, holder, delim='\t')
    holes = [45, 47, 49, 51, 53]
    interpolate_flux(holes, p, holder, delim='\t')
# ============= EOF =============================================
# def load_flux_csv(p, holes, delim):
#     with open(p, 'U') as fp:
#         reader = csv.reader(fp, delimiter=delim)
#         reader.next()
#
#         mi = Inf
#         ma = -Inf
#         xy = []
#         z = []
#         ze = []
# #         rs = []
#         hole_ids = []
#         for line in reader:
#             if not line:
#                 continue
#             hole = int(line[0])
#             hole_ids.append(hole - 1)
#             j = float(line[1])
#             je = float(line[2])
#             x, y, v = holes[hole - 1]
#             xy.append((x, y))
#             z.append(j)
#             z.append(je)
# #             rs.append(round(((x ** 2 + y ** 2) ** 0.5) * 100))
#
#             mi = min(mi, j)
#             ma = max(ma, j)
#
#         xy = array(xy)
#         xx, yy = xy.T
#         z = array(z)
#
#         return (xx, yy, z, ze), hole_ids
# def draw_border(d):
#     r = d / 2.
#     xs = linspace(-r, r, 200)
#     y = (r ** 2 - xs ** 2) ** 0.5
#     plot(xs, y, c='black')
#     plot(xs, -y, c='black')

# def draw_circular_grid(r, rings):
#     for ray in range(0, 360, 10):
#
#             m = -math.radians(ray)
#             x = r * math.cos(m)
#             y = r * math.sin(m)
#             plot([0, x], [0, y], ls='-.', color='black')
#
#     for ring in rings:
#         ring /= 100.
#         x = linspace(-ring, ring, 100)
#         y = (ring ** 2 - x ** 2) ** 0.5
#
#         plot(x, -y, ls='-.', color='black')
#         x = linspace(-ring, ring, 100)
#         y = (ring ** 2 - x ** 2) ** 0.5
#         plot(x, y, ls='-.', color='black')

# def visualize_flux(p, holder, use_polar=False):
#     '''
#         load the x,y points for irrad holder
#         load the flux file
#
#         schema:
#             hole,j
#
#     '''
#     holes = load_holder(holder)
# #    x, y, holes = zip(*holes)
#
#     with open(p, 'U') as fp:
#         reader = csv.reader(fp)
# #        holes = []
# #        js = []
#         reader.next()
#         groups = []
#         group = []
#         for line in reader:
#             if not line:
#                 groups.append(group)
#                 group = []
#             else:
#                 group.append(pt_factory(line, holes))
#         groups.append(group)
#         mi = Inf
#         ma = -Inf
#
# #        fig = Figure()
#         if not use_polar:
#             fig = plt.figure()
#             ax = fig.add_subplot(111,
#                                  projection='3d'
#                                  )
# #        ax = fig.gca(projection='3d')
#         mi_rings = []
#         ma_rings = []
#         for args in groups:
# #            print args
# #            theta, r = zip(*args)
#             if use_polar:
#                 x, y, theta, r = zip(*[ai for ai in args if ai])
#
#                 polar(theta, r)
#                 mi = min(min(r), mi)
#                 ma = max(max(r), ma)
#
#             else:
#                 x, y, theta, j = zip(*[ai for ai in args if ai])
#                 x = array(x)
#                 y = array(y)
#                 r = (x ** 2 + y ** 2) ** 0.5
#
#                 m, b = polyfit(x, y, 1)
#
# #                xs = linspace(0, 0.5)
# #                mf, bf = polyfit(x, j, 1)
# #                fj = polyval((mf, bf), xs)
# #                ax.plot(xs, polyval((m, b), xs), fj,)
#                 ax.plot(x, y, j, color='blue'
# #                        label='{}'.format(int(math.degrees(mean(theta))))
#                         )
# #                ax.plot(x, y)
#                 midx = argmin(j)
#                 madx = argmax(j)
#
#                 mi_rings.append((x[midx], y[midx], j[midx]))
#                 ma_rings.append((x[madx], y[madx], j[madx]))
#
#         if not use_polar:
#             x, y, j = zip(*ma_rings)
#             ax.plot(x, y, j, color='black')
#             x, y, j = zip(*mi_rings)
#             ax.plot(x, y, j, color='black')
#         else:
#             ylim(mi * 0.95, ma)
# #        ax.set_xlim(-1, 1)
# #        ax.set_ylim(-1, 1)
# #                print r
# #        lines = [pt_factory(line, holes) for line in reader]
# #        theta, r = zip(*[args for args in lines if args])
#     legend()
#     show()
