# Budget

Consumes transaction history (spending & income) & aggregates it into a few useful charts.

1. Monthly total spendings vs total income
1. Monthly "Surplus" where surpus = total income - total expenses
1. Last months expenses per category vs the prior N-Months (eg last 6months)


# To Run

To run, you'll need your transaction history with the expectation the following fields exist:

| Column   | Type               | Description                                                                              |
|----------|--------------------|------------------------------------------------------------------------------------------|
| date     | string or datetime | ISO8601 compliant datetime                                                               |
| category | string             | The spending type, eg transport, food, etc                                               |
| amount   | float              | Transaction amount assuming positive values correspond to income & negative for expenses |


Update the following with the path to your data:
```python
transactions_df = pd.read_csv("data/report_2023-03-10_230157.csv", sep=";")
```

To run:
```bash
poetry run python analysis.py  
```