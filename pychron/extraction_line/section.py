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

#============= standard library imports ========================

#============= local library imports  ==========================
# from canvas.canvas3D.elements.components import Valve, Shaft
class Section(object):
    '''
        G{classtree}
    '''
#    components=['bone']
#    tests=dict(C=(10,'closed-static-dynamic'),
#           F=(1,'closed-static-gettering'),
#           H=(2,'closed-static-measuring')
#           )
    components = None
    tests = None
    cur_precedence = 0
    cur_state = None
    def __init__(self):
        '''
        '''
        self.components = []
        self.tests = {}
    def add_component(self, c):
        '''
            @type c: C{str}
            @param c:
        '''
        self.components.append(c)
    def add_test(self, tkey, test):
        '''
            test == tuple(precedence , test string)
            ex (10,'closed-static-dynamic')
        '''
        self.tests[tkey] = test
    def _update_other_valves(self, name, valves, state, sg):
        '''
            @type name: C{str}
            @param name:

            @type valves: C{str}
            @param valves:

            @type state: C{str}
            @param state:

            @type sg: C{str}
            @param sg:
        '''
        for vk in valves:
            v = sg.get_object_by_name(vk)
            if v is not None and v.state and v.name != name:
                for b in v.branches:
                    b.set_state(state, name)

    def update_state(self, action, valve, valves, gas_type, sg):
        '''
            @type action: C{str}
            @param action:

            @type valve: C{str}
            @param valve:

            @type valves: C{str}
            @param valves:

            @type gas_type: C{str}
            @param gas_type:

            @type sg: C{str}
            @param sg:
        '''


        # update the state based on the initial valve state change
        state, prec = self._update_state_(action, valve, sg)



        print action, valve.name, state, prec, self.cur_precedence, self.cur_state
        if action:
            # if the state change was to open the valve
            if prec is not None:
                # self.precedence_stack.append(prec)
                self.cur_precedence = prec

            v = sg.get_object_by_name(valve.name)
            if state is None:
                if v is not None:
                    for b in v.branches:
                        b.set_state(self.cur_state, valve.name)
            else:
                if gas_type is not None and state == 'measuring':
                    state = '_'.join((state, gas_type))
                # print state
                self.set_state(valve, state, sg)


                # update the state of any open valve
                self._update_other_valves(valve.name, valves, state, sg)
#                for vk in valves:
#                    v=sg.get_object_by_name(vk)
#                    if v is not None and v.state:
#                        for b in v.branches:
#                            b.set_state(state,valve.name)
#

        else:
            # the state change closed the valve so reset precedence to zero
            # and change our state to static
            # then run test on all other valves to see if a lower precedence is
            # applicable
            state = 'static'
            self.cur_precedence = 0


            # run all tests on all valves
            avalve = None
            for vk in valves:
                # exclude the initial valve
                if not vk == valve.name:
                    _s, prec = self._update_state_(action, valves[vk], sg)

                    if _s is not None and _s != 'static':
                        # a lower precedence test was found to be true
                        state = _s
                        # update our current precedence
                        self.cur_precedence = prec

                        # remember the valve
                        avalve = valves[vk]

            if avalve is not None:
                print avalve.name
                if gas_type is not None and state == 'measuring':
                    state = '_'.join((state, gas_type))
                self.set_state(avalve, state, sg)
                self.set_valve_high_side_state(valve, 'static', sg)
            else:
                self.set_state(valve, 'static', sg, low_side=False)


    def _update_state_(self, action, valve, sg):
        '''
            @type action: C{str}
            @param action:

            @type valve: C{str}
            @param valve:

            @type sg: C{str}
            @param sg:
        '''
        # need list of components to change
        # need a scene graph instance
        state = None
        precedence = None
        for t in self.tests:
            _precedence, test = self.tests[t]

            _state = self.run_test(t, test, valve)
            if _state is not None:
                if self.cur_precedence <= _precedence:
#                    if action:
#                        self.cur_precedence=precedence
#                        self.precedence_stack.append(precedence)
                    state = _state
                    precedence = _precedence



        return state, precedence

    def set_valve_high_side_state(self, valve, state, sg):
        '''
            @type valve: C{str}
            @param valve:

            @type state: C{str}
            @param state:

            @type sg: C{str}
            @param sg:
        '''
        c = sg.get_object_by_name(valve.name)

        if c is not None:
            c.high_side.set_state(state, valve.name)

    def set_state(self, valve, state, sg, low_side=True, high_side=True):
        '''
            @type valve: C{str}
            @param valve:

            @type state: C{str}
            @param state:

            @type sg: C{str}
            @param sg:

            @type low_side: C{str}
            @param low_side:

            @type high_side: C{str}
            @param high_side:
        '''
        self.cur_state = state
        if state is not None:

            for c in self.components:
                c = sg.get_object_by_name(c)

                c.set_state(state, valve.name)

            cvalve = sg.get_object_by_name(valve.name)
            if cvalve is not None:
    #            if not cvalve.state:
                ok = False
                for b in cvalve.branches:
                    if cvalve.low_side == b:
                        if low_side:
                            ok = True
                    elif cvalve.high_side == b:
                        if high_side:
                            ok = True
                    else:
                        ok = True

                    if ok:
                        b.set_state(state, valve.name)

                for c in cvalve.connections:
                    c.set_state(state, valve.name)



    def run_test(self, testkey, test, valve):
        '''
            @type testkey: C{str}
            @param testkey:

            @type test: C{str}
            @param test:

            @type valve: C{str}
            @param valve:
        '''

        test_state, true_outcome, false_outcome = test.split('-')
        if valve.name == testkey:
            test_state = True if test_state == 'open' else False
            if valve.state == test_state:
                return true_outcome
            else:
                return false_outcome
# class Section(object):
#    tests=None
#    components=None
#    valve_manager=None
#    scene_graph=None
#    precedence=0
#    def __init__(self):
#        self.tests=[]
#        self.components=[]
#    def add_test(self,c):
#        self.tests.append(c)
#
#    def test(self,action):
#
#        for t in self.tests:
#
#            vname,tstate,true_out,false_out=t.split('-')
#            v=self.scene_graph.get_object_by_name(vname)
#
#
#            tstate=True if tstate=='open' else False
#            vstate=self.valve_manager.get_valve_state_by_name(vname)
#            outcome = true_out if vstate==tstate else false_out
#
#
#            args=(outcome,action,self.precedence)
#            for b in v.branches:
#                b.set_state(*args)
#
#            for c in v.connections:
#                c.set_state(*args)
#
#            valves=[]
#            for c in self.components:
#              #  args=(outcome,action,self.precedence)
#                c=self.scene_graph.get_object_by_name(c)
#                if isinstance(c,Valve):
#                    valves.append(c)
#
#                else:
#                    noutcome,precedence=c.set_state(*args)
#                    #c.set_state(*args)
#
#            #print 'new out', noutcome,outcome,precedence
#            # args=(noutcome,action,precedence)
# #            for v in valves:
# #                if v.state:
# #                    for b in v.branches:
# #                        b.set_state(*args)
#
#

#============= EOF ====================================
