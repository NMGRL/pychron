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
import io
import os

from PIL import Image, UnidentifiedImageError
from PIL.Image import frombytes
from numpy import array, loadtxt, column_stack, frombuffer, fromstring
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String, Float, TEXT, BLOB, ForeignKey
from sqlalchemy.orm import relationship

from pychron.core.helpers.logger_setup import logging_setup
from pychron.database.core.base_orm import BaseMixin
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.image.cv_wrapper import grayspace
from pychron.paths import paths

Base = declarative_base()

LABEL_MAP = dict(good=0, bad=1, empty=2, multigrain=3, contaminant=4, blurry=5)


class LabelTbl(Base, BaseMixin):
    name = Column(String)

class LabelsTbl(Base, BaseMixin):
    sample_id = Column(Integer, ForeignKey('SampleTbl.id'))
    label_id = Column(Integer, ForeignKey('LabelTbl.id'))

    sample = relationship('SampleTbl', uselist=False)
    label = relationship('LabelTbl', uselist=False)

class SampleTbl(Base, BaseMixin):
    blob = Column(BLOB)
    name = Column(String)

class TrayDB(DatabaseAdapter):
    def __init__(self, *args, **kw):
        super(TrayDB, self).__init__(*args, **kw)
        self.kind = "sqlite"
        if not self.path:
            self.path = os.path.join(paths.hidden_dir, "traydb.db")

    def build_database(self):
        self.connect(test=False)
        if not os.path.isfile(self.path):
            with self.session_ctx() as sess:
                Base.metadata.create_all(bind=sess.bind)

        with self.session_ctx():
            for i, l in enumerate(('good', 'bad', 'empty', 'multigrain', 'contaminant', 'blurry')):
                dbl = LabelTbl(id=i, name=l)
                self._add_unique(dbl, 'label', l)

    def get_label(self, lname):
        with self.session_ctx() as sess:
            q = sess.query(LabelTbl)
            q = q.filter(LabelTbl.name==lname)
            return q.one()

    def add_labeled_sample(self, name, frame, label):
        # if not isinstance(sample, bytes):
        #     sample = sample.tobytes()
        sample = grayspace(frame).flatten().tobytes()
        dbsam = SampleTbl(name=name,
                          blob=sample)
        dbl = self.get_label(label)

        ls = LabelsTbl(sample=dbsam,
                       label=dbl)

        self.add_item(dbsam)
        self.add_item(ls)
    def get_sample_labels(self):
        with self.session_ctx() as sess:
            q = sess.query(LabelsTbl)
            labels = []
            samples = []
            names = []
            for record in q.all():
                label = record.label
                sample = record.sample.blob
                sample = frombuffer(sample)
                samples.append(sample)
                labels.append(label.id)
                names.append(record.sample.name)

            if labels:
                return names, array(samples), array(labels)

def load_test_data():
    d = TrayDB(path='/Users/ross/Sandbox/loadimages/db.sqlite')
    d.build_database()
    with d.session_ctx():

        for tag in ('blurry', 'empty'):
            root = f'/Users/ross/Sandbox/loadimages/421{tag}'
            for f in os.listdir(root):

                p = os.path.join(root, f)
                try:
                    img = Image.open(p)
                except UnidentifiedImageError:
                    continue
                d.add_labeled_sample(p, array(img), tag)


if __name__ == '__main__':
    paths.build('~/PychronDev')
    logging_setup('traydb')
    load_test_data()
# ============= EOF =============================================
