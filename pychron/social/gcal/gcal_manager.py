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
import httplib2
from apptools.preferences.preference_binding import bind_preference
from googleapiclient import discovery
from oauth2client.file import Storage
from traits.api import Str

from pychron.loggable import Loggable


class GCalManager(Loggable):
    credentials_path = Str
    calendar = Str

    def __init__(self, bind=True, *args, **kw):
        super(GCalManager, self).__init__(*args, **kw)
        if bind:
            self.bind_preferences()

    def bind_preferences(self):
        prefid = 'pychron.gcal'
        # bind_preference(self, 'username', '{}.username'.format(prefid))
        # bind_preference(self, 'password', '{}.password'.format(prefid))
        bind_preference(self, 'calendar', '{}.calendar'.format(prefid))
        bind_preference(self, 'credentials_path', '{}.credentials_path'.format(prefid))

    def post_event(self, description, start, end):
        s = self.get_service()
        events = s.events()
        body = self._get_body(description, start, end)
        event = events.insert(calendarId=cal_id, body=body)
        event.execute()

    def get_calendars(self):
        service = self.get_service()
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                print calendar_list_entry['summary']
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    def get_service(self):
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        return service

    def _get_credentials(self):
        store = Storage(self.credentials_path)
        credentials = store.get()
        # if not credentials or credentials.invalid:
        #     flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        #     flow.user_agent = APPLICATION_NAME
        #     if flags:
        #         credentials = tools.run_flow(flow, store, flags)
        #     else:  # Needed only for compatibility with Python 2.6
        #         credentials = tools.run(flow, store)
        #     print('Storing credentials to ' + credential_path)
        return credentials

    def _get_body(self, description, start, end):
        return {'summary': 'Pychron Event',
                'description': description,
                'start': {'dateTime': start},
                'end': {'dateTime': end},
                }


if __name__ == '__main__':
    g = GCalManager(bind=False)
    g.credentials_path = '/Users/ross/Pychron_dev/setupfiles/client_secret.json'
    g.get_calendars()
    # g.post_event()
# ============= EOF =============================================
