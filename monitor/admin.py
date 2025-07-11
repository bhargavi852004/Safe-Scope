from django.contrib import admin
from .models import RiskAlert, ParentUser

@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = ('child_email', 'reason', 'page_url', 'triggered_at')
    list_filter = ('triggered_at',)
    search_fields = ('child_email', 'reason')


@admin.register(ParentUser)
class ParentUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'is_staff', 'is_active')
    search_fields = ('email',)
