from wtforms import ValidationError

from .messages import MAX_LENGTH_MSG
from .messages import MAX_LENGTH_REAL_TIME_MSG
from .messages import MIN_LENGTH_MSG

class MinLength(object):

    def __init__(self, min, message=None):
        self.min = min
        self.message = message

    def __call__(self, form, field):
        if len(field.data) < self.min:
            if self.message is None:
                message = MIN_LENGTH_MSG % {'min': self.min, 'label': field.label.text.lower()}
            else:
                message = self.message % {'min': self.min}
            raise ValidationError(message)


class MaxLength(object):

    def __init__(self, max, message=None, real_time=False,
                 real_time_message=MAX_LENGTH_REAL_TIME_MSG):
        self.max = max
        self.message = message
        self.real_time = real_time
        self.real_time_message = real_time_message

    def __call__(self, form, field):
        if len(field.data) > self.max:
            if self.message is None:
                message = MAX_LENGTH_MSG % {'max': self.max, 'label': field.label.text.lower()}
            else:
                message = self.message % {'max': self.max}
            raise ValidationError(message)
