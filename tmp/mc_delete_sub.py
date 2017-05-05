"""
PURPOSE: deletes all selected subscribers from Marketing Cloud All Subscribers List

operates on a csv file, with the following header: SubscriberKey
-can limit operation to only the first x rows of file with second parameter 'limit'
"""

import FuelSDK
import sys
import csv

stubObj = FuelSDK.ET_Client()

def delete(filename, sk_field='SubscriberKey', limit=99999999):
    iterations = 0
    successes = 0

    with open(filename, 'r') as csvfile:
        with open(filename+'.delete-results.csv', 'w') as resultfile:
            csvfile_reader = csv.DictReader(csvfile, delimiter=',')
            result_writer = csv.DictWriter(resultfile, fieldnames=['sk', 'message', 'results'], delimiter=',')

            result_writer.writeheader()

            for row in csvfile_reader:

                try:

                    if iterations >= limit:
                        result_writer.writerow(dict(sk='null',
                                                    message='null',
                                                    results='processed' + str(iterations) + ' records, with ' + str(successes) + ' successes'))
                        return print('done: processed ' + str(iterations) + ' records, with ' + str(successes) + ' successes')
                    iterations = iterations + 1

                    sk = row[sk_field]

                    subscriber = FuelSDK.ET_Subscriber()
                    subscriber.auth_stub = stubObj
                    subscriber.props = {'SubscriberKey': sk}

                    result = subscriber.delete()

                    print('delete results of sk: ' + str(sk) + ': ' + str(result.message) + ' ' + str(result.results[0]['StatusMessage']))
                    result_writer.writerow(dict(sk=sk,
                                                message=result.message,
                                                results=result.results[0]['StatusMessage']))
                    if result.message == 'OK':
                        successes = successes + 1

                except:
                    print('*******ERROR***** on sk: ' + sk + ': ' + str(sys.exc_info[0]))
                    result_writer.writerow(dict(sk=sk,
                                                message='internal error',
                                                results=sys.exc_info()[0]))

            # clean up
            result_writer.writerow(dict(sk='null',
                                        message='null',
                                        results='processed' + str(iterations) + ' records, with ' + str(
                                            successes) + ' successes'))
            return print('done: processed ' + str(iterations) + ' records, with ' + str(successes) + ' successes')
