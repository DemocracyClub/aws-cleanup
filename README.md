# aws-cleanup

Admin script to help identify and delete inactive images and snapshots from DC AWS accounts

```
usage: cleanup.py [-h] --config CONFIG --action {list,delete} [--keep KEEP]

Delete inactive images and snapshots from AWS

optional arguments:
  --config CONFIG        config file
  --action {list,delete}
  --keep KEEP            <Optional> AMIs to keep (multiple --keep arguments are allowed)
```

* Set `AWS_PROFILE` env var
* Use `--action list` to identify inactive images
* Identify anything we don't want to delete
* Pass them in `--keep` params when we run with `--action delete` to delete them


example:

```
AWS_PROFILE=myprofile ./cleanup.py --config ee_london --action list --keep ami-0123 --keep ami-3456
```
