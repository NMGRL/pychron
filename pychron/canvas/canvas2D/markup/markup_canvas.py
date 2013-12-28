#===============================================================================
# Copyright 2011 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Enum, Any
#=============standard library imports ========================
from numpy import abs
import collections
#=============local library imports  ==========================
from pychron.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from pychron.canvas.canvas2D.scene.primitives.primitives import PointIndicator
# from pychron.canvas.canvas2D.markup.markup_items import PointIndicator


class MarkupContainer(collections.MutableMapping):
    layers = None
    def clear(self):
        self.layers = [dict(), dict()]

    def __init__(self, *args, **kw):
        '''
            default layer is 1 
            to draw under layer 1 use layer 0
                
        '''
        self.layers = [dict(), dict()]

#    def add_layer(self):
#        self.layers.append(dict())
#
#    def add_item(self, item, key, layer=0):
#        l = self.layers[layer]
#        l.update(key, item)

    def __iter__(self):
        return (k for l in self.layers for k in l)

    def __contains__(self, v):
        return True in [v in l for l in self.layers]

    def __getitem__(self, k):
        for l in self.layers:
            item = next((v for key, v in l.iteritems() if key == k), None)
            if item is not None:
                return item

    def __setitem__(self, k, v):
        if isinstance(k, tuple):
            li = k[1]
            key = k[0]
        else:
            li = 1
            key = k
        try:
            l = self.layers[li]
        except IndexError:
            self.layers.append(dict())
            l = self.layers[-1]

#        if len(l) > 100:
#            k = l.keys()
#            k.sort()
#            l.pop(k[0])

        l[key] = v

    def __len__(self):
        return sum([len(l) for l in self.layers])

    def __delitem__(self, k):
        if isinstance(k, tuple):
            li = k[1]
            key = k[0]
        else:
            li = 1
            key = k
        l = self.layers[li]
        try:
            del l[key]
        except KeyError:
            pass


class MarkupCanvas(BaseDataCanvas):
    '''
    '''
    markupcontainer = None
    temp_start_pos = None
    temp_end_pos = None
    current_pos = None
    line_counter = 0
    point_counter = 0

    selected_point = None
    selected_element = None

    selected = Any
    invalid_layers = None
    def __init__(self, *args, **kw):
        super(MarkupCanvas, self).__init__(*args, **kw)
        self.clear()

    def get_item(self, base, key):
        key = '{}{}'.format(base, key)
        return next((v for k, v in self.markupcontainer.iteritems() if k == key), None)

    def _draw_hook(self, gc, *args, **kw):
        '''

        '''

        # draw the lines currently held in the markupcontainer
        self._draw_current_markup(gc)
        self._draw_markup_dict(gc)
        super(MarkupCanvas, self)._draw_hook(gc, *args, **kw)

    def _draw_current_markup(self, *args, **kw):
        pass


    def _draw_markup_dict(self, gc):
        '''
    
        '''
        gc.save_state()
        test = lambda x: self.invalid_layers and x in self.invalid_layers
        try:

            for i, l in enumerate(self.markupcontainer.layers):
                if test(i):
                    continue

                for obj in l.itervalues():
#                    print obj
                    try:
                        obj.render(gc)
                    except AttributeError:
                        continue
        except RuntimeError:
            pass
        finally:
            gc.restore_state()

    def clear(self):
        self.markupcontainer = MarkupContainer()
        self.invalid_layers = []

    def _over_item(self, event, items=None):
        '''
        '''
        if items is None:

            items = self.markupcontainer.itervalues()

        return next((item for item in items if hasattr(item, 'is_in') and item.is_in(event)), None)
#        for item in items:
#            try:
#                if item.is_in(event):
#                    return item
#            except AttributeError:
#                continue
#            if hasattr(item, 'is_in'):

    def select_right_down(self, event):
        obj = self._over_item(event)
        self._menu_factory(event)

    def select_left_down(self, event):
        obj = self._over_item(event)
        self._selection_hook(obj)
        self.invalidate_and_redraw()

    def _selection_hook(self, obj):
        pass

    def _menu_factory(self, event):
        self.invalidate_and_redraw()

    def OnFoo(self, event):
        print 'asdfasd', event

    def select_mouse_move(self, event):
        self.normal_mouse_move(event)

    def normal_mouse_move(self, event):
        obj = self._over_item(event)
        if obj:
            event.window.set_pointer(self.select_pointer)
            self.event_state = 'select'
            self.selected = obj
        else:
            self.selected = None
            event.window.set_pointer(self.normal_pointer)
            self.event_state = 'normal'

