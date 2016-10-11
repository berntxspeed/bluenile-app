from flask.ext.wtf import Form
from werkzeug.datastructures import MultiDict
from wtforms import SelectMultipleField
from wtforms.widgets import CheckboxInput
from wtforms.widgets import ListWidget

from .messages import MAX_LENGTH_MSG
from .messages import MIN_LENGTH_MSG

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

def strip_filter(value):
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value

class BaseForm(Form):

    class Meta:
        def bind_field(self, form, unbound_field, options):
            filters = unbound_field.kwargs.get('filters', None) or []
            filters.append(strip_filter)
            return unbound_field.bind(form=form, filters=filters, **options)

    def __init__(self, data, *args, **kwargs):
        # Strip extra newline so that backend length validation matches with the client
        cleaned_data = MultiDict()
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_data[key] = value.replace('\r\n', '\n')
        Form.__init__(self, cleaned_data, csrf_enabled=False, *args, **kwargs)

    def json_data(self, onkeyup=False):
        rules = {}
        messages = {}
        extras = {}
        for field_name, field in self._fields.items():
            rule = {}
            message = {}
            extra = {}
            exists = True

            if not field.validators:
                continue

            # Disable validation for unsupported fields
            if field.__class__.__name__ == 'MultiCheckBoxField':
                continue

            for validator in field.validators:
                v_name = validator.__class__.__name__
                if v_name == 'Required':
                    rule['required'] = True
                    message['required'] = validator.message
                elif v_name == 'MinLength':
                    rule['minlength'] = validator.min
                    if validator.message is None:
                        min_length_msg = MIN_LENGTH_MSG % { 'min': validator.min,
                                                            'label': field.label.text.lower() }
                    else:
                        min_length_msg = validator.message % { 'min': validator.min }
                    message['minlength'] = min_length_msg
                elif v_name == 'MaxLength':
                    rule['maxlength'] = validator.max
                    if validator.message is None:
                        max_length_msg = MAX_LENGTH_MSG % {'max': validator.max,
                                                           'label': field.label.text.lower()}
                    else:
                        max_length_msg = validator.message % {'max': validator.max}
                    message['maxlength'] = max_length_msg
                    if validator.real_time:
                        extra['realTime'] = validator.real_time_message
                elif v_name == 'Regexp':
                    rule['regex'] = validator.regex.pattern
                    message['regex'] = validator.message
                elif v_name == 'Email':
                    rule['email'] = True
                    message['email'] = validator.message
                elif v_name == 'EqualTo':
                    rule['equalTo'] = '#' + validator.fieldname
                    message['equalTo'] = validator.message
                elif v_name == 'URL':
                    rule['url'] = True
                    message['url'] = validator.message

            if rule:
                rules[field_name] = rule

            if message:
                messages[field_name] = message

            if extra:
                extras[field_name] = extra

        return {
            'rules': rules,
            'messages': messages,
            'extras': extras,
            'onkeyup': onkeyup,
        }
