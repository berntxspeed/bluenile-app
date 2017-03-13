import datetime


def set_db_instance_attr(inst, attr_name, str_val):
    if not isinstance(str_val, str):
        raise ValueError('str_val must be of type string')

        # determine type of db attr
    type_of_attr = str(inst.__table__.c[attr_name].type)

    try:
        # coerce str_val to desired data type
        if 'VARCHAR' in type_of_attr:
            return str_val
        elif 'FLOAT' in type_of_attr:
            return float(str_val)
        elif 'INTEGER' in type_of_attr:
            return int(str_val)
        elif 'BOOLEAN' in type_of_attr:
            return _to_boolean(str_val)
        elif 'TIMESTAMP' in type_of_attr:
            return _to_timestamp(str_val)
        else:
            raise ValueError('no method implemented yet to convert to ' + type_of_attr)

    except Exception as exc:
        print('failed to coerce ' + attr_name + ' to ' + type_of_attr + ': ' + str(exc))


def _to_boolean(str_val):
    true_vals = ['y', 'yes', 't', 'true', '1', 'p', 'pos', 'positive', 'paid']
    false_vals = ['n', 'no', 'f', 'false', '0', 'n', 'neg', 'negative', 'unpaid', None, '']
    if str_val.lower() in true_vals:
        return True
    elif str_val.lower() in false_vals:
        return False
    else:
        raise ValueError('unrecognized string for boolean conversion: ' + str_val)


def _to_timestamp(str_val):
    exception = None

    conversions_available = [
        lambda x: datetime.datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p'),
        lambda x: datetime.datetime.strptime(x[:19], '%Y-%m-%dT%H:%M:%S'),
        lambda x: datetime.datetime.fromtimestamp(float(x[:-3]))
    ]

    for conversion in conversions_available:
        try:
            return conversion(str_val)
        except Exception as exc:
            exception = exc

    raise ValueError('date format not yet supported: ' + str_val)


