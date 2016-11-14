# ===============================================================================
# Copyright 2016 ross
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

# ============= enthought library imports =======================
import os
from datetime import datetime, timedelta

import httplib2
from apptools.preferences.preference_binding import bind_preference
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from traits.api import Str
from tzlocal import get_localzone

from pychron.loggable import Loggable
from pychron.paths import paths

SCOPES = 'https://www.googleapis.com/auth/calendar'
APPLICATION_NAME = 'Pychron'
TZ = get_localzone().zone


class GoogleCalendarClient(Loggable):
    client_secret_path = Str
    calendar = Str
    _active_event_id = None

    def __init__(self, bind=True, *args, **kw):
        super(GoogleCalendarClient, self).__init__(*args, **kw)
        if bind:
            self.bind_preferences()

    def bind_preferences(self):
        prefid = 'pychron.google_calendar'
        bind_preference(self, 'calendar', '{}.calendar'.format(prefid))
        bind_preference(self, 'client_secret_path', '{}.client_secret_path'.format(prefid))

    def post_event(self, summary, description, end, start=None, calendar=None):
        if calendar is None:
            calendar = self.calendar

        self.debug('Post event to {}'.format(calendar))
        self.debug('summary: {}'.format(summary))
        self.debug('description: {}'.format(description))
        self.debug('start: {}'.format(start))
        self.debug('end: {}'.format(end))

        cal = self.get_calendar(calendar)
        events = self._get_events()

        body = self._get_body(summary, description, start, end)
        request = events.insert(calendarId=cal['id'], body=body)
        try:
            event = request.execute()
        except HttpError, e:
            self.warning_dialog('Failed to post event. Exception: {}'.format(e))
            return

        self.debug('Post event resp: {}'.format(event['created']))
        self._active_event_id = event.get('id')
        self.debug('active event= {}'.format(self._active_event_id))

    def edit_event(self, event_info, end=None, calendar=None, event_id=None):
        if calendar is None:
            calendar = self.calendar

        if event_id is None:
            event_id = self._active_event_id

        if event_id is not None:
            events = self._get_events()
            cid = self._get_calendar_id(calendar)
            request = events.get(calendarId=cid, eventId=event_id)

            try:
                body = request.execute()
            except HttpError, e:
                self.warning_dialog('Failed to get event. Exception: {}'.format(e))
                return

            body.update(**event_info)

            if end == 'now':
                body['end'] = {'dateTime': datetime.now().isoformat(),
                               'timeZone': TZ}

            request = events.update(calendarId=cid, eventId=event_id, body=body)

            try:
                resp = request.execute()
            except HttpError, e:
                self.warning_dialog('Failed to edit event. Exception: {}'.format(e))
                return

            self.debug('Edit event resp:{}'.format(resp['updated']))
        else:
            self.warning_dialog('Invalid event id. Cannot edit event')

    def _get_events(self):
        service = self.get_service()
        events = service.events()
        return events

    def _get_calendar_id(self, calendar):
        cal = self.get_calendar(calendar)
        return cal['id']

    def get_calendars(self):
        service = self.get_service()
        page_token = None
        cals = []
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            cals.extend((calendar_list_entry for calendar_list_entry in calendar_list['items']))
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        return cals

    def print_calendar_names(self):
        for c in self.get_calendars():
            print c['summary']

    def get_calendar(self, name):
        cal_objs = self.get_calendars()
        return next((c for c in cal_objs if c['summary'] == name), None)

    def get_service(self):
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        return service

    def _get_credentials(self, flags=None):
        store = Storage(os.path.join(paths.appdata_dir, 'google_api_credentials.json'))
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_path, SCOPES)
            flow.user_agent = APPLICATION_NAME
            credentials = tools.run_flow(flow, store, flags)

        return credentials

    def _get_body(self, summary, description, start, end):
        if start is None:
            start = datetime.now()

        if isinstance(start, datetime):
            start = start.isoformat()
        if isinstance(end, datetime):
            end = end.isoformat()

        return {'summary': summary,
                'description': description,
                'start': {'dateTime': start,
                          'timeZone': TZ},
                'end': {'dateTime': end,
                        'timeZone': TZ}}


if __name__ == '__main__':
    paths.build('_dev')
    g = GoogleCalendarClient(bind=False)
    g.credentials_path = '/Users/ross/Pychron_dev/setupfiles/argonlab_credentials.json'
    g.client_secret_path = '/Users/ross/Pychron_dev/setupfiles/client_secret.json'

    s = datetime.now()
    e = s + timedelta(hours=1)
    # g.post_event('Test Event', 'description foobar', e.isoformat(),
    #              calendar='test')
    # g.print_calendar_names()
    g.edit_event({'description': 'asdfascewqasd21341234'},
                 end='now',
                 event_id='', calendar='test')
# ============= EOF =============================================
