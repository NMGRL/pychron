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
import hashlib
import os
import webbrowser
import wsgiref
from base64 import urlsafe_b64encode
from random import SystemRandom
from string import ascii_letters, digits
from wsgiref.simple_server import WSGIRequestHandler
import requests_oauthlib

from pychron.globals import globalv


class _RedirectWSGIApp(object):
    """WSGI app to handle the authorization redirect.

    Stores the request URI and displays the given success message.
    """

    def __init__(self, success_message):
        """
        Args:
            success_message (str): The message to display in the web browser
                the authorization flow is complete.
        """
        self.last_request_uri = None
        self._success_message = success_message

    def __call__(self, environ, start_response):
        """WSGI Callable.

        Args:
            environ (Mapping[str, Any]): The WSGI environment.
            start_response (Callable[str, list]): The WSGI start_response
                callable.

        Returns:
            Iterable[bytes]: The response body.
        """
        start_response("200 OK", [("Content-type", "text/plain; charset=utf-8")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]


class InstalledAppFlow(object):
    autogenerate_code_verifier = None
    code_verifier = None

    def flow(self, config, scopes, **kw):
        # Credentials you get from registering a new application
        self.client_config = config
        self.oauth2session = requests_oauthlib.OAuth2Session(
            client_id=config["client_id"], scope=scopes, **kw
        )
        return self.run_local_server()

    def authorization_url(self, **kwargs):
        """Generates an authorization URL.

        This is the first step in the OAuth 2.0 Authorization Flow. The user's
        browser should be redirected to the returned URL.

        This method calls
        :meth:`requests_oauthlib.OAuth2Session.authorization_url`
        and specifies the client configuration's authorization URI (usually
        Google's authorization server) and specifies that "offline" access is
        desired. This is required in order to obtain a refresh token.

        Args:
            kwargs: Additional arguments passed through to
                :meth:`requests_oauthlib.OAuth2Session.authorization_url`

        Returns:
            Tuple[str, str]: The generated authorization URL and state. The
                user must visit the URL to complete the flow. The state is used
                when completing the flow to verify that the request originated
                from your application. If your application is using a different
                :class:`Flow` instance to obtain the token, you will need to
                specify the ``state`` when constructing the :class:`Flow`.
        """
        kwargs.setdefault("access_type", "offline")
        # if self.autogenerate_code_verifier:
        #     chars = ascii_letters + digits + "-._~"
        #     rnd = SystemRandom()
        #     random_verifier = [rnd.choice(chars) for _ in range(0, 128)]
        #     self.code_verifier = "".join(random_verifier)
        #
        # if self.code_verifier:
        #     code_hash = hashlib.sha256()
        #     code_hash.update(str.encode(self.code_verifier))
        #     unencoded_challenge = code_hash.digest()
        #     b64_challenge = urlsafe_b64encode(unencoded_challenge)
        #     code_challenge = b64_challenge.decode().split("=")[0]
        #     kwargs.setdefault("code_challenge", code_challenge)
        #     kwargs.setdefault("code_challenge_method", "S256")
        url, state = self.oauth2session.authorization_url(
            self.client_config["auth_uri"], **kwargs
        )

        return url, state

    def run_local_server(
        self,
        host="localhost",
        bind_addr=None,
        port=8080,
        authorization_prompt_message="",
        success_message="The authentication flow has completed. You may close this window.",
        open_browser=True,
        redirect_uri_trailing_slash=True,
        **kwargs
    ):
        wsgi_app = _RedirectWSGIApp(success_message)
        # Fail fast if the address is occupied
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False

        local_server = wsgiref.simple_server.make_server(
            bind_addr or host, port, wsgi_app, handler_class=WSGIRequestHandler
        )

        redirect_uri_format = (
            "http://{}:{}/" if redirect_uri_trailing_slash else "http://{}:{}"
        )
        self.redirect_uri = redirect_uri_format.format(host, local_server.server_port)
        auth_url, _ = self.authorization_url(**kwargs)

        if open_browser:
            webbrowser.open(auth_url, new=1, autoraise=True)

        print(authorization_prompt_message.format(url=auth_url))

        local_server.handle_request()

        # Note: using https here because oauthlib is very picky that
        # OAuth 2.0 should only occur over https.
        authorization_response = wsgi_app.last_request_uri.replace("http", "https")
        token = self.fetch_token(authorization_response=authorization_response)

        # This closes the socket
        local_server.server_close()
        return token

        # # Get the authorization verifier code from the callback url
        # redirect_response = input('Paste the full redirect URL here:')
        #
        # # Fetch the access token
        # github.fetch_token(token_url, client_secret=client_secret,
        #                    authorization_response=redirect_response)
        #
        # # Fetch a protected resource, i.e. user profile
        # r = github.get('https://api.github.com/user')
        # print(r.content)

    def fetch_token(self, **kwargs):
        """Completes the Authorization Flow and obtains an access token.

        This is the final step in the OAuth 2.0 Authorization Flow. This is
        called after the user consents.

        This method calls
        :meth:`requests_oauthlib.OAuth2Session.fetch_token`
        and specifies the client configuration's token URI (usually Google's
        token server).

        Args:
            kwargs: Arguments passed through to
                :meth:`requests_oauthlib.OAuth2Session.fetch_token`. At least
                one of ``code`` or ``authorization_response`` must be
                specified.

        Returns:
            Mapping[str, str]: The obtained tokens. Typically, you will not use
                return value of this function and instead and use
                :meth:`credentials` to obtain a
                :class:`~google.auth.credentials.Credentials` instance.
        """
        kwargs["verify"] = globalv.verify_ssl
        if globalv.cert_file and os.path.isfile(globalv.cert_file):
            kwargs["cert"] = globalv.cert_file

        kwargs.setdefault("client_secret", self.client_config["client_secret"])
        return self.oauth2session.fetch_token(self.client_config["token_uri"], **kwargs)


if __name__ == "__main__":
    a = InstalledAppFlow()
    config = {
        "client_id": "05317d25974cd74eba4e",
        "client_secret": "be1fec163f573bfba2aea8dbd8b0452dad28bf95",
        "auth_uri": "https://github.com/login/oauth/authorize",
        "token_uri": "https://github.com/login/oauth/access_token",
    }

    token = a.flow(config=config, scopes=["repo"])
    print(token)
# ============= EOF =============================================
