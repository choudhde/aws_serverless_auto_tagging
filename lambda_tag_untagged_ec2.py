####
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
####
__author__ = 'dc'

import boto3
import sys
import os
import time
from botocore.exceptions import ClientError


# List every region you'd like to scan.  
aws_regions = ['ca-central-1', 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
               'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3', 'ap-south-1',
               'ap-southeast-1', 'ap-southeast-2',
               'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3']

# Global variables for Keys and Values to be tagged to each instances and volumes
key_backup = str(os.getenv('KEY_BACKUP'))
val_backup = str(os.getenv('VAL_BACKUP'))

key_lob = str(os.getenv('KEY_LOB'))
val_lob = str(os.getenv('VAL_LOB'))

key_cost = str(os.getenv('KEY_COST'))
val_cost = str(os.getenv('VAL_COST'))

key_ms = str(os.getenv('KEY_MS'))
val_ms = str(os.getenv('VAL_MS'))

key_ms_group = str(os.getenv('KEY_MS_GROUP'))
val_ms_group = str(os.getenv('VAL_MS_GROUP'))

key_workload = str(os.getenv('KEY_WORKLOAD'))
val_workload = str(os.getenv('VAL_WORKLOAD'))

key_data_classification = str(os.getenv('KEY_DATA_CLASSIFICATION'))
val_data_classification = str(os.getenv('VAL_DATA_CLASSIFICATION'))

key_env = str(os.getenv('KEY_ENV'))
val_env = str(os.getenv('VAL_ENV'))

key_client = str(os.getenv('KEY_CLIENT'))
val_client = str(os.getenv('VAL_CLIENT'))

Filters = ['terminated', 'terminating']

key_type = ''
owner_id = str(os.getenv('OWNER_ID'))


#############################
# Check instances with no tag
#############################

def tag_instance(ec2, aws_region):
    key_type = 'instancetype'

    try:
        reservations = ec2.describe_instances()['Reservations']
    except:
        # Don't fatal error on regions that we haven't activated/enabled
        if 'OptInRequired' in str(sys.exc_info()):
            return
        else:
            raise
    time.sleep(2)
    try:

        for reservation in reservations:
            for instance in reservation['Instances']:
                if instance['State']['Name'] not in Filters:
                    tags = {}
                    try:
                        for tag in instance['Tags']:
                            tags[tag['Key']] = tag['Value']
                    except Exception as e:
                        # If all tags are missing
                        print("Found instance without any " + str(e))
                    # Check for only key:Name, and tag it with InstanceId if missing
                    if not ('Name' in tags):
                        print("Instance without key:Name and Value")
                        ec2.create_tags(Resources=[instance['InstanceId']],
                                        Tags=[{'Key': 'Name', 'Value': instance['InstanceId']}])
                        print("Key:Name added with Value: {}\n".format(instance['InstanceId']))
                    # Run this function if  tags are missing
                    missing_tags(tags, instance['InstanceId'], instance['InstanceType'], key_type, ec2,
                                        aws_region)

    except Exception:
        print("Unexpected error:", sys.exc_info()[0])


#######################################
# Function to Tag Volumes
#######################################

def tag_vol(ec2, aws_region):
    key_type = 'volumetype'

    try:
        reservations = ec2.describe_volumes()['Volumes']
    except:
        # Don't fatal error on regions that we haven't activated/enabled
        if 'OptInRequired' in str(sys.exc_info()):
            return
        else:
            raise
    time.sleep(2)
    try:
        for volume in reservations:
            tags = {}
            try:
                for tag in volume['Tags']:
                    tags[tag['Key']] = tag['Value']
            except Exception as e:
                # If all tags are missing
                print("Found volume without any " + str(e))
            # Check for only key:Name, and tag it with InstanceId
            for v in volume['Attachments']:
                if not ('Name' in tags):
                    print("Volume without key:Name and Value")
                    ec2.create_tags(Resources=[v['VolumeId']],
                                    Tags=[{'Key': 'Name', 'Value': v['InstanceId']}])
            # Run this function if tags are missing
            missing_tags(tags, volume['VolumeId'], volume['VolumeType'], key_type, ec2, aws_region)

    except Exception:
        print("Unexpected error:", sys.exc_info()[0])


