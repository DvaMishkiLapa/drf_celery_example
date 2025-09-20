from django.contrib import admin
from lead.models import (Lead, LeadEvent, LeadFollowup, LeadFollowupRule,
                         TaskExecutionLock)


class ReadOnlyModelAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('phone', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('phone',)
    ordering = ('-updated_at',)


@admin.register(LeadEvent)
class LeadEventAdmin(admin.ModelAdmin):
    list_display = ('lead', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('lead__phone',)
    ordering = ('-created_at',)


@admin.register(LeadFollowupRule)
class LeadFollowupRuleAdmin(admin.ModelAdmin):
    list_display = ('status', 'delay', 'is_enabled', 'text')
    list_filter = ('status', 'is_enabled')
    search_fields = ('text',)
    ordering = ('status', 'delay')


@admin.register(LeadFollowup)
class LeadFollowupAdmin(ReadOnlyModelAdmin):
    list_display = ('lead', 'rule', 'created_at')
    list_filter = ('rule__status',)
    search_fields = ('lead__phone',)
    ordering = ('-created_at',)
    readonly_fields = ('lead', 'rule', 'created_at')


@admin.register(TaskExecutionLock)
class TaskExecutionLockAdmin(ReadOnlyModelAdmin):
    list_display = ('name', 'locked_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('name', 'locked_at')
