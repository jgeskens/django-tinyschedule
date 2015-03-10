from __future__ import unicode_literals
from django.db import models
from django.db.models import Q
from django.utils import formats
from django.template.defaultfilters import pluralize
from django.contrib.humanize.templatetags.humanize import ordinal, apnumber

import datetime
import six


class ScheduleRepeatType(object):
    NONE = 'none'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'

    choices = (
        (NONE, 'None'),
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
    )

    choices_dict = dict(choices)

    pluralized_instances = (
        (DAILY, 'day,days'),
        (WEEKLY, 'week,weeks'),
        (MONTHLY, 'month,months'),
        (YEARLY, 'year,years'),
    )

    pluralized_instances_dict = dict(pluralized_instances)


class WeekDay(object):
    MONDAY = 'monday'
    TUESDAY = 'tuesday'
    WEDNESDAY = 'wednesday'
    THURSDAY = 'thursday'
    FRIDAY = 'friday'
    SATURDAY = 'saturday'
    SUNDAY = 'sunday'

    choices = (
        (MONDAY, 'monday'),
        (TUESDAY, 'tuesday'),
        (WEDNESDAY, 'wednesday'),
        (THURSDAY, 'thursday'),
        (FRIDAY, 'friday'),
        (SATURDAY, 'saturday'),
        (SUNDAY, 'sunday'),
    )

    choices_dict = dict(choices)


def add_month(date, override_day=0):
    date_day = date.day if override_day == 0 else override_day
    if date.month == 12:
        return datetime.date(date.year + 1, 1, date_day)
    else:
        return datetime.date(date.year, date.month + 1, date_day)


def add_month_based_on_weekday(date):
    # Is the weekday of this date the last one?
    is_last_weekday = (date + datetime.timedelta(weeks=1)).month != date.month

    # Some magic which pushes and pulls some weeks until
    # it fits right.
    new_date = date + datetime.timedelta(weeks=4)
    if (new_date.day + 6) // 7 < (date.day + 6) // 7:
        new_date += datetime.timedelta(weeks=1)
    next_month = add_month(date, override_day=1)
    if new_date.month == (next_month.month - 1 if next_month.month > 1 else 12):
        new_date += datetime.timedelta(weeks=1)
    elif new_date.month == (next_month.month + 1 if next_month.month < 12 else 1):
        new_date += datetime.timedelta(weeks=-1)

    # If the weekdate of the original date was the last one,
    # and there is some room left, add a week extra so this
    # will result in a last weekday of the month again.
    if is_last_weekday and (new_date + datetime.timedelta(weeks=1)).month == new_date.month:
        new_date += datetime.timedelta(weeks=1)

    return new_date


class ScheduleManager(models.Manager):
    def lookup(self, date, end_date=None, schedules_queryset=None):
        end_date = end_date or date
        schedules_queryset = schedules_queryset or self.all()
        for schedule in schedules_queryset.filter(
            start_date__gte=date,
            end_date__isnull=True,
            repeat_type=ScheduleRepeatType.NONE
            ).filter(start_date__lte=end_date):
            yield schedule.start_date, schedule, 0

        def check_repeating_patterns(schedules):
            for schedule in schedules:
                for i, occurrence in enumerate(schedule.iterate_occurrences(end_date)):
                    if occurrence >= date:
                        yield occurrence, schedule, i

        for schedule_pair in check_repeating_patterns(
                schedules_queryset.filter(
                    (Q(start_date__lte=date) | Q(start_date__lte=end_date))
                    &
                    (Q(end_date__gte=date) | Q(end_date__gte=end_date))
                ).exclude(repeat_type=ScheduleRepeatType.NONE)
            ):
            yield schedule_pair

        for schedule_pair in check_repeating_patterns(
                schedules_queryset.filter(
                    Q(start_date__lte=date) | Q(start_date__lte=end_date)
                ).filter(
                    end_date__isnull=True,
                ).exclude(repeat_type=ScheduleRepeatType.NONE)
            ):
            yield schedule_pair

