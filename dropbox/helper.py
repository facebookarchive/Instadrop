def load_config(config_file):
    from dropbox import auth
    return auth.Authenticator.load_config(config_file)


def authenticated_client(profile):
    import settings
    from dropbox import auth
    from dropbox.client import DropboxClient
    from oauth import oauth

    dba = auth.Authenticator(settings.DROPBOX_CONFIG)

    access_token = oauth.OAuthToken(
            key = profile.db_access_token_key,
            secret = profile.db_access_token_secret)

    client = DropboxClient(
        settings.DROPBOX_CONFIG['server'],
        settings.DROPBOX_CONFIG['content_server'],
        settings.DROPBOX_CONFIG['port'],
        dba,
        access_token)

    return client