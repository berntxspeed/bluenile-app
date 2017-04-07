#TODO: don't watch any changes on Event
#TODO: build front end connection so users can input event defs and report on events
#TODO: enable more deta-type sensitive checking to happen
#handle the case where it goes from null to something (as opposed to <doesnt matter> to something)

from pprint import pprint as pp

class EventMgr(object):

    def __init__(self, db, Event, EventDef):
        self._db = db
        self._Event = Event
        self._EventDef = EventDef
        self._event_defs = None

    def log_insert_events(self, session):
        self.refresh_event_defs()
        for target in session.new:
            self._log_event(target, 'insert')

    def log_update_events(self, session):
        self.refresh_event_defs()
        for target in session.dirty:
            self._log_event(target, 'update')

    def refresh_event_defs(self):
        self._event_defs = self._get_event_defs()

    def _log_event(self, target, op):
        if op not in ['update', 'insert']:
            raise ValueError('invalid operation to log event for.  can only log for insert and update')

        state = self._db.inspect(target)
        changes = {}

        for attr in state.attrs:
            hist = state.get_history(attr.key, True)
            if not hist.has_changes():
                continue
            changes[attr.key] = (hist.deleted, hist.added)

        # pp(changes)

        if changes is not {}:
            if self._event_defs is None:
                self._event_defs = self._get_event_defs()
            event_defs = None
            if self._event_defs.get(target.__tablename__, None) is not None:
                event_defs = [edef for edef in self._event_defs.get(target.__tablename__) if edef.dml_op == op]

            if event_defs is not None:
                for event_def in event_defs:
                    if event_def.dml_op == 'insert':
                        if event_def.column is not None:
                            change = changes.get(event_def.column, None)
                            newVal = safe_list_get(change, 1, None)
                            if event_def.new_val is None \
                                            or (event_def.new_val == str(safe_list_get(newVal, 0, None))) \
                                            or (event_def.new_val == 'notnull' and newVal != None)\
                                            or (event_def.new_val == 'null' and newVal == None):
                                event = self._Event(def_id=event_def.id,
                                                    rec_id=target.id,
                                                    new_val=safe_list_get(newVal, 0, None))
                                self._db.session.add(event)
                        else:
                            event = self._Event(def_id=event_def.id,
                                                rec_id=target.id)
                            self._db.session.add(event)
                    elif event_def.dml_op == 'update':
                        change = changes.get(event_def.column, None)
                        oldVal = safe_list_get(safe_list_get(change, 0, None), 0, None)
                        newVal = safe_list_get(safe_list_get(change, 1, None), 0, None)
                        if event_def.old_val is None \
                                        or (event_def.old_val == str(oldVal)) \
                                        or (event_def.old_val == 'notnull' and oldVal != None) \
                                        or (event_def.old_val == 'null' and oldVal == None):
                            if event_def.new_val is None \
                                            or (event_def.new_val == str(newVal)) \
                                            or (event_def.new_val == 'notnull' and newVal != None) \
                                            or (event_def.new_val == 'null' and newVal == None):
                                if oldVal != newVal:
                                    event = self._Event(def_id=event_def.id,
                                                  rec_id=target.id,
                                                  old_val=safe_list_get(oldVal, 0, None),
                                                  new_val=safe_list_get(newVal, 0, None))
                                    self._db.session.add(event)

    def _get_event_defs(self):
        edefs = {}
        for edef in self._EventDef.query.all():
            if edef.table not in edefs.keys():
                edefs[edef.table] = [edef]
            else:
                edefs.get(edef.table).append(edef)
        return edefs

def safe_list_get (l, idx, default):
  try:
    return l[idx]
  except:
    return default