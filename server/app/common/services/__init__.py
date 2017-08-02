



class DbService(object):

    def __init__(self, config, db, logger):
        self.config = config
        self.db = db
        self.logger = logger

    def validate_on_submit(self, request, form):
        return request.method == 'POST' and form.validate()

    
