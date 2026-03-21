# ===============================================================================
# Copyright 2020 ross
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
from pychron.dvc.dvc_orm import AnalysisTbl
from pychron.dvc.dvc_helper import get_dvc

DRY = False


def get_analysis(dvc, runid):
    args = runid.split("-")
    idn, aliquot = "-".join(args[:-1]), args[-1]
    return dvc.get_analysis_runid(idn, aliquot)


def fix_load(dvc, sess, load, ms):
    start_dban = get_analysis(dvc, load["start"])
    end_dban = get_analysis(dvc, load["end"])

    # add the new load
    load_name = load["load"]
    if not DRY:
        dvc.add_load(load_name, load["holder"], "NMGRL")

    # get all analyses between start and end inclusive
    q = sess.query(AnalysisTbl)

    print("starttime", load["start"], start_dban.timestamp)
    print("endtime", load["end"], end_dban.timestamp)

    q = q.filter(AnalysisTbl.timestamp >= start_dban.timestamp)
    q = q.filter(AnalysisTbl.timestamp <= end_dban.timestamp)
    q = q.filter(AnalysisTbl.mass_spectrometer == ms)
    print("n analyses", len(q.all()))
    for i, a in enumerate(q.all()):
        print(
            "added measured position for {},{},{}".format(
                load_name, i, a.id, a.timestamp
            )
        )
        # add new measured position
        if not DRY:
            dvc.add_measured_position(a, load=load_name)


def main():
    ms = "jan"
    loads = (
        {
            "load": "C0185",
            "start": "ba-02-J-1507",
            "end": "a-02-J-3080",
            "holder": "221-hole",
        },
        {
            "load": "C0186",
            "start": "ba-02-J-1509",
            "end": "c-03-J-2536",
            "holder": "221-hole",
        },
        {
            "load": "C0187",
            "start": "bu-FC-J-13279",
            "end": "a-02-J-3095",
            "holder": "221-hole",
        },
        {
            "load": "C0188",
            "start": "ba-03-J-05",
            "end": "c-03-J-2542",
            "holder": "221-hole",
        },
        {
            "load": "C0189",
            "start": "bu-FC-J-13289",
            "end": "c-03-J-2547",
            "holder": "221-hole",
        },
    )

    dvc = get_dvc()
    dvc.connect()

    for l in loads:
        with dvc.session_ctx() as sess:
            fix_load(dvc, sess, l, ms)


if __name__ == "__main__":
    main()
# ============= EOF =============================================
