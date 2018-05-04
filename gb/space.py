import boto3 
from botocore.client import Config  

from . import variables

GRADEBOOK_SPACE = session.client("s3",
                        region_name='nyc3',
                        aws_access_key_id=variables.GRADEBOOK_SPACE_ID,
                        aws_secret_access_key=variables.GRADEBOOK_SPACE_SECRET,
                        endpoint_url='https://nyc3.digitaloceanspaces.com')