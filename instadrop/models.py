from google.appengine.ext import db


class Profile(db.Model):
    full_name = db.StringProperty()
    ig_user_id = db.StringProperty()
    ig_username = db.StringProperty()
    ig_access_token = db.StringProperty()
    db_oauth_token_key = db.StringProperty()
    db_oauth_token_secret = db.StringProperty()
    db_access_token_key = db.StringProperty()
    db_access_token_secret = db.StringProperty()

    def dropbox_connected(self):
        return (self.db_access_token_key and self.db_access_token_secret)


    def instagram_connected(self):
        return (self.ig_access_token and self.ig_user_id)


    def fully_connected(self):
        return (self.dropbox_connected() and self.instagram_connected())