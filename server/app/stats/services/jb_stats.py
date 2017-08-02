from flask import url_for
from flask import flash
from flask import redirect

from ...common.services import DbService
from ...common.models import User

from bson.objectid import ObjectId

class JbStatsService(DbService):

    def __init__(self, config, db, logger, mongo):
        super(JbStatsService, self).__init__(config, db, logger)
        self.mongo = mongo

    def special_logged_in_page(self, request, session):
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

    def journey_view(self):
        journeys = []
        for j in self.mongo.db.journeys.find():
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

    def journey_detail(self, id):
        journey = self.mongo.db.journeys.find_one_or_404({'_id': ObjectId(id)})
        journey['_id'] = str(journey['_id'])
        return journey


