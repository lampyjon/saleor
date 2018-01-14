# custom_storages.py

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage
from saleor.core.storages import S3MediaStorage

class StaticStorage(S3BotoStorage):
	location = settings.STATICFILES_LOCATION


class MediaStorage(S3MediaStorage):
        location = settings.MEDIAFILES_LOCATION


