# Capacity Alerts

capacity_alerts.py will run a check against a Qumulo cluster running Qumulo Core 1.2.9 or later. Requires python 2.7. 
The script will generate a csv file containing the alert name and the current usage and will email if the capacity threshold is exceeded.

Credentials are defined with environment variables, as follows: 
$API_HOSTNAME   #Cluster FQDN
$API_USER       #Username with rights to use API
$API_PASSWORD   #Password for that user

Before running the alerts, there are two steps:

1. Set up your email smtp server and other configutation in <code>capacity_alerts.py</code>
2. Define your alerts in <code>alert-definitions.txt</code>. A sample file is provided. Each line should be tab delimited and formatted as follows: 
alert_name  /storage/system/path    alert_size_in_TB(base 1000)
