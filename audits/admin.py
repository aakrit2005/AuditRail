from django.contrib import admin
from .models import Auditor, Location, AuditTemplate, ChecklistItem, Audit, AuditResponse


@admin.register(Auditor)
class AuditorAdmin(admin.ModelAdmin):
    list_display = ('name', 'initials', 'region', 'email')
    search_fields = ('name', 'region')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_name', 'region')
    search_fields = ('name', 'client_name', 'region')


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1


@admin.register(AuditTemplate)
class AuditTemplateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [ChecklistItemInline]


class AuditResponseInline(admin.TabularInline):
    model = AuditResponse
    extra = 0
    readonly_fields = ('checklist_item',)


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('code', 'location', 'auditor', 'template', 'status', 'due_date', 'score_percent', 'flagged_count')
    list_filter = ('status', 'template', 'auditor')
    search_fields = ('code', 'location__name', 'auditor__name')
    inlines = [AuditResponseInline]


@admin.register(AuditResponse)
class AuditResponseAdmin(admin.ModelAdmin):
    list_display = ('audit', 'checklist_item', 'score', 'flagged', 'has_photo')
    list_filter = ('flagged', 'has_photo')
