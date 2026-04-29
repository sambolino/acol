#
# VAMDC-node config file
#
# You may customize your setup by copy&pasting the variables you want to 
# change from the default config file in nodes/settings_default.py to 
# this file. Try to only copy over things you really need to customize 
# and do *not* make any changes to settings_defaults.py directly. That 
# way you'll always have a sane default to fall back on (also, the 
# master file may change with updates).

import os
from settings_default import *

os.environ['LC_ALL'] = 'en_US.utf8'

# Comment out the following line once your node goes live.
# As long as this is set to True there will be additional
# logging output and performance will be slower.
DEBUG=True

NODE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../nodes/acol
BASE_PATH = os.path.dirname(os.path.dirname(NODE_DIR))         # .../NodeSoftware

###################################################
# Database connection
# Setting up the database type and information.
# Simplest for testing is sqlite3.
###################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': "DB_NAME",
        'USER': "DB_USER",                      # Not used with sqlite3.
        'PASSWORD': "DB_PASSWORD",                  # Not used with sqlite3.
        'HOST': "DB_HOST",                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

###############################################
# Admin information
# You NEED to set a valid email-adress here
# since critical errors will be emailed there.
###############################################
ADMINS = (  ('', ''),
            ('', ''),
        )

MANAGERS = ADMINS

###############################################
# Logging
# You can uncomment the following line and set
# the filename. Unless you do so, the log-file
# is called 'node.log' and resides in your
# systems TMP-directory
###############################################
NODENAME='acol'

LOGGING['handlers']['logfile']['filename'] = os.path.join(
    BASE_PATH,
    'nodes',
    NODENAME,
    'node.log'
)

###############################################
# Example query
# Please comment out the following and adapt it
# to at least one meaingful query for your node.
###############################################
# EXAMPLE_QUERIES = ['SELECT ALL WHERE ... something',
#                    'SELECT ALL WHERE ... something else',
#                   ]

STATIC_URL = '/static/'
SERVE_STATIC = True

INSTALLED_APPS = ('django.contrib.admin',
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'node',
		          'django_extensions',
		          #'south', 
                  'floppyforms',
                  )

STATICFILES_DIRS = (
    os.path.join(os.getcwd(), "../../static"),
    os.path.join(os.getcwd(), "static"),
    BASE_PATH+'/nodes/acol/static'
)

ADMIN_MEDIA_PREFIX = '/static/admin/'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATES = [ 
    {   
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_PATH, 'nodes', NODENAME, 'templates'),
            os.path.join(BASE_PATH, 'nodes', NODENAME, 'static', 'templates'),
            ],  
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],  
        },  
    },  
]

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    BASE_PATH+'/nodes/acol/templates/',
    BASE_PATH+'/static/templates/',
    BASE_PATH+'/nodes/acol/static/templates/'
)

TMPDIR = os.path.join(BASE_PATH, 'tmp')

MIRRORS = {
}

MIDDLEWARE = (
    #~ 'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #~ 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

PROJECT_DIR = os.path.dirname(__file__)

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

EXAMPLE_QUERIES = [\
  'Select * where AtomSymbol="H"',
]

SECRET_KEY = "xxx"


QUERY_STORE_ACTIVE = True


try:
    from local_settings import *
except ImportError:
    pass
