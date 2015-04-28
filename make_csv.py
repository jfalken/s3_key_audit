#!/usr/bin/env python

import csv
import sys
import time
from pymongo import MongoClient


def get_id_count(iter_dt, col):
    ''' returns the count of objects for iter_dt '''
    c = col.find({'iter_dt': iter_dt})
    try:
        return c.count()
    except:
        return 0


def setup_csv():
    ''' init and return a csv writer object '''
    filename = 's3_audit_public_{:s}.csv'.format(str(time.time()))
    fh = open(filename, 'w')
    c = csv.writer(fh)
    header = ['Account', 'Bucket', 'URL', 'Key']
    c.writerow(header)
    return c, filename


def main():
    client = MongoClient()
    col = client['s3audit']['results']

    # list most recent iterations
    ids = col.distinct('iter_dt')
    ids = ids[::-1]  # chronological
    ids = ids[:20]  # limit to 20 recent runs

    print '\nShowing most recent 20 runs.'
    print 'Select which run you want to export: \n'
    for i, idt in enumerate(ids):
        print '\t[{number}] - "{iter_dt}" ({c:d} entries)'.format(
            number=i, iter_dt=str(idt), c=get_id_count(idt, col))
    print '\n Select a number:'

    resp = raw_input(': ')
    try:
        assert int(resp.strip()) in range(len(ids))
    except:
        print 'Invalid selection'
        sys.exit(0)

    # write the output
    docs = col.find({'iter_dt': ids[int(resp.strip())]})
    csvw, filename = setup_csv()
    for d in docs:
        row = [d['account'], d['bucket'], d['url'], d['key']]
        csvw.writerow(row)

    print 'Done. Filename is "{}"'.format(filename)

if __name__ == '__main__':
    main()