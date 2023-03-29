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
import csv
from itertools import groupby

from sqlalchemy import func, extract, cast, Date

from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.dvc.dvc_orm import (
    AnalysisTbl,
    IrradiationPositionTbl,
    LevelTbl,
    IrradiationTbl,
    SampleTbl,
    ProjectTbl,
    MaterialTbl,
    AnalysisChangeTbl,
)
from pychron.dvc.fix import get_dvc

ANALYSIS_HEADER = [
    "sample",
    "project",
    "irradiation",
    "identifier",
    "runid",
    "timestamp",
]
SAMPLE_HEADER = [
    "sample",
    "material",
    "project",
    "pi",
    "irradiation",
    "irradiation_info",
    "identifier",
    "latitude",
    "longitude",
]


def make_sample_row(record):
    ip = record.irradiation_position
    sample = ip.sample
    row = [
        sample.name,
        sample.material.name,
        sample.project.name,
        sample.project.principal_investigator.name,
        ip.level.irradiation.name,
        record.irradiation_info,
        ip.identifier,
        sample.lat,
        sample.lon,
    ]
    return row


def make_analysis_row(record):
    ip = record.irradiation_position
    sample = ip.sample
    row = [
        sample.name,
        sample.project.name,
        ip.level.irradiation.name,
        ip.identifier,
        record.record_id,
        record.timestamp,
    ]
    return row


def make_report():
    dvc = get_dvc(host="129.138.12.160", username="jross", password="argon4039")
    dvc.connect()
    with dvc.session_ctx() as sess:
        make_yearly_report(sess, 2021)


def make_yearly_report(sess, year):
    q = sess.query(AnalysisTbl)
    q = q.join(AnalysisChangeTbl)
    q = q.join(IrradiationPositionTbl)
    q = q.join(LevelTbl)
    q = q.join(IrradiationTbl)
    q = q.join(SampleTbl)
    q = q.join(MaterialTbl)
    q = q.join(ProjectTbl)

    q = q.filter(ProjectTbl.name.notin_(["REFERENCES", "CorrectionFactors"]))
    q = q.filter(ProjectTbl.name.notlike("Irradiation%"))
    q = q.filter(extract("year", cast(AnalysisTbl.timestamp, Date)) == year)
    q = q.filter(AnalysisChangeTbl.tag != "invalid")
    q = q.order_by(AnalysisTbl.timestamp.desc())

    records = q.all()

    # with open(f'samples.{year}.csv', 'w') as wfile:
    #     writer = csv.writer(wfile)
    #     writer.writerow(SAMPLE_HEADER)
    #
    #     grecords = groupby(sorted(records, key=lambda x: x.sample),
    #                        key=lambda xi: xi.sample)
    #     srows = [next(rs) for (s, rs) in grecords]
    #
    #     for i, r in enumerate(sorted(srows, key=lambda x: x.project)):
    #         print(f'writing sample {i}')
    #         writer.writerow(make_sample_row(r))

    with open(f"analysis.{year}.csv", "w") as wfile:
        writer = csv.writer(wfile)
        writer.writerow(ANALYSIS_HEADER)
        for i, ri in enumerate(records):
            print(f"writing analysis {i}")
            writer.writerow(make_analysis_row(ri))


if __name__ == "__main__":
    make_report()
# ============= EOF =============================================