class InteractionMarkupCanvas(MarkupCanvas):
    tool_state = Enum('select', 'line', 'mline', 'rect', 'point', 'noteditable')
    def get_path_points(self, k):
        '''

        '''
        self.m
        element = self.markupcontainer[k]
        if isinstance(element[0], list):
            path = []
            for lineseg in element[0]:
                path.append(self.map_data(lineseg[0]))
                path.append(self.map_data(lineseg[1]))

            pa = [path[0]]
            for i in range(1, len(path) - 2, 2):
                pa.append(path[i])

            pa.append(path[-1:][0])
        else:
            pa = element[:2]

        return pa

    def normal_mouse_move(self, event):
        '''
        '''
        if self.tool_state == 'noteditable':
            return

        a = self._over_mark_up_line(event)

        o = self._over_item(event)

        self.current_pos = (event.x, event.y)
        if a is not None or o is not None:
            if self.tool_state not in ['line', 'mline', 'rect']:
                # change mouse
                event.window.set_pointer(self.select_pointer)
                event.handled = True
        else:

            if self.tool_state == 'point':
                event.window.set_pointer(self.cross_pointer)
            elif self.tool_state not in ['line', 'mline', 'rect']:
                event.window.set_pointer(self.normal_pointer)
#        self.invalidate_and_redraw()
        self.request_redraw()

    def normal_left_down(self, event):
        '''

        '''
        if self.tool_state == 'noteditable':
            return

        try:
            self.selected_element.set_state(False)
        except AttributeError:
            pass


#        self.selected_point = None
#        self.selected_element = None
#
        self.temp_start_pos = (event.x, event.y)

        if self.tool_state in ['line', 'mline']:
            self.event_state = 'ldraw'
            event.window.set_pointer(self.cross_pointer)
        elif self.tool_state == 'rect':
            self.event_state = 'rdraw'
            event.window.set_pointer(self.cross_pointer)

        else:
            item = self._over_item(event)
            if item:
                self.selected_element = item
                self.selected_element.set_state(True)
                self.event_state = 'omove'
                event.handled = True
                event.item = item
            elif self.selected_element is not None:
                self.selected_element = None
                self.selected_point = None
            else:
                l = self._over_mark_up_line(event)

                if not l == None:
                    event.handled = True
                    e = self.markupcontainer[l]
                    self.selected_element = l
                    e[2] = True
                    if 'line' in l:
                        self.event_state = 'lmove'
                        point = None
                        if isinstance(e[0], list):
                            # this is a multiline
                            for i, pts in enumerate(e[0]):
                                point = self._over_mark_up_point(event, pts)
                                if point is not None:
                                    break
                            if point is not None:
                                point = [point, i]
                        else:
                            point = self._over_mark_up_point(event, e)

                        if not point == None:
                            self.selected_point = point
                            self.event_state = 'pmove'
                    elif 'rect' in l:
                        self.event_state = 'rmove'
                        # check over corner
                        pts = e[0]
                        tol = 10
                        pti = None
                        for i, (x, y) in enumerate(pts):
                            if abs(event.x - x) < tol and abs(event.y - y) < tol:
                                pti = i
                                break

                        if pti is not None:
                            self.selected_point = pti
                            self.event_state = 'rpmove'
                else:
                    if self.tool_state == 'point':
                        x, y = self.map_data((event.x, event.y))
                        pid = 'point{}'.format(self.point_counter)
                        self.markupcontainer[pid] = PointIndicator(x, y, canvas=self, identifier=pid)
                        self.point_counter += 1
                        event.handled = True
        self.request_redraw()


    def normal_key_pressed(self, event):
        '''
        '''
        try:
            if event.character == 'Backspace' and self.selected_element is not None:
                self.markupcontainer.pop(self.selected_element.identifier)
                self.selected_element = None
        except:
            pass

        self.key_set_tool_state(event)


    def omove_mouse_move(self, event):

        xadj, yadj = self._calc_adjustment(event)
        self.temp_start_pos = (event.x, event.y)
        self.selected_element.adjust(xadj, yadj)

