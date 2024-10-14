# ===============================================================================
# Copyright 2024 Jake Ross
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
from traits.api import Instance, Button, File, Str
from pychron.loggable import Loggable
from traitsui.api import View, UItem, Item


class UploadDatabase(Loggable):
    dvc = Instance("pychron.dvc.dvc.DVC")

    upload = Button("Upload")
    path = File
    # path = File('/Users/jross/dumps/_localhost_pychrondvc_2024_04_24_14_08_29.sql')
    # path = File('/Users/jross/dumps/_localhost_pychrondvc_2024_04_24_14_24_04.sql')
    database_name = Str("pychrondvc")

    def _upload_fired(self):
        # get dvc connection info
        # and make sure its a localhost connection

        host = self.dvc.data_source.host
        user = self.dvc.data_source.username
        password = self.dvc.data_source.password
        kind = self.dvc.data_source.kind

        if host != "localhost":
            self.warning_dialog("Database must be localhost")
            return
        if kind != "mysql":
            self.warning_dialog("Database must be mysql")
            return

        import pymysql

        conn = pymysql.connect(
            host=host,
            port=3306,
            user=user,
            connect_timeout=0.25,
            passwd=password,
        )
        cur = conn.cursor()
        # check if the database exists
        if self._schema_exists(conn, self.database_name):
            if not self.confirmation_dialog(
                f'Database "{self.database_name}" already exists. Do you want to overwrite it and continue?'
            ):
                self.information_dialog("Database upload canceled")
                return
            # drop the database
            cur.execute(f"DROP DATABASE {self.database_name}")

        # create the database
        cur.execute(f"CREATE DATABASE {self.database_name}")

        # upload the database
        with open(self.path, "r") as rfile:
            cur.execute(f"USE {self.database_name};")
            lines = rfile.read().split(";\n")
            self.debug("upload started")
            for i, line in enumerate(lines):
                cur.execute(line)
            self.debug("upload finished")

        cur.close()

        preferences = self.application.preferences
        prefid = "pychron.dvc.connection"

        favorites = preferences.get(f"{prefid}.favorites")
        favorites = favorites.strip()[1:-1].split(", ")

        for fav in favorites:
            args = fav.split(",")
            if args[4].strip() == self.database_name:
                break
        else:
            # find the enabled connection localhost connection
            idx = None
            args = None
            for i, fav in enumerate(favorites):
                args = fav.split(",")
                if args[1] == "mysql" and args[3] == "localhost":
                    idx = i
                    break

            if args and idx is not None:
                args[0] = f"'{self.database_name}"
                args[4] = self.database_name
                favorites.append(",".join(args))
            favorites = [f[1:-1] for f in favorites]

            preferences.set(f"{prefid}.favorites", favorites)
            preferences.save()

        self.information_dialog("Database upload complete!")

    def _schema_exists(self, conn, schema):
        cur = conn.cursor()
        cur.execute(f"SHOW DATABASES LIKE '{schema}'")
        return bool(cur.fetchall())

    def traits_view(self):
        return View(
            Item("database_name", label="Database Name"),
            Item("path", label="Select a Database File"),
            UItem("upload", enabled_when="path"),
            resizable=True,
            width=500,
            buttons=[],
            title="Database Upload",
        )


if __name__ == "__main__":
    u = UploadDatabase()
    u.configure_traits()
# ============= EOF =============================================
