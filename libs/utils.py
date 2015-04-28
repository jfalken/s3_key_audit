import logging
import boto


def setup_logging(config):
    logging.basicConfig(filename=config['log']['file'],
                        format=config['log']['format'],
                        datefmt=config['log']['dateformat'],
                        level=logging.INFO)
    logging.getLogger('requests').propagate = False
    return logging


def get_buckets(account):
    ''' using an account dict from the config, return a list of
        s3 buckets in that account
        returns a generator of bucket objects
    '''
    ak = account['key']
    sk = account['secret']
    s3 = boto.connect_s3(ak, sk)
    return (i for i in s3.get_all_buckets())


def key_is_public(key):
    ''' checks all grants for a key object
        returns boolean if key is publicly available
    '''
    # http://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html
    PUBLIC = 'http://acs.amazonaws.com/groups/global/AllUsers'
    AUTHUSERS = 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers'
    LOGGING = 'http://acs.amazonaws.com/groups/s3/LogDelivery'
    try:
        for g in key.get_acl().acl.grants:
            if g.uri == PUBLIC:
                return True
            else:
                continue
        return False
    except:
        raise


def insert_mdb(document, mongodb_col):
    ''' inserts document in mongodb_col '''
    mongodb_col.insert(document)
    mongodb_col.ensure_index('iter_dt')
    mongodb_col.ensure_index('account')
    mongodb_col.ensure_index('bucket')
    return
