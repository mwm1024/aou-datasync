#!/bin/python3
# requires progress
# requires fuzzywuzzy, optionally with python-Levenshtein
# requires dateparser

import csv
import argparse
import sys
import os.path
from operator import itemgetter
from datetime import datetime, timedelta, time

from progress.bar import Bar
from fuzzywuzzy import process, fuzz
import dateparser


SKIPALL = False

def read_csv(csv_path):
    if os.path.isfile(csv_path):
        pass
    else:
        exit(f'Invalid path: {csv_path}')
    fo = open(csv_path)
    try:
        reader = csv.DictReader(fo)
        if 'PMID' not in reader.fieldnames:
            exit(f'Error: PMID not in the header of {csv_path}.')
        else:
            return [row for row in reader]
    except Exception as e:
        raise


def merge_participants(participants, leads, contacts, resolve=False, days=-1):
    bar = Bar('Processing...', max=len(participants))
    since_day = datetime.now() - timedelta(days=int(days))
    since_day = datetime.combine(since_day.date(), time())
    for participant in participants:
        pmid = participant['PMID']
        participant['Contact ID'] = None
        participant['Lead ID'] = None
        for contact in contacts:
            # find contact match
            if contact['PMID'] == pmid:
                participant['Contact ID'] = contact['Contact ID']
                break
        for lead in leads:
            # find lead match
            if lead['PMID'] == pmid:
                participant['Lead ID'] = lead['Lead ID']
                break
        if not participant['Lead ID'] and not participant['Contact ID']:
            try:
                pcd = dateparser.parse(participant['Primary Consent Date'])
            except Exception as e:
                exit(f'Error: Failed to interpret "{pcd}" for {pmid}.')
            if since_day < pcd or days < 0:
                print(f'\n👉{pmid} ({pcd}) does not have a matching lead or contact...')
                if resolve:
                    if SKIPALL:
                        print(f'Skipped resolving lead.')
                    else:
                        participant = resolver(participant, leads, 'lead')
                if resolve:
                    if SKIPALL:
                        print(f'Skipped resolving contact.')
                    else:
                        participant = resolver(participant, contacts, 'contact')
        bar.next()
    bar.finish()
    return participants


def upload_gen(participants):
    fo_updates = open('output_update_all.csv', 'w')
    fo_inserts = open('output_inserts.csv', 'w')
    fo_issues = open('output_update_contacts.csv', 'w')
    # TODO: Confirm to overwrite
    writer_updates = csv.DictWriter(
        fo_updates,
        fieldnames=participants[0].keys()
    )
    writer_updates.writeheader()
    writer_inserts = csv.DictWriter(
        fo_inserts,
        fieldnames=participants[0].keys()
    )
    writer_inserts.writeheader()
    writer_issues = csv.DictWriter(
        fo_issues,
        fieldnames=participants[0].keys()
    )
    writer_issues.writeheader()
    counter_updates, counter_inserts, counter_issues = 0, 0, 0
    for participant in participants:
        if participant['Lead ID']:
            writer_updates.writerow(participant)
            counter_updates += 1
        elif participant['Contact ID']:
            writer_issues.writerow(participant)
            counter_issues += 1
        else:
            writer_inserts.writerow(participant)
            counter_inserts += 1
    print(f'{counter_updates} records saved to {fo_updates.name}')
    print(f'{counter_issues} records saved to {fo_issues.name}')
    print(f'{counter_inserts} records saved to {fo_inserts.name}')


def resolver(participant, sf_data, category):
    print(f'Resolving {category}...')
    if category not in ('contact', 'lead'):
        exit('Unsupported category for resolver.')
    pmid = participant['PMID']
    participant_info = [
        f'{participant["First Name"]}',
        f'{participant["Last Name"]}',
        f'{participant["Date of Birth"]}',
        f'{participant["Phone"]}',
        f'{participant["Email"]}',
    ]
    candidates = []
    participant_record_id = None
    for record in sf_data:
        record_id = record['Lead ID'] if category == 'lead' else record['Contact ID']

        record_info = [
            f'{record["First Name"]}',
            f'{record["Last Name"]}',
            f'{record["Birthdate"]}',
            f'{record["Phone"]}',
            f'{record["Email"]}',
        ]
        score = fuzz.partial_token_sort_ratio(participant_info, record_info)
        candidates.append([score, record_id, record_info])
        if record['PMID'] == pmid:
            participant_record_id = record_id
            break
    if not participant_record_id:
        print('+' * 16)
        print(f'HealthPro\t',
              f'{pmid}\t\t',
              '\t'.join(participant_info))
        candidates.sort(key=itemgetter(0), reverse=True)
        for i in range(0,3):
            cand = candidates[i]
            # TODO: tab display
            print(f'{category.capitalize()} {i+1} {cand[0]}%\t',
                  f'{cand[1]}\t', # Record ID
                  '\t'.join(cand[2]),
                  )
        selection = input('Make a choice or press any other key to skip: ')
        if selection in ['1', '2', '3']:
            participant_record_id = candidates[int(selection) - 1][1]
            if category == 'lead':
                participant['Lead ID'] = participant_record_id
            else:
                participant['Contact ID'] = participant_record_id
            print(f'✅{pmid} {category.capitalize()} ID -> {participant_record_id}')
        elif selection == 'skipall':
            # TODO: Don't like this, replace global var later.
            global SKIPALL
            SKIPALL = True
            print('Skipping all following issues.')
        else:
            print('Skipped.')
        print('-' * 16)

    return participant


def main():
    parser = argparse.ArgumentParser(
        description='A script to generate csv file \
            to upload to SalesForce. ')
    parser.add_argument('--workq',
                        required=True,
                        help='(Required) HealthPro workqueue CSV.')
    parser.add_argument('--contacts',
                        required=True,
                        help='(Required) SalesForce Contacts CSV.')
    parser.add_argument('--leads',
                        required=True,
                        help='(Required) SalesForce Leads CSV.')
    parser.add_argument('-i',
                        '--interactive',
                        action='store_true',
                        help='Run interactive resolver on missing lead/contact, which shows the Primary Consent Date for these participants as well.')
    parser.add_argument('-d',
                        '--days',
                        help='Only run resolver on records of which the Primary Consent Date is this DAYS ago.')
    args = parser.parse_args()
    participants = read_csv(args.workq)
    contacts = read_csv(args.contacts)
    leads = read_csv(args.leads)
    if not args.days:
        participants_merged = merge_participants(participants,
                                                 leads,
                                                 contacts,
                                                 resolve=args.interactive)
    else:
        try:
            since_day = datetime.now() - timedelta(days=int(args.days))
            since_day = datetime.combine(since_day.date(), time())
            print(f'Primary Consent Date cutoff for resolver: {since_day.date()}')
        except Exception as e:
            exit(f'Failed to interpret -d value, user provides "{args.days}".')
        participants_merged = merge_participants(participants,
                                                 leads,
                                                 contacts,
                                                 resolve=args.interactive,
                                                 days=int(args.days))
    upload_gen(participants_merged)


if __name__ == "__main__":
    main()
