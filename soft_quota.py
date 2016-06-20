#!/usr/bin/env python
# Copyright (c) 2013 Qumulo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.


# Import python libraries
import os
import sys
import smtplib
from email.mime.text import MIMEText

# Import Qumulo REST libraries
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import qumulo.lib.auth
import qumulo.lib.opts
import qumulo.lib.request
import qumulo.rest

# Size Definitions
KILOBYTE = 1024
MEGABYTE = 1024 * KILOBYTE
GIGABYTE = 1024 * MEGABYTE
TERABYTE = 1024 * GIGABYTE

###############CHANGE THESE SETTINGS AND CREATE THESE FILES FOR YOUR ENVIRONMENT #####################################
# Email settings
smtp_server = 'smtp.example.com'
sender = 'qumulo_cluster@example.com'
recipients = ['recipient1@example.com', 'recipient2@example.com']

# Location to write log file and header line for log file
logfile = './group_usage.log'
header = 'Group,SpaceUsed'
storagename = '[QUMULO CLUSTER]' # for email subject

# Import credentials
host = os.environ.get('QUMULO_CLUSTER')
port = 8000
user = os.environ.get('QUMULO_USER')
password = os.environ.get('QUMULO_PWD') or 'admin'

# Import quota dictionary from quotas.txt file
# quotas.txt formatted as one line per quota formatted as <short name> <path on Qumulo storage> <nfs mount path> <quota size in TB>
quota_dict = {}
with open(os.path.join(sys.path[0], "quotas.txt"),"r") as file:
    for line in file:
        quotaname, storage_path, nfs_path, size = line.split()
        quota_dict[quotaname] = (storage_path, nfs_path, float(size))
######################################################################################################################

def login(host, user, passwd, port):
    '''Obtain credentials from the REST server'''
    conninfo = None
    creds = None

    try:
        # Create a connection to the REST server
        conninfo = qumulo.lib.request.Connection(host, int(port))

        # Provide username and password to retreive authentication tokens
        # used by the credentials object
        login_results, _ = qumulo.rest.auth.login(
                conninfo, None, user, passwd)

        # Create the credentials object which will be used for
        # authenticating rest calls
        creds = qumulo.lib.auth.Credentials.from_login_response(login_results)
    except Exception, excpt:
        print "Error connecting to the REST server: %s" % excpt
        print __doc__
        sys.exit(1)

    return (conninfo, creds)

def send_mail(smtp_server, sender, recipients, subject, body):
    mmsg = MIMEText(body, 'html')
    mmsg['Subject'] = subject
    mmsg['From'] = sender
    mmsg['To'] = ", ".join(recipients)

    session = smtplib.SMTP(smtp_server)
    session.sendmail(sender, recipients, mmsg.as_string())
    session.quit()

def build_mail(nfspath, quota, current_usage, smtp_server, sender, recipients):
    sane_current_usage = float(current_usage) / float(TERABYTE)
    subject = storagename + "Quota exceeded"
    body = ""
    body += "The usage on {} has exceeded the quota.<br>".format(nfspath)
    body += "Current usage: %0.2f TB<br>" %sane_current_usage 
    body += "Quota: %0.2f TB<br>" %quota
    body += "<br>"
    send_mail(smtp_server, sender, recipients, subject, body)
        
# Build email and check against quota for notification, return current usage for tracking
def monitor_path(path, conninfo, creds):
    try:
        node = qumulo.rest.fs.read_dir_aggregates(conninfo, creds, path)
    except Exception, excpt:
        print 'Error retrieving path: %s' % excpt
    else:
        current_usage = int(node[0]['total_capacity'])
        return current_usage

def build_csv(quotaname, current_usage, logfile):
    with open(logfile, "a") as file:
        file.write(quotaname + ',' + str(current_usage) + '\n')
        
### Main subroutine
def main(argv):
    # Get credentials
    (conninfo, creds) = login(host, user, password, port)
    
    # Overwrite log file
    with open(logfile, "w") as file:
        file.write(header + '\n')

    # Get quotas and generate CSV
    for quotaname in quota_dict.keys():
        path, nfspath, quota = quota_dict[quotaname]
        current_usage = monitor_path(path, conninfo, creds)
        if current_usage is not None:
            quotaraw = int(quota) * TERABYTE
            if current_usage > quotaraw:
                build_mail(nfspath, quota, current_usage, smtp_server, sender, recipients)
            build_csv(quotaname, current_usage, logfile)    

# Main
if __name__ == '__main__':
    main(sys.argv[1:])
