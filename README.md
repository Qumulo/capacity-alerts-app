# soft_quota
soft_quota.py will run a check against a Qumulo cluster running Qumulo Core 1.2.9 or later. Requires python 2.7. 
The script will generate a csv file containing the quota name and the current usage and will email if the quota is exceeded.

Credentials are defined with environment variables, as follows: 
$QUMULO_CLUSTER  #Cluster FQDN
$QUMULO_USER     #Username with rights to use API
$QUMULO_PWD      #Password for that user

Quotas are defined in the quotas.txt file and are space delimited. A sample file is provided. Format is as follows: 
quota_name /storage/system/path /nfs/mount/path quota_size_in_TB
