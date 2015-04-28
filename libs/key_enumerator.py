import boto
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.connection import SubdomainCallingFormat
from boto.exception import S3ResponseError


class KeyEnumerator(object):
    ''' Class to assist in enumerating all keys in a bucket '''

    def __init__(self, access_key, secret_key, bucket_name):
        self.bucket_name = bucket_name
        self.keys = set()
        self.ak = access_key
        self.sk = secret_key
        self.bo = self._get_bucket_obj()
        self._get_all_keys()

    def _auth_s3(self, calling_format):
        # ordinary format req'd for non-DNS compliant named buckets
        # must specify region else get redir errors, see:
        #  https://github.com/boto/boto/issues/2836
        #  https://github.com/boto/boto/issues/443
        return boto.connect_s3(aws_access_key_id=self.ak,
                               aws_secret_access_key=self.sk,
                               calling_format=calling_format)

    def _get_bucket_obj(self):
        # try both calling formats
        try:
            s3 = self._auth_s3(calling_format=OrdinaryCallingFormat())
            bucket = s3.get_bucket(self.bucket_name)
            self.host = s3.server_name()
            return bucket
        except S3ResponseError, e:
            if e.reason == 'Moved Permanently':
                s3 = self._auth_s3(calling_format=SubdomainCallingFormat())
                bucket = s3.get_bucket(self.bucket_name)
                self.host = s3.server_name()
                return bucket

    def _get_all_keys(self):
        ''' populates self.keys with all keys; this can take a while '''
        for i in self.bo.list():
            self.keys.add(i)

    def get_keys_generator(self):
        return (i for i in self.keys)
