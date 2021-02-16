# aou-datasync
## Usage

A script to generate csv file to upload to SalesForce.

Usage: sf-update-gen.py [-h] --workq WORKQ --contacts CONTACTS --leads LEADS
                        [-i] [-d DAYS]

Optional arguments:
  -h, --help            Show this help message and exit
  --workq WORKQ         (Required) HealthPro workqueue CSV.
  --contacts CONTACTS   (Required) SalesForce Contacts CSV.
  --leads LEADS         (Required) SalesForce Leads CSV.
  -i, --interactive     Run interactive resolver on output_issues.csv
  -d DAYS, --days DAYS  Only run resolver on records of which the Primary
                        Consent Date is this DAYS ago.
