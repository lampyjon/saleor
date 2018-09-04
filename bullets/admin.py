from django.contrib import admin
from .models import Bullet, ActivityCache, OldBullet, News, RunningEvent, BulletEvent, BigBulletRider
from .models import IWDRider 
from django_summernote.admin import SummernoteModelAdmin


admin.site.register(ActivityCache)
admin.site.register(OldBullet)
admin.site.register(Bullet)
admin.site.register(RunningEvent)
admin.site.register(BulletEvent)
admin.site.register(IWDRider)
admin.site.register(BigBulletRider)

class NewsAdmin(SummernoteModelAdmin):
	pass

admin.site.register(News, NewsAdmin)

