from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import Investment, Wallet


@csrf_exempt
def finternet_webhook(request):

    data = json.loads(request.body)

    txn_id = data.get("id")
    status = data.get("status")

    if status == "success":

        investment = Investment.objects.get(
            finternet_txn_id=txn_id
        )

        investment.status = "completed"
        investment.save()

        # Update creator bucket
        wallet = Wallet.objects.get(
            user=investment.project.creator
        )

        wallet.balance += investment.bucket_amount
        wallet.save()

    return JsonResponse({"ok": True})
