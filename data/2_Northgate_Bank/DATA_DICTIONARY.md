# Northgate Bank: Fraud and Disputes Operations: data dictionary

Regional bank, Jan to Jun 2026. Fraud rules produce many alerts; card disputes have regulatory deadlines (45 days to resolve).

The data is **invented for teaching**; any resemblance to real people or companies is coincidence. Files are raw extracts (the bronze layer) exactly as landed from each source system. They are imperfect, as real extracts are. Do not edit them.

See `bronze/_manifest.csv` for record counts.

## Conventions
- Card processor timestamps are UTC; core banking timestamps are local time.
- Rules R01 to R12 are described by the fraud team as: velocity, geography, device, new payee, structuring, and so on. Disposition values: False positive, Escalated, SAR filed.
- SAR means Suspicious Activity Report filed with regulators. Cash deposits above $10,000 trigger currency reporting.

## core_banking/customers.csv
Customer master from the core banking system.

| Column | Example |
|---|---|
| cust_id | N100000 |
| first_name | John |
| last_name | Scott |
| dob | 1956-02-21 |
| address | 891 Oak Dr |
| city | Springfield |
| state | MI |
| phone | 469-555-3426 |
| email | john.scott13@example.com |
| segment | Premier |

## core_banking/accounts.csv
Accounts by customer.

| Column | Example |
|---|---|
| acct_id | A500000 |
| cust_id | N100000 |
| acct_type | Checking |
| open_dt | 2019-06-03 |
| status | Open |

## transactions/transactions.csv
Union of the card processor feed and the core banking feed. Positive amount is money in, negative is money out, except card purchases which are positive spend. Login events are included with amount 0.

| Column | Example |
|---|---|
| txn_id | T0015758 |
| acct_id | A504993 |
| txn_ts | 2026-01-01T00:06:12Z |
| channel | Card |
| amount | 52.85 |
| merchant_raw | Apple Store R112 |
| mcc | 5732 |
| counterparty |  |
| device_id | DV3218 |
| ip_country | US |

## fraud_engine/alerts.csv
Alerts raised by the rules engine, one per flagged transaction.

| Column | Example |
|---|---|
| alert_id | AL000001 |
| txn_id | T0000015 |
| acct_id | A504171 |
| rule_id | R09 |
| score | 0.59 |
| alert_dt | 2026-04-22 |
| disposition | False positive |
| analyst_id | AN09 |
| minutes_spent | 39 |

## fraud_engine/analyst_notes.jsonl
Free-text notes by analysts.

Example record: `{"alert_id": "AL000001", "analyst_id": "AN09", "text": "Customer confirmed. FP."}`

## disputes/card_disputes.csv
Card disputes filed by customers; due_dt is the regulatory deadline.

| Column | Example |
|---|---|
| dispute_id | DS00001 |
| acct_id | A500973 |
| txn_id | T0012310 |
| filed_dt | 2026-03-20 |
| reason | Incorrect amount |
| amount | 44.72 |
| due_dt | 2026-05-04 |
| status | Closed |
| resolved_dt | 2026-04-06 |
| provisional_credit | Y |
