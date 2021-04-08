# what instances users are allowed to create
AWS_VALID_INSTANCES = [
    "t2.nano",
    "t2.micro",
    "t2.small",
    "t2.medium",
    "t2.large",
    "t2.xlarge",
    "t2.2xlarge",
]

# id of security group (firewall rules) to use for created instances
AWS_NET_SECURITY_GROUP = "sg-REPLACEME"

# admin access ssh pubkey -- added to every instance
AWS_ADMIN_PUBKEY = "ssh-rsa ADMINKEY admin"

# check for stale instances every X hours
AWS_STALE_CHECK_INTERVAL = 8

# warn requestor after instance is X hours old
AWS_STALE_WARN_AGE = 24

# delete instance if requestor has not responded to the last X warnings
AWS_STALE_DELETE_AFTER = 1
