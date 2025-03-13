
SECRET_KEY = 'fake-key'
DEBUG = True
ALLOWED_HOSTS = ['*']
ROOT_URLCONF = 'mon_projet.urls'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'recommandations', 
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
STATIC_URL = '/static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',  
#         'NAME': 'bjzv0bfpzgquhzxmjzuo',        
#         'USER': 'u2puh0fcouhfbwcpvqu3',                
#         'PASSWORD': 'HxTong235uPHl0yjUIRM6qRLfCRkpi',                
#         'HOST': 'bjzv0bfpzgquhzxmjzuo-postgresql.services.clever-cloud.com',                       
#         'PORT': '50013',                          
#     }
    
# }
