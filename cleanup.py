#!/usr/bin/env python3
import argparse
import boto3

ALLOWED_ACTIONS = ['list', 'delete']

# get a list of any AMIs which are
# currently used by a Launch Config
def get_images_in_use(region):
    autoscaling = boto3.client('autoscaling', region_name=region)
    launch_configs = autoscaling.describe_launch_configurations()
    if 'LaunchConfigurations' not in launch_configs:
        raise Exception("Could not find any LaunchConfigurations")
    if len(launch_configs['LaunchConfigurations']) == 0:
        raise Exception("Could not find any LaunchConfigurations")

    images = []
    for lc in launch_configs['LaunchConfigurations']:
        images.append(lc['ImageId'])

    if len(images) == 0:
        raise Exception(
            "Could not find any images for launch config {name}".format(
                name=lc['LaunchConfigurationName']
            )
        )
    return images

def has_tag(image, key, value):
    for tag in image.tags:
        if tag['Key'] == key and tag['Value'] == value:
            return True
    return False

def should_delete_image(image, tags, do_not_delete):
    found = {}
    for key in tags:
        if has_tag(image, key, tags[key]):
            found[key] = True

    # we only want to delete this image
    # if it has _all_ of the required tags
    if set(found.keys()) == set(tags.keys()):
        # and its not in the exclude list
        if image.id not in do_not_delete:
            return True

    return False

def process_images(images, action):
    print('images:')
    print('---')
    for image in images:
        print('{id}  | {date}'.format(id=image.id, date=image.creation_date))
        if action == 'delete':
            image.deregister()

def process_snapshots(snapshots, action):
    print('snapshots:')
    print('---')
    for snapshot in snapshots:
        print('{id} | {date}'.format(id=snapshot.id, date=snapshot.start_time))
        if action == 'delete':
            snapshot.delete()

def main(region, tags, keep, action):
    if action not in ALLOWED_ACTIONS:
        raise Exception('action must be one of {actions}'.format(
                actions=str(ALLOWED_ACTIONS)
            )
        )
    ec2 = boto3.resource('ec2', region_name=region)

    # we don't want to delete any images
    # used by a current launch config
    # or which we've explicitly said we want to keep
    do_not_delete = keep + get_images_in_use(region)

    flagged_images = []
    flagged_snapshots = []

    for image in ec2.images.filter(Owners=['self']):
        if should_delete_image(image, tags, do_not_delete):
            flagged_images.append(image)

    # identify any snapshots associated with
    # the images we are going to delete
    for image in flagged_images:
        for device in image.block_device_mappings:
            if 'Ebs' in device:
                snapshot = ec2.Snapshot(device['Ebs']['SnapshotId'])
                flagged_snapshots.append(snapshot)

    process_images(flagged_images, action)
    print('')
    process_snapshots(flagged_snapshots, action)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Delete inactive images and snapshots from AWS')
    parser.add_argument(
        '--config',
        action='store',
        help='config file',
        required=True
    )
    parser.add_argument(
        '--action',
        dest='action',
        action='store',
        choices=ALLOWED_ACTIONS,
        required=True
    )
    parser.add_argument(
        '--keep',
        help='<Optional> AMIs to keep (multiple --keep arguments are allowed)',
        required=False,
        action='append',
        default=[]
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    config = __import__(args.config, fromlist=['REGION_NAME', 'TAGS'])
    print('imported config from {}.py'.format(args.config))
    print('')
    print(
        '{action}ing inactive images and snapshots in {region} with tags {tags} except {keep}...'.format(
            action=args.action,
            region=config.REGION_NAME,
            tags=str(config.TAGS),
            keep=str(args.keep),
        )
    )
    print('')
    main(config.REGION_NAME, config.TAGS, args.keep, args.action)
