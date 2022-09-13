# ===============================================================================
# Copyright 2022 ross
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
import unittest

from pychron.dvc import prep_repo_name

FOOBAR = "Foo-Bar"


class RepoNameTestCase(unittest.TestCase):
    def test_repo_comma(self):
        name = "Foo,Bar"
        self.assertEqual(prep_repo_name(name), "Foo-Bar")

    def test_repo_slash(self):
        name = "Foo/Bar"
        self.assertEqual(prep_repo_name(name), "FooBar")

    def test_repo_space(self):
        name = "Foo Bar"
        self.assertEqual(prep_repo_name(name), "FooBar")

    def test_repo_underscore(self):
        name = "Foo_Bar"
        self.assertEqual(prep_repo_name(name), "FooBar")

    def test_repo_special_character(self):
        name = "Foo&Bar"
        self.assertEqual(prep_repo_name(name), "Foo-Bar")

    def test_repo_special_character2(self):
        name = "&Foo>Bar$"
        self.assertEqual(prep_repo_name(name), "-Foo-Bar-")


# ============= EOF =============================================
