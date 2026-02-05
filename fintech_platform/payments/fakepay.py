from django.shortcuts import get_object_or_404, redirect
from payments.models import Investment, Wallet, PlatformBucket


def fake_payment(request, txn_id):

    # Find investment
    investment = get_object_or_404(
        Investment,
        finternet_txn_id=txn_id
    )

    # If already paid, skip
    if investment.status == "completed":
        return redirect("/admin/")

    # Get wallets
    creator_wallet, _ = Wallet.objects.get_or_create(
        user=investment.project.creator
    )

    investor_wallet, _ = Wallet.objects.get_or_create(
        user=investment.investor
    )

    bucket = PlatformBucket.objects.first()

    # Credit balances
    creator_wallet.balance += investment.creator_amount
    creator_wallet.save()

    bucket.balance += investment.bucket_amount
    bucket.save()

    # Mark completed
    investment.status = "completed"
    investment.save()

    return redirect(f"/api/callback/{txn_id}/")
