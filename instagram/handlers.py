from google.appengine.ext import webapp

import settings

from instagram.client import InstagramAPI

from instadrop.models import Profile
from lilcookies import LilCookies


class InstagramAuth(webapp.RequestHandler):
    def get(self):
        api = InstagramAPI(**settings.INSTAGRAM_CONFIG)
        self.redirect(api.get_authorize_url())


class InstagramDisconnect(webapp.RequestHandler):
    def get(self):
        cookieutil = LilCookies(self, settings.COOKIE_SECRET)
        ig_user_id = cookieutil.get_secure_cookie(name = "ig_user_id")

        profiles = Profile.all()
        profiles.filter("ig_user_id =", ig_user_id)
        profile = profiles.get()

        if profile:
            profile.delete()

        self.redirect("/")


class InstagramCallback(webapp.RequestHandler):
    def get(self):
        instagram_client = InstagramAPI(**settings.INSTAGRAM_CONFIG)

        code = self.request.get("code")
        access_token = instagram_client.exchange_code_for_access_token(code)

        instagram_client = InstagramAPI(access_token = access_token)

        user = instagram_client.user("self")

        profiles = Profile.all()
        profiles.filter("ig_user_id = ", user.id)
        profile = (profiles.get() or Profile())

        profile.full_name = (user.full_name or user.username)
        profile.ig_user_id = user.id
        profile.ig_username = user.username
        profile.ig_access_token = access_token
        profile.put()

        cookieutil = LilCookies(self, settings.COOKIE_SECRET)
        cookieutil.set_secure_cookie(
                name = "ig_user_id",
                value = user.id,
                expires_days = 365)

        self.redirect("/connect")

class InstagramLoadUser(webapp.RequestHandler):
    def get(self):
        ig_user_id = self.request.get("ig_user_id")

        if not ig_user_id:
            self.redirect("/connect")

        instagram_client = InstagramAPI(**settings.INSTAGRAM_CONFIG)

        access_token = instagram_client.exchange_user_id_for_access_token(ig_user_id)

        instagram_client = InstagramAPI(access_token = access_token)

        user = instagram_client.user("self")

        profiles = Profile.all()
        profiles.filter("ig_user_id = ", user.id)
        profile = (profiles.get() or Profile())

        profile.full_name = (user.full_name or user.username)
        profile.ig_user_id = user.id
        profile.ig_username = user.username
        profile.ig_access_token = access_token
        profile.put()

        cookieutil = LilCookies(self, settings.COOKIE_SECRET)
        cookieutil.set_secure_cookie(
                name = "ig_user_id",
                value = user.id,
                expires_days = 365)

        self.redirect("/")


class InstagramSubscribe(webapp.RequestHandler):
    def get(self):
        from urllib import urlencode
        from httplib2 import Http

        subscriptions_url = "https://api.instagram.com/v1/subscriptions"

        data = {
            "client_id": settings.INSTAGRAM_CONFIG["client_id"],
            "client_secret": settings.INSTAGRAM_CONFIG["client_secret"],
            "callback_url": settings.INSTAGRAM_PUSH_CALLBACK,
            "aspect": "media",
            "object": "user"
        }

        http_object = Http(timeout = 20)
        response, content = http_object.request(
                subscriptions_url, "POST", urlencode(data))


class InstagramPushCallback(webapp.RequestHandler):
    def get(self):
        challenge = self.request.get("hub.challenge")
        self.response.out.write(challenge)


    def post(self):
        import hashlib
        import hmac
        import logging
        from StringIO import StringIO
        from time import time
        from urllib2 import urlopen
        from django.utils import simplejson
        from dropbox import helper as dropbox_helper

        payload = self.request.body

        # verify payload
        signature = self.request.headers['X-Hub-Signature']
        client_secret = settings.INSTAGRAM_CONFIG['client_secret']
        hashing_obj= hmac.new(client_secret.encode("utf-8"),
            msg = payload.encode("utf-8"),
            digestmod = hashlib.sha1)
        digest = hashing_obj.hexdigest()

        if digest != signature:
            logging.info("Digest and signature differ. (%s, %s)"
                % (digest, signature))
            return

        changes = simplejson.loads(payload)
        for change in changes:
            profiles = Profile.all()
            profiles.filter("ig_user_id =", change['object_id'])
            profile = profiles.get()

            if not profile:
                logging.info("Cannot find profile %s", change['object_id'])
                continue

            instagram_client = InstagramAPI(
                    access_token = profile.ig_access_token)

            media, _ = instagram_client.user_recent_media(count = 1)
            media = media[0]

            media_file = urlopen(media.images['standard_resolution'].url)
            media_data = media_file.read()

            dropbox_file = StringIO(media_data)
            dropbox_file.name = ("%s.jpg" % int(time()))

            dropbox_client = dropbox_helper.authenticated_client(profile)
            dropbox_client.put_file(
                settings.DROPBOX_CONFIG['root'],
                "/Instagram Photos/",
                dropbox_file)
