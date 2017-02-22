from pprint import pprint as pp

class EventMgr(object):

    def __init__(self, db, Event, EventDef):
        self._db = db
        self._Event = Event
        self._EventDef = EventDef

    def log_events(self, session):
        for target in session.new:
            self._log_event(target, 'insert')
        for target in session.dirty:
            self._log_event(target, 'update')

    def _log_event(self, target, op):
        if op not in ['update', 'insert']:
            raise ValueError('invalid operation to log event for.  can only log for insert and update')

        if op == 'insert':
            #TODO: build out the insert handler
            pass
        elif op == 'update':
            state = self._db.inspect(target)
            changes = {}

            for attr in state.attrs:
                hist = state.get_history(attr.key, True)
                if not hist.has_changes():
                    continue
                changes[attr.key] = (hist.deleted, hist.added)

            pp(changes)

            if changes is not {}:
                event_defs = self._EventDef.query.filter(self._EventDef.table == target.__tablename__,
                                                          self._EventDef.dml_op == op).all()
                if event_defs is not None:
                    for event_def in event_defs:
                        if changes.get(event_def.column, None) is not None:
                            change = changes.get(event_def.column, None)
                            if event_def.old_val is None or event_def.old_val == str(change[0][0]):
                                if event_def.new_val is None or event_def.new_val == str(change[1][0]):
                                    event = self._Event(def_id=event_def.id,
                                                  rec_id=target.id,
                                                  old_val=change[0][0],
                                                  new_val=change[1][0])
                                    self._db.session.add(event)


