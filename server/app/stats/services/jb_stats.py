from flask import url_for
from flask import flash
from flask import redirect

from ...common.services import DbService
from ...common.models.system_models import User

from bson.objectid import ObjectId


class JbStatsService(DbService):

    def __init__(self, config, db, logger, mongo):
        super(JbStatsService, self).__init__(config, db, logger)
        self.mongo = mongo

    @staticmethod
    def special_logged_in_page(request, session):
        facebook_id = session.get('facebook_id')
        if facebook_id:
            user = User.query.filter_by(facebook_id=facebook_id).first()
        else:
            return { 'status': 'no facebook_id found' }
        if user is None:
            return { 'status': 'no user found at that facebook_id' }
        return {
            'email': user.email,
            'fb_id': facebook_id
        }

    def journey_view(self, user_config=None):
        journeys = []

        if user_config is not None:
            collection = self.mongo.db['journeys_' + self.user_config.get('account_name', '')]
        else:
            collection = self.mongo.db.journeys

        for j in collection.find():
            journeys.append({
                '_id': j['_id'],
                'name': j['name']
            })
        if len(journeys) < 1:
            flash('Error: no journeys found. check that journey data has been synced with Email Platform.')
            return {'error': 'No Journeys Found'}
        return {
            'journeys': journeys
        }

    def journey_detail(self, id, user_config=None):

        if user_config is not None:
            collection = self.mongo.db['journeys_' + self.user_config.get('account_name', '')]
        else:
            collection = self.mongo.db.journeys

        journey = collection.find_one_or_404({'_id': ObjectId(id)})
        journey['_id'] = str(journey['_id'])
        return journey
