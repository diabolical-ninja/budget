"""
Objectives:
    - Monthly total spending vs income
    - Monthly surplus + rolling average (smoothing)
    - Last N-months average per category vs current month
        - red/back depending whether over or under
"""

# %%
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots

MAX_HISTORY = 36  # Months, aka 3yrs
COMPARISON_MONTHS = 6  # Compare to the last 6months of expenditure

# %%
transactions_df = pd.read_csv("data/report_2023-03-10_230157.csv", sep=";")

# %%
# Select data range desired:
#   - Exclude the current month as it's likely incomplete
#   - Only compare against the last N Months
transactions_df["date"] = pd.to_datetime(transactions_df["date"])

# Determine current month & the earliest month to consider
current_month = transactions_df["date"].max().strftime("%Y-%m")
start_month = pd.Timestamp(current_month) - relativedelta(months=MAX_HISTORY)

transactions_df = transactions_df[
    (transactions_df["date"] < current_month) & (transactions_df["date"] >= start_month)
]

# %%
# Calculate total expenses & income per month

expenses_df = transactions_df[transactions_df["category"] != "Income"]
income_df = transactions_df[transactions_df["category"] == "Income"]

monthly_expenses = (
    expenses_df.groupby(pd.Grouper(key="date", freq="MS"))["amount"]
    .sum()
    .abs()
    .reset_index()
)
monthly_expenses["category"] = "Expense"
monthly_expenses.sort_values(by="date", ascending=True)

monthly_income = (
    income_df.groupby(pd.Grouper(key="date", freq="MS"))["amount"].sum().reset_index()
)
monthly_income["category"] = "Income"
monthly_income.sort_values(by="date", ascending=True)


income_expenses_df = pd.concat([monthly_expenses, monthly_income])

# Viz
income_expenses_fig = px.line(
    income_expenses_df,
    x="date",
    y="amount",
    color="category",
    markers=True,
    color_discrete_sequence=px.colors.qualitative.Bold,
)

income_expenses_fig.update_layout(
    title="Monthly Total Income & Expenses",
    xaxis_title="Month",
    yaxis_title="Amount ($)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    legend_title="Type",
)

income_expenses_fig.update_traces(connectgaps=False)

income_expenses_fig.show()

# %%
# Surplus is money in - money out (hopefully > 0!!)
monthly_surplus_df = pd.DataFrame(
    {
        "date": monthly_expenses["date"],
        "surplus": monthly_income["amount"] - monthly_expenses["amount"],
    }
)

monthly_surplus_df["smoothed_surplus"] = monthly_surplus_df["surplus"].rolling(6).mean()


surplus_fig = px.scatter(
    monthly_surplus_df,
    x="date",
    y="surplus",
    color="surplus",
    color_continuous_scale="temps_r",
    trendline="rolling",
    trendline_options={"window": 6},  # 6month rolling average
    trendline_color_override="black",
)

# Get the trendline trace and customize its style
trendline_trace = surplus_fig.data[1]
trendline_trace.line.dash = "dot"

surplus_fig.update_layout(
    title="Monthly Surplus",
    xaxis_title="Month",
    yaxis_title="Amount ($)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    legend_title="Type",
)

surplus_fig.update_traces(connectgaps=False, marker_size=7)
surplus_fig.show()

# %%
# Compare the last months expenses with the N-months preceeding it
# For the preceeding months it calculates the total per month for each month
# then averages across them


# Current Months expenses
max_month = transactions_df["date"].max()
n_months_back = (max_month - relativedelta(months=COMPARISON_MONTHS)).strftime("%Y-%m")

most_recent_months_transactions = transactions_df[
    transactions_df["date"] >= max_month.strftime("%Y-%m")
]
most_recent_months_tally = (
    most_recent_months_transactions.groupby(["category"])["amount"].sum().reset_index()
)

# Preceeding N-months
n_months_back_df = transactions_df[
    (transactions_df["date"] >= n_months_back)
    & (transactions_df["date"] < max_month.strftime("%Y-%m"))
]

summary_per_month = (
    n_months_back_df.groupby([pd.Grouper(key="date", freq="MS"), "category"])["amount"]
    .sum()
    .reset_index()
)

summary_per_month_summarised = (
    summary_per_month.groupby(["category"])["amount"].mean().reset_index()
)

# Combine both aggregates for comparison & viz
summary_joined = pd.merge(
    left=summary_per_month_summarised, right=most_recent_months_tally, on="category"
)

summary_joined.columns = [
    "Category",
    f"Avg {COMPARISON_MONTHS} Months",
    "Current Month",
]

# Format columns to make them look pretty
summary_joined[f"Avg {COMPARISON_MONTHS} Months"] = summary_joined[
    f"Avg {COMPARISON_MONTHS} Months"
].apply(lambda x: "$ {:.2f}".format((x)))
summary_joined["Current Month"] = summary_joined["Current Month"].apply(
    lambda x: "$ {:.2f}".format((x))
)


# Viz
def determine_colour(current_month: str, prior_months: str) -> str:
    current_month = float(current_month.replace("$", "").strip())
    prior_months = float(prior_months.replace("$", "").strip())

    if current_month > prior_months:
        colour = "#90EE90"  # Light Green
    elif current_month < prior_months:
        colour = "#F08080"  # Light Red
    else:
        colour = "#e6f2fd"  # Neutral Blue

    return colour


colours = summary_joined.apply(
    lambda x: determine_colour(
        x["Current Month"], x[f"Avg {COMPARISON_MONTHS} Months"]
    ),
    axis=1,
)

fill_color = []
n_rows = summary_joined.shape[0]

fill_color.append(["#e6f2fd"] * n_rows)
fill_color.append(["#e6f2fd"] * n_rows)
fill_color.append(colours)


table_fig = go.Figure(
    data=[
        go.Table(
            header=dict(
                values=[f"<b>{x}</b>" for x in summary_joined.columns],
                align="left",
                font=dict(color="black", size=15),
            ),
            cells=dict(
                values=summary_joined.values.T,
                align=["left", "center"],
                fill_color=fill_color,
                font_size=15,
                height=35,
            ),
        )
    ]
)

table_fig.update_layout(title_text="<b>Category Comparison</b>", autosize=True)
table_fig.show()
