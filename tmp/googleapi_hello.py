"""Hello Analytics Reporting API V4."""
# http://daynebatten.com/2015/07/raw-data-google-analytics/
# pip install google-api-python-client

import argparse
import sys

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools


SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
KEY_FILE_LOCATION = 'bluenilesw-app-f937c2e51267.p12'
SERVICE_ACCOUNT_EMAIL = 'bluenile-sw-google-analytics@bluenilesw-app.iam.gserviceaccount.com'
VIEW_ID = '122242971'


def initialize_analyticsreporting():
  """Initializes an analyticsreporting service object.

  Returns:
    analytics an authorized analyticsreporting service object.
  """

  credentials = ServiceAccountCredentials.from_p12_keyfile(
    SERVICE_ACCOUNT_EMAIL, KEY_FILE_LOCATION, scopes=SCOPES)

  http = credentials.authorize(httplib2.Http())

  # Build the service object.
  analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

  return analytics


def get_report(analytics):
  # Use the Analytics Service Object to query the Analytics Reporting API V4.

  # metrics: ga:sessions, ga:pageValue, ga:pageViews
  # dims: ga:dimension1, ga:dimension3, ga:dimension2, ga:pagePath

  # metrics: transactions, totalValue, itemQuantity, productDetailViews
  # dims: dim1/2/3

  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '1daysAgo', 'endDate': 'today'}],
          'metrics': [
            {'expression': 'ga:totalValue'},
            {'expression': 'ga:itemQuantity'},
            {'expression': 'ga:productDetailViews'}
          ],
          'dimensions': [
            {'name': 'ga:dimension1'},
            {'name': 'ga:dimension3'},
            {'name': 'ga:dimension2'},
            {'name': 'ga:metro'},
            {'name': 'ga:operatingSystem'},
            {'name': 'ga:region'},
            {'name': 'ga:country'}
          ]
        }]
      }
  ).execute()


def print_response(response):
  """Parses and prints the Analytics Reporting API V4 response"""

  for report in response.get('reports', []):
    columnHeader = report.get('columnHeader', {})
    dimensionHeaders = columnHeader.get('dimensions', [])
    metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
    rows = report.get('data', {}).get('rows', [])

    for row in rows:
      dimensions = row.get('dimensions', [])
      dateRangeValues = row.get('metrics', [])

      for header, dimension in zip(dimensionHeaders, dimensions):
        print(header + ': ' + dimension)

      for i, values in enumerate(dateRangeValues):
        print('Date range (' + str(i) + ')')
        for metricHeader, value in zip(metricHeaders, values.get('values')):
          print(metricHeader.get('name') + ': ' + value)


def main():

  analytics = initialize_analyticsreporting()
  response = get_report(analytics)
  from pprint import pprint as pp
  pp(response)
  print_response(response)

if __name__ == '__main__':
  main()
