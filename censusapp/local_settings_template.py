# --- Instructions ---
# Fill in the six required fields below
# When you're done, save the file and rename it to "local_settings.py"
# Remember that this file will not sync through github and so will need to be uploaded manually.

# --- Census Settings ---

CENSUS_NAME = "your census name goes here"
# The CENSUS_NAME will appear as the title of your site and in the header of every page.


COPY_ID_PREFIX = "your copy id prefix goes here"
# The COPY_ID_PREFIX will appear in some table headings and some urls. It should be kept short (two letters is best).


RESERVED_PREFIXES = {'homepage', 'title', 'issue', 'copy', 'search', 'info'}
if COPY_ID_PREFIX in RESERVED_PREFIXES:
    raise ValueError(f"COPY_ID_PREFIX '{COPY_ID_PREFIX}' is a reserved word and cannot be used.")
# The COPY_ID_PREFIX must *not* be any of the above six words, since this will create a url conflict.


CENSUS_EMAIL = "your email address goes here"
# This email address will appear in a link in the Site Footer.


# --- Allowed Hosts ---

ALLOWED_HOSTS = ['localhost','www.yourcensusname.org', 'youraccount.yourhostingsite.com']
# Include 'localhost' as well as your own site's URL and your hosting site's URL.


# --- Notifications ---

NOTIFICATIONS = [('your own name goes here', 'your email address goes here')]
# Include your own name and email address.


# --- Secret Key ---

SECRET_KEY = 'your secret key goes here'
# SECURITY WARNING: keep the secret key used in production secret!
# You can generate a new secret key from the command line, with these two commands:
# > from django.core.management.utils import get_random_secret_key
# > print(get_random_secret_key())


# --- Debug ---

DEBUG = True
# DEBUG should be set to True in development and to False in production
# SECURITY WARNING: don't run with DEBUG turned on in production!
# Note that when the site runs locally with DEBUG = False, media files (i.e. the title icons) will not appear.
# This is because Django does not serve media files in production mode, and I couldn't find a simple workaround.


