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
import time
import smtplib
from email.mime.text import MIMEText

# Import Qumulo REST libraries
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import qumulo.lib.auth
import qumulo.lib.opts
import qumulo.lib.request
import qumulo.rest

# Size Definitions
KILOBYTE = 1000
MEGABYTE = 1000 * KILOBYTE
GIGABYTE = 1000 * MEGABYTE
TERABYTE = 1000 * GIGABYTE

############### CHANGE THESE SETTINGS AND CREATE THESE FILES FOR YOUR ENVIRONMENT #####################################
# Email settings
smtp_server = 'smtp.example.com'
sender = 'qumulo_cluster@example.com'
recipients = ['recipient1@example.com', 'recipient2@example.com']

# Location to write log file and header line for log file
logfile = './run_capacity_alert.log'
header = 'Alert Time,Alert Name,Path,SpaceUsed'
storagename = '[QUMULO CLUSTER]' # for email subject

# Import credentials
host = os.getenv('API_HOSTNAME', '{your-qumulo-cluster-hostname}')
user = os.getenv('API_USER','{your-qumulo-api-username}')
password = os.getenv('API_PASSWORD','{your-qumulo-api-password}')
port = 8000

# Import alert dictionary from alert_definitions.txt file
# alert_definitions.txt formatted as one line per alert formatted as <short name> <path on Qumulo storage> <capacity size in TB, base 1000>
alert_dict = {}

definitions_file = "alert_definitions.txt"
if not os.path.exists(definitions_file):
    print("\nPlease create the %s file." % (definitions_file, ))
    print("Each line should three tab separated columns as defined as the following:")
    print("<Alert name> <Cluster path> <Capacity threshold (in TB, base 1000)>\n")
    sys.exit()

with open(definitions_file,"r") as file:
    for line in file:
        alert_name, storage_path, size = line.split()
        alert_dict[alert_name] = (storage_path, float(size))

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

def build_mail(path, alert_size, current_usage, smtp_server, sender, recipients):
    sane_current_usage = float(current_usage) / float(TERABYTE)
    subject = storagename + " Capacity alert"
    body = ""
    body += "The usage on {} has exceeded its capacity threshold.<br>".format(path)
    body += "Current usage: %0.2f TB<br>" % sane_current_usage 
    body += "Capacity threshold: %0.2f TB<br>" % alert_size
    body += "<br>"
    send_mail(smtp_server, sender, recipients, subject, body)
        
# Build email and check against alert for notification, return current usage for tracking
def monitor_path(path, conninfo, creds):
    try:
        node = qumulo.rest.fs.read_dir_aggregates(conninfo, creds, path)
    except Exception, excpt:
        print 'Error retrieving path: %s' % excpt
    else:
        current_usage = float(node[0]['total_capacity'])
        return current_usage


def build_csv(alert_name, path, current_usage, logfile):
    with open(logfile, "a") as file:
        file.write("%s,%s,%s,%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"),
                                    alert_name, 
                                    path, 
                                    round(current_usage/TERABYTE,4)))

### Main subroutine
def main(argv):
    # Get credentials
    (conninfo, creds) = login(host, user, password, port)
    
    # Overwrite log file
    with open(logfile, "w") as file:
        file.write(header + '\n')

    # Get alerts and generate CSV
    for alert_name in alert_dict.keys():
        path, alert_size = alert_dict[alert_name]
        current_usage = monitor_path(path, conninfo, creds)
        if current_usage is not None:
            alert_raw = float(alert_size) * TERABYTE
            if current_usage > alert_raw:
                build_mail(path, alert_size, current_usage, smtp_server, sender, recipients)
            build_csv(alert_name, path, current_usage, logfile)    

# Main
if __name__ == '__main__':
    main(sys.argv[1:])
