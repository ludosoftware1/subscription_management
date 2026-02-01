from django.conf import settings

def app_version_processor(request):
    return {'APP_VERSION': settings.APP_VERSION}