#        self.invalidate_and_redraw()
        self.request_redraw()

    def omove_left_up(self, event):
        self.event_state = 'normal'


    def pmove_mouse_move(self, event):
        '''

        '''
        xadj, yadj = self._calc_adjustment(event)
        self.temp_start_pos = (event.x, event.y)

        def _update_(point, container, elem):

            if abs(point[0] - container[0][0]) <= 1 and abs(point[1] - container[0][1]) <= 1:
                ep = container[0]
                re = [(ep[0] + xadj, ep[1] + yadj), container[1]] + elem[2:]



            elif abs(point[0] - container[1][0]) <= 1 and abs(point[1] - container[1][1]) <= 1:
                ep = container[1]
                re = [container[0], (ep[0] + xadj, ep[1] + yadj)] + elem[2:]

            ep = (ep[0] + xadj, ep[1] + yadj)
            return ep, re

        element = self.markupcontainer[self.selected_element]
        pt = self.selected_point
        if isinstance(pt, list):
            # multiline
            ep, re = _update_(pt[0], element[0][pt[1]], element)
            self.selected_point = [ep, pt[1]]
            self.markupcontainer[self.selected_element][0][pt[1]] = (re[0], re[1])

            if 0 < pt[1] < len(element[0]) - 1:
                ep, re = _update_(pt[0], element[0][pt[1] + 1], element)
                self.markupcontainer[self.selected_element][0][pt[1] + 1] = (re[0], re[1])

        else:
            ep, re = _update_(pt, element, element)

            self.selected_point = ep
            self.markupcontainer[self.selected_element] = re

#        self.invalidate_and_redraw()
        self.request_redraw()

    def pmove_left_up(self, event):
        '''
        '''
        self.end_move()

    def lmove_mouse_move(self, event):
        '''

        '''
        se = self.selected_element
        element = self.markupcontainer[se]
        def _adjust(container):
            xe = container[0][0]
            ye = container[0][1]
            x2e = container[1][0]
            y2e = container[1][1]
            xadj, yadj = self._calc_adjustment(event)

            return (xe + xadj, ye + yadj), (x2e + xadj, y2e + yadj)

        if isinstance(element[0], list):
            npts = []
            for pts in element[0]:
                npts.append(_adjust(pts))
            ndict = [npts] + element[1:]
        else:
            npts = _adjust(element)
            ndict = [npts[0], npts[1]] + element[2:]

        self.markupcontainer[se] = ndict
        self.temp_start_pos = (event.x, event.y)
        # self.invalidate_and_redraw()
        self.request_redraw()
    def lmove_left_up(self, event):
        self.end_move()

    def ldraw_mouse_move(self, event):
        '''
        '''
        self.temp_end_pos = (event.x, event.y)
#        self.invalidate_and_redraw()
        self.request_redraw()

    def ldraw_left_down(self, event):
        '''

        '''
        b = self.bounds
        ob = self.outer_bounds
        # assumes uniform padding
        px = (ob[0] - b[0]) / 2.0
        py = (ob[1] - b[1]) / 2.0

        if px <= event.x <= b[0] + px and py <= event.y <= b[1] + py:
            self.temp_end_pos = (event.x, event.y)

            # store the line in the markupcontainer
            nline = [self.temp_start_pos, self.temp_end_pos, False]
            key = 'line{}'.format(self.line_counter)
            if self.tool_state == 'line':
                self.markupcontainer[key] = nline
                self.line_counter += 1

                # set state back to normal and redraw
                self.event_state = 'normal'
            elif self.tool_state == 'mline':
                pkey = 'mline{}'.format(self.line_counter - 1)
                if pkey in self.markupcontainer:
                    lines = self.markupcontainer[pkey][0]
                    lines.append((nline[0], nline[1]))
                else:
                    self.markupcontainer['mline{}'.format(self.line_counter)] = [[(nline[0], nline[1])], None, False]
                    self.line_counter += 1
                self.temp_start_pos = (event.x, event.y)

        # self.invalidate_and_redraw()
        self.request_redraw()

    def ldraw_key_pressed(self, event):
        '''
        '''

        if event.character == 's':
            event.window.set_pointer(self.normal_pointer)
            if self.tool_state == 'mline':
                self.event_state = 'normal'
                self.line_counter += 1
            self.tool_state = 'select'

        # self.invalidate_and_redraw()
        self.request_redraw()

    def rmove_mouse_move(self, event):
        elem = self.markupcontainer[self.selected_element]
        xa, ya = self._calc_adjustment(event)
        elem[0] = [(pt[0] + xa, pt[1] + ya) for pt in elem[0]]
        self.temp_start_pos = (event.x, event.y)
