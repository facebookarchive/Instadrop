from google.appengine.ext import webapp

import settings

from dropbox import auth as dropbox_auth
from instadrop.models import Profile
from lilcookies import LilCookies


class DropboxAuth(webapp.RequestHandler):
    def get(self):
        cookieutil = LilCookies(self, settings.COOKIE_SECRET)
        ig_user_id = cookieutil.get_secure_cookie(name = "ig_user_id")

        dba = dropbox_auth.Authenticator(settings.DROPBOX_CONFIG)
        req_token = dba.obtain_request_token()

        profiles = Profile.all()
        profiles.filter("ig_user_id =", ig_user_id)
        profile = profiles.get()

        if not profile:
            self.redirect("/connect")
            return

        profile.db_oauth_token_key = req_token.key
        profile.db_oauth_token_secret = req_token.secret
        profile.put()

        authorize_url = dba.build_authorize_url(
                req_token,
                callback = settings.DROPBOX_CALLBACK)

        self.redirect(authorize_url)


class DropboxDisconnect(webapp.RequestHandler):
    def get(self):
        cookieutil = LilCookies(self, settings.COOKIE_SECRET)
        ig_user_id = cookieutil.get_secure_cookie(name = "ig_user_id")

        profiles = Profile.all()
        profiles.filter("ig_user_id =", ig_user_id)
        profile = profiles.get()

        if profile:
            profile.db_access_token_key = None
            profile.db_oauth_token_secret = None
            profile.put()

        self.redirect("/")


class DropboxCallback(webapp.RequestHandler):
    def get(self):
        from oauth import oauth

        dba = dropbox_auth.Authenticator(settings.DROPBOX_CONFIG)

        token = self.request.get("oauth_token")
        profile = Profile.all().filter("db_oauth_token_key =", token).get()

        if not profile:
            self.redirect("/connect")
            return

        oauth_token = oauth.OAuthToken(
                                       key = profile.db_oauth_token_key,
                                       secret = profile.db_oauth_token_secret)

        verifier = settings.DROPBOX_CONFIG['verifier']
        access_token = dba.obtain_access_token(oauth_token, verifier)

        profile.db_access_token_key = access_token.key
        profile.db_access_token_secret = access_token.secret
        profile.put()

        self.redirect("/connect")