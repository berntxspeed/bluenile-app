import hashlib
import csv

def hash_csvfile(filename, fields):
    """
    :param filename: 'filename.csv'
    :param fields:  ['field', 'field', ...]
    :return: None (just console output)
    """
    with open(filename, 'r') as csvfile:
        with open(filename+'.hash', 'w') as hashed_csvfile:
            csvfile_reader = csv.DictReader(csvfile, delimiter=',')
            csvfile_writer = csv.DictWriter(hashed_csvfile, fieldnames=csvfile_reader.fieldnames, delimiter=',')

            csvfile_writer.writeheader()
            for row in csvfile_reader:
                for field in fields:
                    row[field] = hashlib.md5(row[field].encode()).hexdigest()
                csvfile_writer.writerow(row)