#        self.invalidate_and_redraw()
        self.request_redraw()

    def rmove_left_up(self, event):
        self.end_move()

    def end_move(self):
        elem = self.markupcontainer[self.selected_element]
        elem[2] = False
        self.event_state = 'normal'

    def rpmove_mouse_move(self, event):
        elem = self.markupcontainer[self.selected_element]
        xa, ya = self._calc_adjustment(event)


#        p1 = elem[0][self.selected_point - 1]
#
#        p2 = elem[0][self.selected_point]
#
#        p3 = elem[0][self.selected_point + 1]

        if self.selected_point == 0 or self.selected_point == 4:
            p1 = elem[0][1]
            p3 = elem[0][3]
            elem[0][1] = (p1[0] + xa, p1[1])
            elem[0][3] = (p3[0], p3[1] + ya)
        elif self.selected_point == 1:
            p1 = elem[0][0]
            p3 = elem[0][2]
            elem[0][0] = (p1[0] + xa, p1[1])
            elem[0][2] = (p3[0], p3[1] + ya)
        elif self.selected_point == 2:
            p1 = elem[0][1]
            p3 = elem[0][3]
            elem[0][3] = (p3[0] + xa, p3[1])
            elem[0][1] = (p1[0], p1[1] + ya)
        elif self.selected_point == 3:
            p1 = elem[0][2]
            p3 = elem[0][0]
            elem[0][2] = (p1[0] + xa, p1[1])
            elem[0][0] = (p3[0], p3[1] + ya)

        elem[0][self.selected_point] = (elem[0][self.selected_point][0] + xa,
                                         elem[0][self.selected_point][1] + ya)
        elem[0][-1] = elem[0][0]

        self.temp_start_pos = (event.x, event.y)
#        self.invalidate_and_redraw()
        self.request_redraw()

    def rpmove_left_up(self, event):
        self.end_move()

    def rdraw_mouse_move(self, event):
        self.temp_end_pos = (event.x, event.y)
#        self.invalidate_and_redraw()
        self.request_redraw()

    def rdraw_left_down(self, event):
        self.markupcontainer['rect'] = [
                                   [self.temp_start_pos,
                                    (self.temp_start_pos[0], self.temp_end_pos[1]),
                                    self.temp_end_pos,
                                    (self.temp_end_pos[0], self.temp_start_pos[1]),
                                    self.temp_start_pos], None, False

                        ]
        self.event_state = 'normal'
        self.tool_state = 'select'
#        self.invalidate_and_redraw()
        self.request_redraw()

    def key_set_tool_state(self, event):
        '''
        '''
        try:
            c = event.character
            window = event.window
            if c == 's':
                self.tool_state = 'select'
            elif c == 'l':
                window.set_pointer(self.cross_pointer)
                self.tool_state = 'line'
            elif c == 'm':
                window.set_pointer(self.cross_pointer)
                self.tool_state = 'mline'
            elif c == 'c':
                window.set_pointer(self.cross_pointer)
                self.tool_state = 'rect'

        except:
            pass



