# ===============================================================================
# Copyright 2021 ross
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
import json
from datetime import datetime
from json import JSONDecodeError
from pprint import pformat

import requests
from requests.exceptions import InvalidSchema, ConnectTimeout, ConnectionError
from traits.api import Str, Int
from apptools.preferences.preference_binding import bind_preference

from pychron.core.pychron_traits import HTTPStr
from pychron.experiment.utilities.identifier import is_step_heat
from pychron.loggable import Loggable


def sample_payload(sm):
    return {
        "name": sm.get("sample", "NoSample"),
        "note": sm.get("note"),
        "project": [{"name": sm.get("project", "NoProject")}],
        "material": sm.get("material", "NoMaterial"),
        "location": {
            "type": "Point",
            "coordinates": [
                float(sm.get("longitude", 0)),
                float(sm.get("latitude", 0)),
            ],
        },
    }


def instrument_payload(cm):
    return {"name": cm.get("instrument", "NoInstrument")}


def preferred_datum_factory(p):
    return {
        "type": {
            "parameter": p["attr"],
            "unit": p.get("unit", ""),
            "error_metric": p.get("error_kind"),
            "is_computed": True,
            "description": p.get("kind"),
        },
        "value": p["value"],
        "error": p["error"],
    }


def analyses_payload(ans, preferred_kinds):
    analyses = [
        {
            "is_bad": ai.get("tag", "ok").lower() == "invalid",
            "analysis_type": (
                "Step Heat" if is_step_heat(ai.get("record_id")) else "Fusion"
            ),
            "analysis_name": ai.get("record_id"),
            "uuid": ai.get("uuid"),
            "datum": [
                {
                    "type": {"parameter": "age", "unit": ai.get("age_units", "Ma")},
                    "value": ai.get("age", 0),
                    "error": ai.get("age_err", 0),
                },
                {
                    "type": {"parameter": "kca", "unit": ""},
                    "value": ai.get("kca", 0),
                    "error": ai.get("kca_err", 0),
                },
            ],
        }
        for ai in ans
    ]

    preferreds = [
        {
            "analysis_name": "preferred",
            "analysis_type": "Preferred",
            "datum": [preferred_datum_factory(p) for p in preferred_kinds],
        }
    ]

    pref = next((p for p in preferred_kinds if p["attr"] == "age"), {})
    page = pref.get("value", 0)
    perror = pref.get("error", 0)
    punit = pref.get("unit", "Ma")
    preferred_age = {
        "analysis_name": "PreferredAge",
        "analysis_type": "Preferred",
        "is_interpreted": True,
        "datum": [
            {
                "type": {"parameter": "age", "unit": punit},
                "value": page,
                "error": perror,
            }
        ],
    }
    analyses.extend(preferreds)
    analyses.append(preferred_age)
    return analyses


class SparrowClient(Loggable):
    """Thin http client used to interact with Sparrow API"""

    username = Str
    password = Str
    host = HTTPStr
    token = Str

    def __init__(self, bind=True, *args, **kw):
        super().__init__(*args, **kw)
        if bind:
            self.bind_preferences()

    def bind_preferences(self):
        prefid = "pychron.sparrow"
        for attr in ("username", "password", "host"):
            bind_preference(self, attr, "{}.{}".format(prefid, attr))

    def login(self):
        url = "{}/auth/login".format(self.base_url)
        res = requests.post(
            url, json={"username": self.username, "password": self.password}, timeout=3
        )
        try:
            token = res.json()["token"]
            self.token = token
            return True
        except KeyError:
            self.warning_dialog(
                "failed connecting to Sparrow. Check connection and username/password"
            )

    def insert_ia(self, path):
        with open(path, "r") as rfile:
            obj = json.load(rfile)
        # print(obj)
        sm = obj.get("sample_metadata")
        cm = obj.get("collection_metadata")
        ans = obj.get("analyses")
        pf = obj.get("preferred")

        # print(cm)
        session = {
            "sample": sample_payload(sm),
            "technique": "Ar/Ar Incremental Heating",
            "project": {"name": sm.get("project", "NoProject")},
            "date": datetime.now().isoformat(),
            "instrument": instrument_payload(cm),
            "analysis": analyses_payload(ans, pf["preferred_kinds"]),
            # 'datum': [datum_factory(p) for p in pf['preferred_kinds']]
        }
        self.debug(pformat(session))
        self.add_session(session)

        # self.add_project(sm)
        # self.add_material(sm)
        # self.add_sample(sm)

        # self.add_instrument(cm)
        # self.add_session()

    def add_instrument(self, cm):
        self._add("instrument", instrument_payload(cm))

    def add_sample(self, sm):
        self._add("sample", sample_payload(sm))

    def add_material(self, sm):
        payload = {"id": sm.get("material", "NoMaterial")}
        self._add("material", payload)

    def add_session(self, payload):
        self._add("session", payload)

    def add_project(self, sm):
        payload = {"name": sm.get("project", "NoProject")}
        self._add("project", payload)

    @property
    def base_url(self):
        return "{}:5002/api/v2".format(self.host)

    def test_api(self):
        try:
            resp = requests.get(self.base_url, timeout=3)
            self.debug("test api. {}".format(resp.text))
            return resp.status_code == 200
        except (ConnectTimeout, InvalidSchema, ConnectionError) as e:
            self.warning(e)
            return False

    def _add(self, tag, payload):
        if not self.token:
            self.login()

        url = "{}/import-data/models/{}".format(self.base_url, tag)
        resp = requests.put(
            url, headers={"Authorization": self.token}, json={"data": payload}
        )
        # print(resp, resp.status_code)
        if resp.status_code != 201:
            print(url)
            print(resp, resp.text)


if __name__ == "__main__":
    s = SparrowClient(host="http://129.138.12.35", bind=False)

    s.add_project({"project": "TestProject"})
    # s.add_session('')

    # p = '/Users/ross/Desktop/14_00000.ia.json'
    # s.insert_ia(p)
# ============= EOF =============================================
