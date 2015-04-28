#!/usr/bin/env python

''' Find all public files in all s3 buckets
related: netflix security monkey --> https://github.com/Netflix/security_monkey,
specifically --> https://github.com/Netflix/security_monkey/blob/master/security_monkey/auditors/s3.py
'''

import sys
import yaml
import argparse
import random
from Queue import Queue
from threading import Thread
from datetime import datetime
from boto.exception import S3ResponseError
from libs.key_enumerator import KeyEnumerator
from libs.utils import insert_mdb
from libs.utils import get_buckets
from libs.utils import setup_logging
from libs.utils import key_is_public
from pymongo import MongoClient


def audit_perms(q, **kwargs):
    ''' audit permissions function '''
    while True:
        job = q.get()
        # unwrap
        aname = job['aname']
        bname = job['bname']
        ke = job['ke']
        key = job['key']
        host = ke.host
        logging = kwargs['logging']
        iter_dt = kwargs['iter_dt']
        col = kwargs['mongocol']
        fullq = kwargs['fullq']

        try:
            if key_is_public(key):
                # if true, write to mongo
                url = 'https://{host}/{bucket}/{key}'.format(
                    host=host, bucket=bname, key=key.name)
                document = {'account': aname,
                            'iter_dt': iter_dt,
                            'url': url,
                            'key': key.name,
                            'bucket': bname}
                insert_mdb(document, col)
        except S3ResponseError, e:
            # this is a bug ref: https://github.com/boto/boto/issues/2824
            # we just pass this. you might wanna manually check this.
            if e.reason == 'Not Found':
                logging.info('[S3A] - Couldnt find key "{}"'.format(
                    str(key.name)))
        except:
            logging.error('[S3A] - Unknown error: {}'.format(
                sys.exc_info()))

        if random.randint(0, 99) == 24:
            # meh. every once in a while ...
            percent = (float(fullq) - float(q.qsize())) / float(fullq)
            logging.info('[S3A] - Working.. Progress {:.3f}% - {} of {} left'.format(
                percent * 100, q.qsize(), fullq))
        q.task_done()


def main(config):

    logging = setup_logging(config)
    logging.info('Audit Started')
    iter_dt = datetime.utcnow()  # same datetime for all docs this iteration

    q = Queue(maxsize=0)
    num_threads = 10

    accounts = config['aws_accounts']
    logging.info('[S3A] - Will work on {:d} AWS accounts.'.format(
        len(accounts)))

    # find which buckets not to use
    ignore_buckets = config['ignore_buckets']

    # populate the queue
    for a in accounts:
        c = 0
        ak = a['key']
        sk = a['secret']
        a_name = a['name']
        logging.info('[S3A] - Enumerating buckets for account "{:s}"'.format(
            a_name))
        buckets = get_buckets(a)
        for b in buckets:
            if b.name in ignore_buckets:
                logging.info('[S3A] - Ignoring bucket: {:s}'.format(b.name))
                continue
            logging.info('[S3A] - Current queue size: {:d}'.format(q.qsize()))
            logging.info('[S3A] - Working on bucket: {:s}'.format(b.name))
            name = b.name
            try:
                ke = KeyEnumerator(ak, sk, name)
            except:
                # there are issues w/ frankfurt buckets
                # https://github.com/boto/boto/issues/2741
                # no good way to find locations atm, so passing on this.
                logging.error('[S3A] - Issue connecting to bucket: {}'.format(
                    b.name))
                continue
            for i in ke.get_keys_generator():
                c += 1
                q.put({'aname': a_name,
                       'ke': ke,
                       'key': i,
                       'bname': name})
        logging.info('[S3A] - Added {:d} keys for {:s}'.format(c, a_name))

    # full q size
    qsize = q.qsize()

    # get a mongo collection object
    client = MongoClient()
    col = client['s3audit']['results']

    # mark all findings w/ the same iter_dt
    logging.info('[S3A] - Starting. Set will be tagged w/ iter_dt {:s}'.format(
        str(iter_dt)))

    # setup the worker threads
    for i in range(num_threads):
        worker = Thread(target=audit_perms,
                        args=(q,),
                        kwargs={'logging': logging,
                                'mongocol': col,
                                'iter_dt': iter_dt,
                                'fullq': qsize})
        worker.setDaemon(True)
        worker.start()

    q.join()
    logging.info('[S3A] - Donezo')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='S3 Key Permissions Auditor')
    parser.add_argument('-c', '--config', dest='config', required=True,
                        help='(Required) YAML configuration file')
    args = parser.parse_args()

    try:
        config = yaml.load(open(args.config, 'r').read())
    except:
        print 'Could not load config file: "{}"'.format(str(sys.exc_info()[1]))
        sys.exit(1)

    main(config=config)