#        self.invalidate_and_redraw()
        self.request_redraw()


    def _draw_current_markup(self, gc):
        '''

        '''
        gc.save_state()

        if self.event_state == 'ldraw':
            gc.set_line_width(4)
            gc.set_stroke_color((1, 0, 1, 1))
            points = [self.temp_start_pos, self.temp_end_pos]
            gc.begin_path()
            gc.lines(points)
            gc.stroke_path()
        elif self.event_state == 'rdraw':
            gc.begin_path()

            if self.temp_end_pos:
                gc.lines([self.temp_start_pos,
                          (self.temp_start_pos[0], self.temp_end_pos[1]),
                           self.temp_end_pos,
                          (self.temp_end_pos[0], self.temp_start_pos[1]),
                          self.temp_start_pos
                          ]
                          )

            gc.stroke_path()

        gc.restore_state()


    def _over_mark_up_line(self, event, tolerance=7):
        '''

        '''

        def _get_key(cont, tolerance):

            x = cont[0][0]
            y = cont[0][1]
            x2 = cont[1][0]
            y2 = cont[1][1]
            m, b = self._get_line_parameters(x, y, x2, y2)

            xa = min(x, x2)
            xb = max(x, x2)
            ya = min(y, y2)
            yb = max(y, y2)

            if m == 'undefined' or abs(m) > 1000000:
                    # the line is vertical
                    if abs(event.x - x) <= tolerance and ya <= event.y <= yb:
                        return k

            # do a first pass by making a box
            elif xa <= event.x <= xb and ya - 5 <= event.y <= yb + 5:
                hitbounds = 5 * abs(m) / 3.0
                if m == 0:
                    hitbounds = 10

                tolerance = abs(m) * tolerance / 3.0
                # loop thru x values form mousex to +- tolerance
                for i in range(int(event.x - hitbounds), int(event.x + hitbounds)):
                    # get the y value of the line at i
                    yi = m * i + b

                    if m == 0:
                        tolerance = 5

                    if abs(yi - event.y) < tolerance:
                        return k

        md = self.markupcontainer
        key = None
        for k, v in md.iteritems():
            if 'line' in k:
                if isinstance(v[0], list):
                    # this is a multi segment line
                    for pts in v[0]:
                        key = _get_key(pts, tolerance)
                        if key is not None:
                            break
                else:
                    key = _get_key(v, tolerance)
            elif 'rect' in k:
                pts = v[0]

                y1 = min(
                       pts[0][1],
                       pts[1][1],
                       )
                y2 = max(
                       pts[0][1],
                       pts[1][1],
                       )

                y = y1 <= event.y <= y2

                x1 = min(
                       pts[0][0],
                       pts[2][0],
                       )
                x2 = max(
                       pts[0][0],
                       pts[2][0],
                       )

                x = x1 <= event.x <= x2
                if x and y:
                    key = k


            if key is not None:
                break
        return key

    def _over_mark_up_point(self, event, line, tolerance=4):
        '''

        '''
        x = line[0][0]
        y = line[0][1]
        x2 = line[1][0]
        y2 = line[1][1]

        if abs(event.x - x) < tolerance and abs(event.y - y) < tolerance:
            return (x, y)
        elif abs(event.x - x2) < tolerance and abs(event.y - y2) < tolerance:
            return (x2, y2)

    def _get_line_parameters(self, x, y, x2, y2):
        '''

        '''
        try:
            m = float((y2 - y)) / (float(x2) - float(x))
            b = float(y) - m * float(x)
        except ZeroDivisionError:
            m = 'undefined'
            b = ''

        return m, b

    def _calc_adjustment(self, event):
        '''
        '''
        xs = self.temp_start_pos[0]
        ys = self.temp_start_pos[1]

        xadj = -xs + event.x
        yadj = -ys + event.y
        return xadj, yadj

#============= EOF ====================================
#    def mldraw_mouse_move(self,event):
#        self.ldraw_mouse_move(event)
#
#    def mldraw_left_down(self,event):
#        self.ldraw_left_down(event)
#    def _save(self, pdf = False):
#        if pdf:
#            #saving an image into a pdf is currently not working
#            from reportlab.pdfgen import canvas
#            pdf = canvas.Canvas('btest.pdf')
#            from kiva.backend_pdf import GraphicsContext
#            gc = GraphicsContext(pdf)
#            self.draw(gc)
#            gc.flush()
#            pdf.save()
#        else:
#            from kiva.backend_image import GraphicsContext as iGraphicsContext
#            s = (int(self.outer_width), int(self.outer_width))
#            s = (500, 500)
#            gc = iGraphicsContext(s)
#            self.draw(gc)
#            gc.save('bbtest.jpg')
