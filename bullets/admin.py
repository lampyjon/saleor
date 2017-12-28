from django.contrib import admin
from .models import SiteValue, ActivityCache, Bullet, News, TdBStage, TdBLeaderBoard_Entry, CTSVehicle, CTSRider
from django_summernote.admin import SummernoteModelAdmin

admin.site.register(SiteValue)
admin.site.register(ActivityCache)
admin.site.register(Bullet)
#admin.site.register(VeloVolunteer)
#admin.site.register(BulletsRunner)
admin.site.register(CTSVehicle)
admin.site.register(CTSRider)


class NewsAdmin(SummernoteModelAdmin):
#	prepopulated_fields = {"slug": ("title",)}
	pass

admin.site.register(News, NewsAdmin)


class TDBStageAdmin(SummernoteModelAdmin):
	pass

admin.site.register(TdBStage, TDBStageAdmin)
admin.site.register(TdBLeaderBoard_Entry)