@six.python_2_unicode_compatible
class AbstractSchedule(models.Model):
    start_date = models.DateField(default=datetime.datetime.now)
    end_date = models.DateField(blank=True, null=True)
    end_after_occurrences = models.PositiveIntegerField(default=0)
    repeat_type = models.CharField(max_length=32, choices=ScheduleRepeatType.choices, default=ScheduleRepeatType.NONE)
    repeat_every = models.PositiveIntegerField(default=1)
    monthly_is_based_on_weekday = models.BooleanField(blank=True, default=False)
    monday = models.BooleanField(blank=True, default=False)
    tuesday = models.BooleanField(blank=True, default=False)
    wednesday = models.BooleanField(blank=True, default=False)
    thursday = models.BooleanField(blank=True, default=False)
    friday = models.BooleanField(blank=True, default=False)
    saturday = models.BooleanField(blank=True, default=False)
    sunday = models.BooleanField(blank=True, default=False)

    objects = ScheduleManager()

    class Meta:
        abstract = True

    @property
    def humanized_weekdays(self):
        return ', '.join(weekday_name for weekday_slug, weekday_name in WeekDay.choices if getattr(self, weekday_slug))

    def _description_builder(self):
        if self.repeat_type != ScheduleRepeatType.NONE:
            yield 'every'
            if self.repeat_every > 1:
                yield apnumber(self.repeat_every)
            yield pluralize(self.repeat_every, ScheduleRepeatType.pluralized_instances_dict[self.repeat_type])
            if self.repeat_type == ScheduleRepeatType.WEEKLY and \
                    any(getattr(self, weekday_entry[0]) for weekday_entry in WeekDay.choices):
                yield 'on'
                yield self.humanized_weekdays
            elif self.repeat_type == ScheduleRepeatType.MONTHLY and self.monthly_is_based_on_weekday:
                week_position = (datetime.date(self.start_date.year, self.start_date.month, 1).weekday() + self.start_date.day) / 7
                is_last_weekday = (self.start_date + datetime.timedelta(weeks=1)).month != self.start_date.month
                if is_last_weekday:
                    yield 'on the last %s' % WeekDay.choices[self.start_date.weekday()][1]
                else:
                    yield 'on the %s %s' % (ordinal(week_position + 1), WeekDay.choices[self.start_date.weekday()][1])
            elif self.repeat_type == ScheduleRepeatType.MONTHLY and not self.monthly_is_based_on_weekday:
                yield 'on the'
                yield ordinal(self.start_date.day)
            yield 'from'
            yield formats.date_format(self.start_date, 'SHORT_DATE_FORMAT')

            if self.end_date is not None:
                yield 'until'
                yield formats.date_format(self.end_date, 'SHORT_DATE_FORMAT')

            if self.end_after_occurrences > 0:
                if self.end_date:
                    yield 'or'
                yield 'until'
                yield six.text_type(self.end_after_occurrences)
                yield pluralize(self.end_after_occurrences, 'occurence,occurences')
                yield 'took place'
        else:
            yield 'on'
            yield formats.date_format(self.start_date, 'SHORT_DATE_FORMAT')

    def __str__(self):
        return ' '.join(self._description_builder())

    def iterate_occurrences(self, end_date=None):
        occurrences = 0
        current = self.start_date
        while (end_date is None or current <= end_date) and \
            (not self.end_date or current <= self.end_date) and \
            (self.end_after_occurrences == 0 or occurrences < self.end_after_occurrences):
            occurrences += 1
            yield current
            current = self.next_date(current)

    def __getitem__(self, item):
        if not isinstance(item, six.string_types):
            for i, occurrence in enumerate(self.iterate_occurrences()):
                if item == i:
                    return occurrence
        else:
            return super(AbstractSchedule, self).__getitem__(item)

    def next_date(self, date):
        """
        Based on this schedule, give the next valid date after ``date``.
        It is only guaranteed that the resulting next date is valid when the
        given ``date`` is already valid.
        """
        if self.repeat_type == ScheduleRepeatType.DAILY:
            return date + datetime.timedelta(days=self.repeat_every)
        elif self.repeat_type == ScheduleRepeatType.WEEKLY:
            current = date
            for i in range(7):
                current = current + datetime.timedelta(days=1)
                if current.weekday() == 0:
                    # When we arrive on Monday, skip some weeks if needed.
                    current = current + datetime.timedelta(days=7 * (self.repeat_every - 1))
                if getattr(self, WeekDay.choices[current.weekday()][0]):
                    return current
        elif self.repeat_type == ScheduleRepeatType.MONTHLY:
            current = date
            for i in range(self.repeat_every):
                # FIXME: catch ValueError and ignore bad months. Works like Google Calendar
                current = add_month_based_on_weekday(current) \
                    if self.monthly_is_based_on_weekday \
                    else add_month(current)
            return current
        elif self.repeat_type == ScheduleRepeatType.YEARLY:
            try:
                return datetime.date(date.year + self.repeat_every,
                                     self.start_date.month,
                                     self.start_date.day)
            except ValueError:
                assert self.start_date.day == 29 and self.start_date.month == 2
                return datetime.date(date.year + self.repeat_every, 2, 28)

        raise ValueError('repeat_type "%s" is not supported' % self.repeat_type)


class Schedule(AbstractSchedule):
    pass
