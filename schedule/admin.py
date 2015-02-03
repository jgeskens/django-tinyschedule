from __future__ import unicode_literals
from django.contrib import admin

from .models import Schedule


class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        '__unicode__',
        'start_date',
        'end_date',
        'end_after_occurrences',
        'repeat_type',
        'repeat_every',
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday',
        'monthly_is_based_on_weekday'
    )
    list_filter = ('repeat_type',)
    date_hierarchy = 'start_date'
admin.site.register(Schedule, ScheduleAdmin)
