import csv


# this appends zip codes to AreaCode field of EmlOpen and EmlClick tables
# it assumes the values of city are all caps w no spaces like this SANMATEO

def append_zipcodes(db, model, filename):

    with open(filename, 'r') as csvfile:
        csvfile_reader = csv.DictReader(csvfile, delimiter=',')
        already_processed = []

        # using city names without spaces
        for row in csvfile_reader:

            if (row['City'], row['State']) in already_processed:
                continue

            already_processed.append((row['City'], row['State']))

            recs = model.query.filter(model.City == row['City'].replace(' ', ''), model.Region == row['State']).all()
            print('*', end='', flush=True)
            if len(recs) > 0:
                print('found ' + str(len(recs)) + ' records with city ' + row['City'].replace(' ', ''))
                for rec in recs:
                    rec.AreaCode = row['ZipCode']
                    db.session.add(rec)
                db.session.commit()



def append_zipcodes2(db, model, filename):

    with open(filename, 'r') as csvfile:
        csvfile_reader = csv.DictReader(csvfile, delimiter=',')
        already_processed = []

        # using city names without spaces
        for row in csvfile_reader:

            if (row['Place Name'], row['State Abbreviation']) in already_processed:
                continue

            already_processed.append((row['Place Name'], row['State Abbreviation']))

            recs = model.query.filter(model.City == row['Place Name'].replace(' ', '').upper(), model.Region == row['State Abbreviation']).all()
            print('*', end='', flush=True)
            if len(recs) > 0:
                print('found ' + str(len(recs)) + ' records with city ' + row['Place Name'].replace(' ', ''))
                for rec in recs:
                    rec.AreaCode = row['Postal Code']
                    db.session.add(rec)
                db.session.commit()

# this one works with the fips_codes_website.csv file - which has the right FIPS values to match
# - up with the ids of the us-10m.v1.json data from D3
def append_zipcodes3(db, model, filename):

    with open(filename, 'r') as csvfile:
        csvfile_reader = csv.DictReader(csvfile, delimiter=',')
        already_processed = []

        # using city names without spaces
        for row in csvfile_reader:

            if (row['GU Name'], row['State Abbreviation']) in already_processed:
                continue

            already_processed.append((row['GU Name'], row['State Abbreviation']))

            recs = model.query.filter(model.City == row['GU Name'].replace(' ', '').upper(), model.Region == row['State Abbreviation']).all()
            print('*', end='', flush=True)
            if len(recs) > 0:
                print('found ' + str(len(recs)) + ' records with city ' + row['GU Name'].replace(' ', ''))
                for rec in recs:
                    rec.AreaCode = row['State FIPS Code'] + row['County FIPS Code']
                    db.session.add(rec)
                db.session.commit()