# ===============================================================================
# Copyright 2019 ross
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
import requests

access_token_cookie = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1NTEyMDk0ODgsIm5iZiI6MTU1MTIwOTQ4OCwianRpI' \
                      'joiMjE2OWJlZWUtMmIwYy00NjEwLTk2NTgtY2U5OGNiM2YxY2Y3IiwiZXhwIjoxNTUzODAxNDg4LCJpZGVudGl0eSI' \
                      '6Impyb3NzIiwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIn0.y4Hx7PVEWUvam9_rYLU0TB5Bg7myWDw10EK7z' \
                      'hwvyZY'


def get_samples():
    url = 'http://localhost:5002/api/v1/sample?all=True'
    response = requests.get(url, cookies={'access_token_cookie': access_token_cookie})
    if response.status_code == 200:
        return response.json()


if __name__ == '__main__':
    print(get_samples())
# ============= EOF =============================================
