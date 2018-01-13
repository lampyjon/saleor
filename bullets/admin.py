from django.contrib import admin
from .models import Bullet, ActivityCache, OldBullet, News, RunningEvent 
from django_summernote.admin import SummernoteModelAdmin


admin.site.register(ActivityCache)
admin.site.register(OldBullet)
admin.site.register(Bullet)
admin.site.register(RunningEvent)


class NewsAdmin(SummernoteModelAdmin):
#	prepopulated_fields = {"slug": ("title",)}
	pass

admin.site.register(News, NewsAdmin)

