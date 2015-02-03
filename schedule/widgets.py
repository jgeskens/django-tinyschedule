from django.forms.widgets import Widget, HiddenInput
from django.utils.safestring import mark_safe
from .forms import ScheduleForm
from .models import Schedule


class ScheduleWidget(Widget):
    def __init__(self, attrs=None):
        super(ScheduleWidget, self).__init__(attrs=attrs)
        self.form_class = ScheduleForm

    def render(self, name, value, attrs=None):
        if value is None:
            schedule = None
        else:
            schedule = Schedule.objects.get(pk=value)

        form = self.form_class(prefix=u'%s_form' % name, instance=schedule)
        hidden_input = HiddenInput().render(name='%s_form_original_pk' % name, value=value or '')
        output = u'\n'.join((form.as_p(), hidden_input))
        return mark_safe(output)

    def value_from_datadict(self, data, files, name):
        prefix = u'%s_form' % name
        original_pk_raw = data.get('%s_form_original_pk' % name)
        instance = Schedule.objects.get(pk=int(original_pk_raw)) if original_pk_raw else None
        form = self.form_class(data, prefix=prefix, instance=instance)

        if form.is_valid():
            schedule = form.save()
            return schedule.pk
        else:
            if original_pk_raw:
                return int(original_pk_raw)
            else:
                return None
