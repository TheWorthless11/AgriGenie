from django.contrib import admin
from .models import UserApproval, SystemAlert, SystemReport, AIDiseaseMonitor, AIPricePredictor, ActivityLog


@admin.register(UserApproval)
class UserApprovalAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'reviewed_by', 'reviewed_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'reviewed_at']


@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'is_active', 'all_users', 'created_at']
    list_filter = ['alert_type', 'is_active', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    filter_horizontal = ['target_users']


@admin.register(SystemReport)
class SystemReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'generated_at', 'generated_by']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['title']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'


@admin.register(AIDiseaseMonitor)
class AIDiseaseMonitorAdmin(admin.ModelAdmin):
    list_display = ['total_detections', 'accurate_detections', 'accuracy_percentage', 'last_updated', 'model_version']
    readonly_fields = ['last_updated']


@admin.register(AIPricePredictor)
class AIPricePredictorAdmin(admin.ModelAdmin):
    list_display = ['total_predictions', 'accurate_predictions', 'accuracy_percentage', 'average_error_percentage', 'last_updated', 'model_version']
    readonly_fields = ['last_updated']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp', 'user__role']
    search_fields = ['user__username', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
