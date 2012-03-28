from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode

def escape_newline(value):
    '''
    Escapes newlines so that they are not lost in <textarea>.
    '''
    if len(value) >= 1 and value[0] == '\n':
        return '\n' + value
    return value

class PluralTextarea(forms.Textarea):
    '''
    Text area extension which possibly handles plurals.
    '''
    def render(self, name, value, attrs=None):
        lang, value = value

        # Need to add extra class
        attrs['class'] = 'translation'

        # Handle single item translation
        if len(value) == 1:
            return super(PluralTextarea, self).render(name, escape_newline(value[0]), attrs)

        # Okay we have more strings
        ret = []
        for idx, val in enumerate(value):
            # Generate ID
            if idx > 0:
                fieldname = '%s_%d' % (name, idx)
                attrs['id'] += '_%d' % idx
            else:
                fieldname = name

            # Render textare
            textarea = super(PluralTextarea, self).render(fieldname, escape_newline(val), attrs)
            # Label for plural
            label = lang.get_plural_label(idx)
            ret.append('<label class="plural" for="%s">%s</label><br />%s' % (attrs['id'], label, textarea))

        # Show plural equation for more strings
        pluralmsg = '<br /><span class="plural"><abbr title="%s">%s</abbr>: %s</span>' % (
            ugettext('This equation is used to identify which plural form will be used based on given count (n).'),
            ugettext('Plural equation'),
            lang.pluralequation)

        # Join output
        return mark_safe('<br />'.join(ret) + pluralmsg)

    def value_from_datadict(self, data, files, name):
        ret = [data.get(name, None)]
        for idx in range(1, 10):
            fieldname = '%s_%d' % (name, idx)
            if not fieldname in data:
                break
            ret.append(data.get(fieldname, None))
        ret = [smart_unicode(r.replace('\r', '')) for r in ret]
        if len(ret) == 0:
            return ret[0]
        return ret

class PluralField(forms.CharField):
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(PluralField, self).__init__(*args, widget = PluralTextarea, **kwargs)

    def to_python(self, value):
        # We can get list from PluralTextarea
        return value

class TranslationForm(forms.Form):
    checksum = forms.CharField(widget = forms.HiddenInput)
    target = PluralField(required = False)
    fuzzy = forms.BooleanField(label = _('Fuzzy'), required = False)

class SimpleUploadForm(forms.Form):
    file  = forms.FileField(label = _('File'))

class UploadForm(SimpleUploadForm):
    overwrite = forms.BooleanField(label = _('Overwrite existing translations'), required = False)

class ExtraUploadForm(UploadForm):
    author_name = forms.CharField(
        label = _('Author name'),
        required = False,
        help_text = _('Keep empty for using currently logged in user.')
        )
    author_email = forms.EmailField(
        label = _('Author email'),
        required = False,
        help_text = _('Keep empty for using currently logged in user.')
        )

class SearchForm(forms.Form):
    q = forms.CharField(label = _('Query'))
    exact = forms.BooleanField(label = _('Exact match'), required = False, initial = False)
    src = forms.BooleanField(label = _('Search in source strings'), required = False, initial = True)
    tgt = forms.BooleanField(label = _('Search in target strings'), required = False, initial = True)
    ctx = forms.BooleanField(label = _('Search in context strings'), required = False, initial = False)

class MergeForm(forms.Form):
    checksum = forms.CharField()
    merge = forms.IntegerField()

class AutoForm(forms.Form):
    overwrite = forms.BooleanField(label = _('Overwrite entries'), required = False, initial = False)
    subproject = forms.ChoiceField(label = _('Subproject to use'), required = False, initial = '')

    def __init__(self, obj, *args, **kwargs):
        choices = [(s.slug, s.name) for s in obj.subproject.project.subproject_set.exclude(id = obj.subproject.id)]
        super(AutoForm, self).__init__(*args, **kwargs)
        self.fields['subproject'].choices = [('', _('All subprojects'))] + choices
