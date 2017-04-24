import datetime


def set_db_instance_attr(inst, attr_name, str_val):
    if not isinstance(str_val, str):
        if str_val is None:
            return None
        else:
            try:
                str_val = str(str_val)
            except Exception as exc:
                raise ValueError('str_val must be of type string.  exception: '+repr(exc))

    # determine type of db attr
    type_of_attr = str(inst.__table__.c[attr_name].type)

    try:
        return _coerce_datatype(type_of_attr, str_val)
    except Exception as exc:
        print('failed to coerce ' + attr_name + ' to ' + type_of_attr + ': ' + str(exc))

def convert_to_attr_datatype(attr, str_val):
    if not isinstance(str_val, str):
        raise ValueError('str_val must be of type string')

    # determine type of db attr
    attr_name = attr.key
    type_of_attr = str(attr.type)

    try:
        return _coerce_datatype(type_of_attr, str_val)
    except Exception as exc:
        print('failed to coerce ' + attr_name + ' to ' + type_of_attr + ': ' + str(exc))


def _coerce_datatype(type, str_val):
    # coerce str_val to desired data type
    if 'VARCHAR' in type:
        return str_val
    elif 'FLOAT' in type:
        return float(str_val)
    elif 'INTEGER' in type:
        return int(str_val)
    elif 'BOOLEAN' in type:
        return _to_boolean(str_val)
    elif 'TIMESTAMP' in type:
        return _to_timestamp(str_val)
    else:
        raise ValueError('no method implemented yet to convert to ' + type)

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
        lambda x: datetime.datetime.strptime(x[:19], '%Y-%m-%d %H:%M:%S'),
        lambda x: datetime.datetime.fromtimestamp(float(x[:-3])),
        lambda x: datetime.datetime.strptime(x, '%Y-%m-%d')
    ]

    for conversion in conversions_available:
        try:
            return conversion(str_val)
        except Exception as exc:
            exception = exc

    raise ValueError('date format not yet supported: ' + str_val)


