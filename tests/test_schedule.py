from django.test import TestCase

from schedule.models import Schedule, ScheduleRepeatType

import datetime


class ScheduleTests(TestCase):
    def setUp(self):
        self.simple = Schedule.objects.create(start_date=datetime.date(2014, 6, 30))

        self.everyday = Schedule.objects.create(
            start_date=datetime.date(2014, 6, 30),
            repeat_type=ScheduleRepeatType.DAILY)

        self.every3days = Schedule.objects.create(
            start_date=datetime.date(2014, 6, 27),
            repeat_type=ScheduleRepeatType.DAILY,
            repeat_every=3)

        self.every2daysuntil = Schedule.objects.create(
            start_date=datetime.date(2014, 6, 28),
            end_date=datetime.date(2014, 7, 15),
            repeat_type=ScheduleRepeatType.DAILY,
            repeat_every=2)

        self.every2weeksmonwedfri = Schedule.objects.create(
            start_date=datetime.date(2014, 6, 30),
            repeat_type=ScheduleRepeatType.WEEKLY,
            monday=True, wednesday=True, friday=True,
            repeat_every=2)

        self.everymonth = Schedule.objects.create(
            start_date=datetime.date(2014, 1, 15),
            end_date=datetime.date(2014, 8, 31),
            repeat_type=ScheduleRepeatType.MONTHLY)

        self.everymonthweekday = Schedule.objects.create(
            start_date=datetime.date(2014, 1, 15),
            end_date=datetime.date(2015, 8, 31),
            repeat_type=ScheduleRepeatType.MONTHLY,
            monthly_is_based_on_weekday=True)

        self.everymonthweekday2 = Schedule.objects.create(
            start_date=datetime.date(2014, 1, 1),
            end_date=datetime.date(2015, 8, 31),
            repeat_type=ScheduleRepeatType.MONTHLY,
            monthly_is_based_on_weekday=True)

        self.everymonthweekday3 = Schedule.objects.create(
            start_date=datetime.date(2014, 1, 29),
            end_date=datetime.date(2015, 8, 31),
            repeat_type=ScheduleRepeatType.MONTHLY,
            repeat_every=2,
            monthly_is_based_on_weekday=True)

        self.fiveoccurrences = Schedule.objects.create(
            start_date=datetime.date(2014, 1, 29),
            end_after_occurrences=5,
            repeat_type=ScheduleRepeatType.MONTHLY,
            repeat_every=2,
            monthly_is_based_on_weekday=True)

        self.yearly = Schedule.objects.create(
            start_date=datetime.date(2012, 2, 29),
            end_after_occurrences=3,
            repeat_type=ScheduleRepeatType.YEARLY,
            repeat_every=2)

    def test_lookup_simple(self):
        lookup = list(Schedule.objects.lookup(datetime.date(2014, 6, 30)))
        self.assertTrue((self.simple.start_date, self.simple, 0) in lookup)

    def test_lookup_every3days(self):
        lookup = list(Schedule.objects.lookup(datetime.date(2014, 6, 30)))
        self.assertTrue((datetime.date(2014, 6, 30), self.every3days, 1) in lookup)

    def test_lookup_every2daysuntil(self):
        lookup = list(Schedule.objects.lookup(datetime.date(2014, 6, 30)))
        self.assertTrue((datetime.date(2014, 6, 30), self.every2daysuntil, 1) in lookup)

    def test_lookup_period(self):
        lookup = list(Schedule.objects.lookup(datetime.date(2014, 7, 7), datetime.date(2014, 7, 30)))
        lookup = [l[:2] for l in lookup]

        self.assertTrue(len(lookup) > 0)

        self.assertFalse((datetime.date(2014, 7, 6), self.everyday) in lookup)
        self.assertTrue((datetime.date(2014, 7, 7), self.everyday) in lookup)
        self.assertTrue((datetime.date(2014, 7, 30), self.everyday) in lookup)
        self.assertFalse((datetime.date(2014, 7, 31), self.everyday) in lookup)

        self.assertTrue((datetime.date(2014, 7, 14), self.every2daysuntil) in lookup)
        self.assertFalse((datetime.date(2014, 7, 16), self.every2daysuntil) in lookup)

        self.assertFalse((datetime.date(2014, 7, 6), self.every3days) in lookup)
        self.assertTrue((datetime.date(2014, 7, 9), self.every3days) in lookup)
        self.assertTrue((datetime.date(2014, 7, 30), self.every3days) in lookup)
        self.assertFalse((datetime.date(2014, 8, 2), self.every3days) in lookup)

        self.assertTrue((datetime.date(2014, 7, 14), self.every2weeksmonwedfri) in lookup)
        self.assertTrue((datetime.date(2014, 7, 28), self.every2weeksmonwedfri) in lookup)

    def test_next_date_for_weeks(self):
        dates = []
        date = self.every2weeksmonwedfri.start_date
        while date <= datetime.date(2014, 7, 30):
            dates.append(date)
            date = self.every2weeksmonwedfri.next_date(date)

        expected = [
            datetime.date(2014, 6, 30),
            datetime.date(2014, 7, 02),
            datetime.date(2014, 7, 04),
            datetime.date(2014, 7, 14),
            datetime.date(2014, 7, 16),
            datetime.date(2014, 7, 18),
            datetime.date(2014, 7, 28),
            datetime.date(2014, 7, 30)
        ]

        self.assertEqual(dates, expected)

    def test_next_date_for_months(self):
        dates = []
        date = self.everymonth.start_date
        while date <= self.everymonth.end_date:
            dates.append(date)
            date = self.everymonth.next_date(date)

        expected = [
            datetime.date(2014, 1, 15),
            datetime.date(2014, 2, 15),
            datetime.date(2014, 3, 15),
            datetime.date(2014, 4, 15),
            datetime.date(2014, 5, 15),
            datetime.date(2014, 6, 15),
            datetime.date(2014, 7, 15),
            datetime.date(2014, 8, 15)
        ]

        self.assertEqual(dates, expected)

    def test_next_date_for_months_based_on_weekday(self):
        dates = []
        date = self.everymonthweekday.start_date
        while date <= self.everymonthweekday.end_date:
            dates.append(date)
            date = self.everymonthweekday.next_date(date)

        expected = [
            datetime.date(2014, 1, 15),
            datetime.date(2014, 2, 19),
            datetime.date(2014, 3, 19),
            datetime.date(2014, 4, 16),
            datetime.date(2014, 5, 21),
            datetime.date(2014, 6, 18),
            datetime.date(2014, 7, 16),
            datetime.date(2014, 8, 20),
            datetime.date(2014, 9, 17),
            datetime.date(2014, 10, 15),
            datetime.date(2014, 11, 19),
            datetime.date(2014, 12, 17),
            datetime.date(2015, 1, 21),
            datetime.date(2015, 2, 18),
            datetime.date(2015, 3, 18),
            datetime.date(2015, 4, 15),
            datetime.date(2015, 5, 20),
            datetime.date(2015, 6, 17),
            datetime.date(2015, 7, 15),
            datetime.date(2015, 8, 19)
        ]

        self.assertEqual(dates, expected)

    def test_next_date_for_months_based_on_weekday2(self):
        dates = []
        date = self.everymonthweekday2.start_date
        while date <= self.everymonthweekday2.end_date:
            dates.append(date)
            date = self.everymonthweekday2.next_date(date)

        expected = [
            datetime.date(2014, 1, 1),
            datetime.date(2014, 2, 5),
            datetime.date(2014, 3, 5),
            datetime.date(2014, 4, 2),
            datetime.date(2014, 5, 7),
            datetime.date(2014, 6, 4),
            datetime.date(2014, 7, 2),
            datetime.date(2014, 8, 6),
            datetime.date(2014, 9, 3),
            datetime.date(2014, 10, 1),
            datetime.date(2014, 11, 5),
            datetime.date(2014, 12, 3),
            datetime.date(2015, 1, 7),
            datetime.date(2015, 2, 4),
            datetime.date(2015, 3, 4),
            datetime.date(2015, 4, 1),
            datetime.date(2015, 5, 6),
            datetime.date(2015, 6, 3),
            datetime.date(2015, 7, 1),
            datetime.date(2015, 8, 5)
        ]

        self.assertEqual(dates, expected)

    def test_next_date_for_months_based_on_weekday3(self):
        dates = []
        date = self.everymonthweekday3.start_date
        while date <= self.everymonthweekday3.end_date:
            dates.append(date)
            date = self.everymonthweekday3.next_date(date)

        expected = [
            datetime.date(2014, 1, 29),
            datetime.date(2014, 3, 26),
            datetime.date(2014, 5, 28),
            datetime.date(2014, 7, 30),
            datetime.date(2014, 9, 24),
            datetime.date(2014, 11, 26),
            datetime.date(2015, 1, 28),
            datetime.date(2015, 3, 25),
            datetime.date(2015, 5, 27),
            datetime.date(2015, 7, 29)
        ]

        self.assertEqual(dates, expected)

    def test_lookup_end_after_occurrences(self):
        schedule_qs = Schedule.objects.filter(pk=self.fiveoccurrences.pk)
        lookup = list(Schedule.objects.lookup(
            datetime.date(2014, 1, 1),
            datetime.date(2014, 12, 31),
            schedule_qs))

        expected = [
            (datetime.date(2014, 1, 29), self.fiveoccurrences, 0),
            (datetime.date(2014, 3, 26), self.fiveoccurrences, 1),
            (datetime.date(2014, 5, 28), self.fiveoccurrences, 2),
            (datetime.date(2014, 7, 30), self.fiveoccurrences, 3),
            (datetime.date(2014, 9, 24), self.fiveoccurrences, 4)
        ]

        self.assertEqual(lookup, expected)

    def test_lookup_yearly(self):
        schedule_qs = Schedule.objects.filter(pk=self.yearly.pk)
        lookup = list(Schedule.objects.lookup(
            datetime.date(2012, 1, 1),
            datetime.date(2020, 12, 31),
            schedule_qs))

        expected = [
            (datetime.date(2012, 2, 29), self.yearly, 0),
            (datetime.date(2014, 2, 28), self.yearly, 1),
            (datetime.date(2016, 2, 29), self.yearly, 2)
        ]

        # for l in lookup:
        #     print l

        self.assertEqual(lookup, expected)

    def test_occurrence_lookup(self):
        self.assertEqual(self.every2weeksmonwedfri[25], datetime.date(2014, 10, 22))