#######################################
# Function to Tag Snapshots
#######################################

def tag_snapshots(ec2, aws_region):
    key_type = 'encrypted_state'

    try:
        reservations = ec2.describe_snapshots()['Snapshots']
    except:
        # Don't fatal error on regions that we haven't activated/enabled
        if 'OptInRequired' in str(sys.exc_info()):
            return
        else:
            raise
    time.sleep(2)
    try:
        for snapshot in reservations:
            tags = {}
            if snapshot['OwnerId'] == owner_id:
                try:
                    for tag in snapshot['Tags']:
                        tags[tag['Key']] = tag['Value']
                except Exception as e:
                    # If all tags are missing
                    print("Found snapshots without any " + str(e))
                # Check for only key:Name, and tag it with VolumeId
                if not ('Name' in tags):
                    print("Snapshot without key:Name and Value")
                    if snapshot['VolumeId'] == 'vol-ffffffff':
                        ec2.create_tags(Resources=[snapshot['SnapshotId']],
                                        Tags=[{'Key': 'Name', 'Value': snapshot['SnapshotId']}])
                    else:
                        ec2.create_tags(Resources=[snapshot['SnapshotId']],
                                        Tags=[{'Key': 'Name', 'Value': snapshot['VolumeId']}])
                # Run this function if tags are missing
                missing_tags(tags, snapshot['SnapshotId'], str(snapshot['Encrypted']), key_type, ec2,
                                    aws_region)

    except Exception:
        print("Unexpected error:", sys.exc_info()[0])


######################################################
# Function missing_tags - When Tags are missing
######################################################

def missing_tags(tags, resource_id, resource_type, key_type, ec2, aws_region):
    # If all tags are found as per compliance
    if ('line_of_business' in tags) and ('cost_centre' in tags) \
            and (key_type in tags) and ('client' in tags) and ('environment' in tags):
        print("Id: {}; Region {}: properly tagged with line_of_business, cost_centre, "
              "client and {}".format(resource_id, aws_region, key_type))
    # If tags missing call function to add them
    else:
        print("Id: {}; Region: {} not tagged as per standards".format(resource_id, aws_region))
        add_name_tag(resource_id, resource_type, key_type, ec2)
        print("Tags were successfully added to {}\n".format(resource_id))


#######################################
# Function to Create Tags
#######################################

def add_name_tag(resource_id, resource_type, key_type, ec2):
    try:
        print("Adding necessary tags to {}".format(resource_id))
        return ec2.create_tags(
            Resources=[resource_id],
            Tags=[{
                'Key': key_lob,
                'Value': val_lob
            }, {
                'Key': key_cost,
                'Value': val_cost
            }, {
                'Key': key_type,
                'Value': resource_type
            }, {
                'Key': key_workload,
                'Value': val_workload
            }, {
                'Key': key_data_classification,
                'Value': val_data_classification
            }, {
                'Key': key_env,
                'Value': val_env
            },  {
                'Key': key_ms,
                'Value': val_ms
            },{    
                 'Key': key_backup,
                 'Value': val_backup
            },{
                'Key': key_ms_group,
                'Value': val_ms_group
            },{
                'Key': key_client,
                'Value': val_client
            }]
        )
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        raise


#####################
# Main Function
#####################

def lambda_handler(event, context):
    for aws_region in aws_regions:
        ec2 = boto3.client('ec2', region_name=aws_region)
        """ :type: pyboto3.ec2 """
        print("Scanning region: {}".format(aws_region))
        tag_instance(ec2, aws_region)
        tag_vol(ec2, aws_region)
        tag_snapshots(ec2, aws_region)
        

if __name__ == "__main__":
    lambda_handler({}, {})