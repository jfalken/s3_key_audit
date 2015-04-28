# S3 Key Auditor

## What is this?

This tool enumerates every key (i.e., file) in s3 for the specified account and checks the permissions of each key to identify if its publicly accessible.

If it is, the results are stored in mongodb. You can create a csv document of a tool's output using the `make_csv.py` script.

### Why do we need to do this?

Buckets can have top level permissions making them public, or private. However, even if you specify a bucket to be private and require authentication or pre-signed URLs to access, any key within that bucket can still have overiding security permissions. Therefore, it becomes necessary to check the permissions of every single key if you wish to identify all public files.

### I want some things public

The config file lets you exclude specified bucket(s).

### How fast is this? I got tons'o'keys

There are two phases. 

First we enumerate all the keys and throw them on a queue. This is single threaded but relatively fast (2 million keys should take about 10 minutes to queue up). 

Then, a number of threads are kicked off to work on the queue. With 20 threads, checking 2 million keys takes about 1 hour. 

These numbers are based off my local on a Mac Book Pro w/ 16GB RAM and decent Internet connection. The script defaults to 10 threads, feel free to up that number if you have the horsepower. See under `Misc` for how to do this.

## Usage

`s3_auditor.py -c config.yaml`

You can tail the log file (default name: `s3_grants_audit.log`) to see the current status. When the audit starts, a % completion is given. 


## Installation

This tool is a python script. Results are stored in a local MongoDB instance.

### Pre-Req

* Python 2.7
* MongoDB Installed and Running locally [docs](http://docs.mongodb.org/manual/installation/) or [downloads](https://www.mongodb.org/downloads)
* AWS API Credentials for the account you want to audit. [S3 Read-Only Permissions](http://docs.aws.amazon.com/directoryservice/latest/adminguide/role_s3_read_only.html) are required.

### Environment Setup

* Preferabbly in a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/), install all required dependencies

  `pip install -r requirements.txt`

### Edit the config file

* Located in `config/config.yaml`
* Edit AWS Account info:

```
aws_accounts:
    - name: account1
      key: aws_access_key
      secret: secret
    - name: account2
      key: aws_access_key
      secret: secret
``` 

 Place the API access key ID in `key`. Place the secret access token in `secret`. If you have multiple accounts, list them all here. If just one account, remove the second example.

* Edit excluded bucket list

```
ignore_buckets:
    - bucket1
    - bucket-2
    - bucket.name.3
    - "bucket4"
```

If you wish to exclude any buckets from being checked, do so here. If you have no exclusions, you can leave this list as-is.

## Results

All results are stored in MongoDB. Database name is `s3audit` and the collection name is `results`. The result documents look like:

```js
{
  "_id": ObjectId("5523efb9be76733942495be1"),
  "account": "AWS Account Name",
  "iter_dt": ISODate("2015-04-07T14:54:00.899Z"),
  "url": "https://s3.amazonaws.com/path/to/file.tgz",
  "bucket": "Bucketname",
  "key": "file.tgz"
}
```

The field `iter_dt` (i.e., iteration datetime) is used to group together all findings from a single run. In other words, results from each distinct run of the script will all have the same iter_dt value. This is used by the csv generation script to identify runs.

## CSV Output

When a run has completed, a convenient way to view results is to generate a CSV.

You can use the `make_csv.py` script to generate a CSV off prior runs. When you run this script, it will connect to MongoDB and find distinct runs via their `iter_dt` field. Select which one you want to generate a CSV and a file will be written.

```bash
(venv)chris:s3_key_audit/ (master✗) $ ./make_csv.py


Showing most recent 20 runs.
Select which run you want to export:

	[0] - "2015-04-09 13:24:44.593000" (48734 entries)
	[1] - "2015-04-08 21:17:38.076000" (227 entries)
	[2] - "2015-04-08 18:50:08.544000" (227 entries)
	[3] - "2015-04-08 17:29:55.827000" (227 entries)
	[4] - "2015-04-08 13:58:35.228000" (45 entries)

 Select a number:
: 2
Done. Filename is "s3_audit_public_1429751124.03.csv"
```

## Contributing

Issues should be created using GitHub issues. If you have an addition, please fork and submit a pull request.

## License 

Copyright 2015 Chris Sandulow

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
