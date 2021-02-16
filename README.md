# aou-datasync
## Usage

A script to generate csv file to upload to SalesForce.

```bash
python3 sf-update-gen.py [-h] --workq WORKQ --contacts CONTACTS --leads LEADS [-i] [-d DAYS]
```

Positional arguments:

- --workq WORKQ            HealthPro workqueue CSV.
- --contacts CONTACTS   SalesForce Contacts CSV.
- --leads LEADS                SalesForce Leads CSV.

Optional arguments:

- -h, --help                       Show this help message and exit
- -i, --interactive               Run interactive resolver on output_issues.csv
- -d DAYS, --days DAYS  Only run resolver on records of which the Primary Consent Date is this DAYS ago.