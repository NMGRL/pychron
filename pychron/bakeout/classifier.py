#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, Property, Str
from traitsui.api import View, Item, TableEditor
from pychron.loggable import Loggable
#============= standard library imports ========================
import os
import numpy as np
#============= local library imports  ==========================
from pychron.paths import paths

class Classifier(Loggable):
    training_data_path = Property
    def _get_training_data_path(self):
        p = os.path.join(paths.hidden_dir, 'bakeout_training_data.npz')
        return p

    def assemble_observation(self, gxs, gys, gps):
        self.info('assembling observation')
        observation = []
        for i, (xs, ys, ps) in enumerate(zip(gxs, gys, gps)):
            obs_i = self._assemble_observation(xs, ys, ps)
            if obs_i is not None:
                observation.extend((i,))
                observation.extend(obs_i)
        return np.asarray(observation)

    def add_to_training_data(self, gxs, gys, gps, classification):
        '''
            gxs=list of xs for each controller
            
        '''
        self.info('adding training data. classified as {}'.format(classification))
        X, y = self.get_training_data()
        observation = self.assemble_observation(gxs, gys, gps)
        X = np.hstack((X, observation))
        y = np.hstack((y, int(classification)))

        p = self.training_data_path
        np.savez(p, X=X, y=y)

    def _assemble_observation(self, xs, ys, ps):
        '''
            xs= time
            ys= temp
            ps= power
            
            observation_i=[total_time, 
            max rise rate for 10s window, time of max rise rate, 
            min rise rate for 10s window, time of min rise rate, 
            max avg temp for 10s window, time of max temp
            min avg temp for 10s window, time of min temp,
            max avg power for 10s window, time of max power
            min avg power for 10s window, time of min power
            ]
        '''
        if len(xs) > 10:
            return

        xs, ys = np.asarray(xs), np.asarray(ys)
        total_time = xs[-1] - xs[0]

        # calculate rise rate for 10s window
        window = [-1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        rise_rates = abs(np.convolve(ys, window, mode='same') / np.convolve(xs, window, mode='same'))

        max_rise_rate = max(rise_rates)
        tmax_rise_rate = self._get_tmax(xs, rise_rates)

        min_rise_rate = min(rise_rates)
        tmin_rise_rate = self._get_tmin(xs, rise_rates)


        window = np.ones(10) / float(10)
        avg_temps = np.convolve(ys, window, mode='same')
        avg_powers = np.convolve(ps, window, mode='same')

        max_temp = max(avg_temps)
        tmax_temp = self._get_tmax(xs, avg_temps)

        min_temp = min(avg_temps)
        tmin_temp = self._get_tmin(xs, avg_temps)

        max_power = max(avg_temps)
        tmax_power = self._get_tmax(xs, avg_powers)

        min_power = min(avg_powers)
        tmin_power = self._get_tmin(xs, avg_powers)

        observation_i = [total_time,
                       max_rise_rate, tmax_rise_rate,
                       min_rise_rate, tmin_rise_rate,
                       max_temp, tmax_temp,
                       min_temp, tmin_temp,
                       max_power, tmax_power,
                       min_power, tmin_power,
                       ]
        return observation_i

    def _get_tmax(self, xs, ns):
        try:
            a = xs[np.argmax(ns)]
        except IndexError:
            a = xs[-1]
        return a

    def _get_tmin(self, xs, ns):
        try:
            a = xs[np.argmin(ns)]
        except IndexError:
            a = xs[-1]
        return a

    def get_training_data(self):

        '''
        '''
        p = self.training_data_path
        if os.path.isfile(p):
            archive = np.load(p)

            X = archive['X']
            y = archive['y']
        else:
            X = np.array([])
            y = np.array([])
        return X, y

    def knn_classify(self, observation):
        '''
            X is the observations
            y is the classification
            X= n by m array where n is the number of observations and m is the number of parameters
            y= 1d array of integers
            
            0=failed bake
            1=successful bake
        '''
        from sklearn.neighbors import KNeighborsClassifier

        X, y = self.get_training_data()
        knn = KNeighborsClassifier()

        # fit the classifier with the training data
        knn.fit(X, y)

        classification = knn.predict(observation)
        return classification

    def sv_classify(self, observation):
        from sklearn import svm

        X, y = self.get_training_data()

        svc = svm.SVC()
        svc.fit(X, y)

        classification = svc.predict(observation)
        return classification

#============= EOF =============================================
