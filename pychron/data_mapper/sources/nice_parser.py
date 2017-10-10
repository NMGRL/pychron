# ===============================================================================
# Copyright 2017 ross
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
import re

from numpy import where

detregex = re.compile(r'^Mass\((?P<idx>\d)')


class NuBase:
    def __add__(self, other):
        if isinstance(other, NuBase):
            other = other.ys

        return self.__class__(self.xs, self.ys + other)
    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, NuBase):
            other = other.ys

        return self.__class__(self.xs, self.ys - other)

    def __rsub__(self, other):
        if isinstance(other, NuBase):
            other = other.ys
        return self.__class__(self.xs, other - self.ys)


class Zero(NuBase):
    def __init__(self, xs, ys):
        self.xs, self.ys = xs, ys.mean()


class Mass(NuBase):
    def __init__(self, xs, ys):
        self.xs, self.ys = xs, ys


class NiceParser():
    def __init__(self, signals):
        self._signals = signals
        self._tokens = []
        self._current = None

    def set_tokens(self, tokens):
        self._tokens = tokens
        self._current = tokens[0]

    def exp(self):

        mt = detregex.match(self._tokens[0])

        result = self.term()
        while self._current in ('+', '-'):
            if self._current == '+':
                self.next()

                result += self.term()

            if self._current == '-':
                self.next()
                result -= self.term()

        return result, mt.group('idx')

    def factor(self):
        result = None
        if self._current[0].isdigit() or self._current[-1].isdigit():
            result = float(self._current)
            self.next()
        elif self._current is '(':
            self.next()
            result = self.exp()
            self.next()
        elif self._current[:4] == 'Mass':
            result = generate_mass(*eval(self._current[4:]))(self._signals)
            result = Mass(*result)
            self.next()
        elif self._current[:4] == 'Zero':
            result = generate_zero(*eval(self._current[4:]))(self._signals)
            result = Zero(*result)
            self.next()

        return result

    def next(self):
        self._tokens = self._tokens[1:]
        self._current = self._tokens[0] if len(self._tokens) > 0 else None

    def term(self):
        result = self.factor()
        while self._current in ('*', '/'):
            if self._current == '*':
                self.next()
                result *= self.term()
            if self._current == '/':
                self.next()
                result /= self.term()
        return result


def _generate(m, n):
    def func(signals):
        ys = signals[:, n]
        xs = signals[:, -2]
        b = where(signals[:, -1] == m)[0]
        return xs[b], ys[b]

    return func


def generate_zero(m, n):
    return _generate(m, n)


def generate_mass(m, n):
    return _generate(100 + m, n)

# ============= EOF =============================================
