from decimal import Decimal


def calculate_split(project, amount):
    amount = Decimal(amount)

    creator_amt = amount * Decimal(project.creator_percent / 100)
    bucket_amt = amount * Decimal(project.bucket_percent / 100)

    return creator_amt, bucket_amt