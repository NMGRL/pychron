# ===============================================================================
# Copyright 2023 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os
import time
import yaml
import bezier
from matplotlib import pyplot as plt
from numpy import array, linspace

from pychron.core.yaml import yload
from pychron.hardware.actuators.gp_actuator import GPActuator
from pychron.paths import paths


class U2351A(GPActuator):
    """

    valve_actuation_config.yaml example

       ValveA:
         open:
           control_points:
            - 0.0,0
            - 0.5,5
            - 1.0,5
           nsteps: 50
           step_delay: 1
         close:
           control_points:
            - 0.0,5
            - 0.5,0
            - 1.0,0
           nsteps: 50
           step_delay: 1
       ValveB:
         open:
           control_points:
            - 0.0,0
            - 0.5,5
            - 1.0,5
           nsteps: 50
           step_delay: 1
         close:
           control_points:
            - 0.0,5
            - 0.5,0
            - 1.0,0
           nsteps: 50
           step_delay: 1
       """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._actuation_config_path = os.path.join(
            paths.device_dir, "valve_actuation_config.yaml"
        )

    def _actuate(self, obj, action):
        addr = obj.address
        state = action.lower() == "open"
        print("actuate. write digital out {} {}".format(addr, state))

        stepobj = self._get_actuation_steps(obj.name)
        if stepobj:
            n = stepobj['nsteps']
            step_delay = stepobj['step_delay']
            steps = self._generate_voltage_steps(stepobj[state])

            self.debug(f"ramping voltage nsteps={n}, step_delay={step_delay}")
            for i, step in enumerate(steps):
                self.debug(f'step {i + 1}/{n} {step}')
                self.ask(f'SOUR:VOLT {step}, (@{addr})')
                time.sleep(step_delay)
        else:
            v = 5 if state else 0
            self.ask(f'SOUR:VOLT {v},(@{addr})')
        return True

    def _generate_voltage_steps(self, obj):
        nodes = array([p.split(',') for p in obj['control_points']], dtype=float).T
        curve = bezier.Curve(nodes, degree=2)
        if obj.get('along_path', False):
            steps = [curve.evaluate(ni)[1][0] for ni in linspace(0.0, 1.0, obj['nsteps'])]
        else:
            ma = nodes.max()
            steps = []
            for i in linspace(0.0, 1.0, obj['nsteps']):
                curve2 = bezier.Curve([[i, i], [0, ma]], degree=1)
                intersections = curve.intersect(curve2)
                output = curve.evaluate_multi(intersections[0, :])[1][0]
                steps.append(output)

        return steps

    def _get_actuation_config(self, name):
        if os.path.isfile(self._actuation_config_path):
            with open(self._actuation_config_path, "r") as wfile:
                obj = yload(wfile)
                return obj.get(name)


if __name__ == '__main__':
    cfg = '''
A:  
 open:
   control_points:
    - 0.0,0
    - 0.5,5
    - 1.0,5
   nsteps: 50
   step_delay: 1
   degree: 2
 close:
   control_points:
    - 0.0,5
    - 0.5,0
    - 0.5,2.5
    - 1.0,0
   nsteps: 50
   step_delay: 1
   degree: 3

'''
    ym = yaml.safe_load(cfg)
    obj = ym['A']['close']
    nodes = array([p.split(',') for p in obj['control_points']], dtype=float).T
    print(nodes)
    curve = bezier.Curve(nodes, degree=obj.get('degree', 1))
    xs, ys = [], []
    xs2, ys2 = [], []
    xs3,ys3 = [],[]
    ma = nodes.max()
    for i in linspace(0.0, 1.0, obj['nsteps']):
        vs = curve.evaluate(i)

        xs.append(vs[0][0])
        ys.append(vs[1][0])
        nodes2 = [[i,i], [0, ma]]
        curve2 = bezier.Curve(nodes2, degree=1)
        print(nodes2, curve2)
        intersections = curve.intersect(curve2)
        print(intersections)
        # xs2.append(intersections[0][0])
        # ys2.append(intersections[1][0]*ma)

        s_vals = intersections[0, :]
        a = curve.evaluate_multi(s_vals)

        xs3.append(a[0][0])
        ys3.append(a[1][0])


    # print(xs)
    plt.scatter(xs, ys)
    plt.scatter(xs2, ys2)
    plt.scatter(xs3, ys3)
    plt.show()
# ============= EOF =============================================
