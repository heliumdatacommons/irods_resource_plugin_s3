from boto3.session import Session
from botocore.client import Config
from botocore.handlers import set_list_objects_encoding_type_url
import boto3
import sys

# This code use a set of AWS account credentials to access an AWS bucket using
# the AssumeRole (ARN) functionality. As such, it mirrors the functionality of the
# iRODS S3 driver as enhanced to use the ARN capability, except rather than registering
# a file into the iRODS icat, this code simply retrieves the file.
# The code uses positional arguments: 
#   The name of the file with the source account credentials: often /var/lib/irods/.ssh/irods-s3-resource-1.keypair
#   The name of the file with the ARN information: often /etc/irods/irods-s3-arn.config
#   The name of AWS bucket to which we have ARN access. often nih-nhgri-datacommons
#   The file in AWS to retrieve: relative to the given bucket
#   The output path for the retrieved file
#   Example invocation:
#      python pythonARNTest.py /var/lib/irods/.ssh/irods-s3-resource-1.keypair /etc/irods/irods-s3-arn.config nih-nhgri-datacommons gtex_v7/wgs/GTEX-1117F-0003-SM-6WBT7.crai GTEX-1117F-0003-SM-6WBT7.crai

if (len(sys.argv) != 6):
   print ('wrong number of arguments: try something like')
   print ('python pythonARNTest.py /var/lib/irods/.ssh/irods-s3-resource-1.keypair /etc/irods/irods-s3-arn.config nih-nhgri-datacommons gtex_v7/wgs/GTEX-1117F-0003-SM-6WBT7.crai GTEX-1117F-0003-SM-6WBT7.crai')
   sys.exit()

# Lets grab all the args
s3_auth_file = sys.argv[1]
s3_arn_file = sys.argv[2]
s3_bucket = sys.argv[3]
file_to_get = sys.argv[4]
where_to_put_it = sys.argv[5]

# read the s3_auth_file for the existing credentials
with open(s3_auth_file) as S3_AUTH_FILE:
    lines = S3_AUTH_FILE.readlines()
lines = [thisLine.strip() for thisLine in lines]     
ACCESS_KEY=lines[0]
SECRET_KEY=lines[1]

# read the s3_arn_file for ARN info
with open(s3_arn_file) as S3_ARN_FILE:
    arn_lines = S3_ARN_FILE.readlines()
arn_lines = [thisLine.strip() for thisLine in arn_lines]     
rolearn = arn_lines[0]
duration = int(arn_lines[1])

# Get a bot client with the existing credentials
client = boto3.client('sts', aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY,
                  region_name="us-east-1")

# get the new "ARN" credentials using the original ones
assumeRoleObject = client.assume_role(RoleArn=rolearn, RoleSessionName ='NIH-Test', DurationSeconds=duration)
credentials = assumeRoleObject['Credentials']

# create a new client using the ARN credentials
s3 = boto3.client('s3',
                  aws_access_key_id = credentials['AccessKeyId'],
                  aws_secret_access_key = credentials['SecretAccessKey'],
                  aws_session_token = credentials['SessionToken'])

# Whew: finally we can download the file.
s3.download_file(s3_bucket, file_to_get, where_to_put_it)

