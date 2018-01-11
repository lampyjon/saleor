from django.contrib import admin
from .models import Bullet, ActivityCache, OldBullet, VeloVolunteer, BulletsRunner, News, TdBStage, TdBLeaderBoard_Entry, CTSVehicle, CTSRider, BulletRunnerPhoto, VeloFeedback, CharityOfYear, NewTDBLeaderBoard
from django_summernote.admin import SummernoteModelAdmin


admin.site.register(ActivityCache)
admin.site.register(OldBullet)
admin.site.register(Bullet)
admin.site.register(VeloVolunteer)
admin.site.register(BulletsRunner)
admin.site.register(CTSVehicle)
admin.site.register(CTSRider)
admin.site.register(BulletRunnerPhoto)
admin.site.register(VeloFeedback)
admin.site.register(CharityOfYear)
admin.site.register(NewTDBLeaderBoard)


class NewsAdmin(SummernoteModelAdmin):
#	prepopulated_fields = {"slug": ("title",)}
	pass

admin.site.register(News, NewsAdmin)


class TDBStageAdmin(SummernoteModelAdmin):
	pass

admin.site.register(TdBStage, TDBStageAdmin)
admin.site.register(TdBLeaderBoard_Entry)


