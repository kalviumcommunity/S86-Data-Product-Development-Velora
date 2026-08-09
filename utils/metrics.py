def total_customers(df):
    return df["customer_id"].nunique()


def total_tickets(df):
    return df["ticket_id"].nunique()


def unresolved_tickets(df):
    return df[df["is_unresolved"]].shape[0]


def escalated_tickets(df):
    return df[df["is_escalated"]].shape[0]


def average_resolution(df):
    return round(df["resolution_days"].mean(), 2)


def churn_rate(df):
    total = total_customers(df)
    churned = df[df["churned"]]["customer_id"].nunique()

    if total == 0:
        return 0

    return round((churned / total) * 100, 2)


def repeat_customers(df):
    return df[df["repeat_customer"]]["customer_id"].nunique()


def high_priority_customers(df):
    """
    Temporary approximation until we calculate
    priority_score later.
    """
    high = df[
        (df["is_unresolved"]) &
        (df["is_escalated"]) &
        (df["repeat_customer"])
    ]

    return high["customer_id"].nunique()