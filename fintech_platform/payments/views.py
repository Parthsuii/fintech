from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Wallet, PlatformBucket, Investment, Project
from .serializers import InvestmentCreateSerializer
from .services import calculate_split
from .finternet import create_finternet_dvp_payment


# ==================================================
# INVEST API (CREATE DvP ESCROW)
# ==================================================

class InvestAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = InvestmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data["project_id"]
        amount = serializer.validated_data["amount"]

        project = get_object_or_404(
            Project,
            id=project_id,
            is_active=True
        )

        # Prevent duplicate pending payments
        existing = Investment.objects.filter(
            investor=request.user,
            project=project,
            status__in=["initiated", "pending_payment"]
        ).first()

        if existing:
            return Response(
                {"error": "Pending investment already exists"},
                status=400
            )

        creator_amt, bucket_amt = calculate_split(project, amount)

        # Create investment
        investment = Investment.objects.create(
            investor=request.user,
            project=project,
            total_amount=amount,
            creator_amount=creator_amt,
            bucket_amount=bucket_amt,
            status="initiated"
        )

        # Call Finternet API
        payment = create_finternet_dvp_payment(
            amount=str(amount),
            reference_id=str(investment.id),
            metadata={
                "investment_id": str(investment.id),
                "project_id": str(project.id),
                "investor_id": str(request.user.id),
            }
        )

        # -------------------------
        # SANDBOX MODE
        # -------------------------

        if not payment or "data" not in payment:

            fake_intent = f"local_{investment.id}"

            investment.finternet_txn_id = fake_intent
            investment.status = "pending_payment"
            investment.save()

            return Response({
                "message": "Sandbox mode (Finternet offline)",
                "payment_url": f"http://127.0.0.1:8000/api/pay/{fake_intent}/",
                "investment_id": investment.id,
                "status": investment.status,
                "mode": "sandbox"
            }, status=201)

        # -------------------------
        # FINTERNET MODE
        # -------------------------

        intent_id = payment["data"]["id"]

        investment.finternet_txn_id = intent_id
        investment.status = "pending_payment"
        investment.save()

        return Response({
            "message": "DvP escrow created",
            "payment_url": payment["data"]["paymentUrl"],
            "investment_id": investment.id,
            "status": investment.status,
            "mode": "finternet"
        }, status=201)


# ==================================================
# PAYMENT PAGE (DEMO UI)
# ==================================================

def pay_view(request, intent_id):

    return HttpResponse(f"""
        <h2>DvP Escrow Payment</h2>
        <p>Intent: {intent_id}</p>

        <form method="post" action="/api/confirm/{intent_id}/">
            <button type="submit">Confirm Payment</button>
        </form>
    """)


# ==================================================
# CONFIRM PAYMENT (SIMULATE BANK / CARD)
# ==================================================

@csrf_exempt
def confirm_payment(request, intent_id):

    investment = Investment.objects.filter(
        finternet_txn_id=intent_id
    ).first()

    if not investment:
        return HttpResponse("Invalid transaction", status=400)

    if investment.status != "pending_payment":
        return HttpResponse("Already processed", status=200)

    investment.status = "funded"
    investment.save(update_fields=["status"])

    return HttpResponse("""
        <h3>Payment Confirmed ✅</h3>
        <p>Funds locked in escrow</p>
    """)


# ==================================================
# DELIVERY PROOF (DvP RELEASE)
# ==================================================

@csrf_exempt
def submit_delivery_proof(request, investment_id):

    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    try:
        with transaction.atomic():

            investment = Investment.objects.select_for_update().get(
                id=investment_id,
                status="funded"
            )

            investment.status = "released"
            investment.save(update_fields=["status"])

    except Investment.DoesNotExist:
        return HttpResponse("Invalid or unpaid investment", status=400)

    return HttpResponse("Delivery proof accepted ✅")


# ==================================================
# SETTLEMENT CALLBACK
# ==================================================

@csrf_exempt
def payment_callback(request, txn_id):

    print("SETTLEMENT:", txn_id)

    with transaction.atomic():

        investment = Investment.objects.select_for_update().filter(
            finternet_txn_id=txn_id
        ).first()

        # Sandbox fallback
        if not investment and txn_id.startswith("local_"):

            inv_id = txn_id.replace("local_", "")

            investment = Investment.objects.select_for_update().filter(
                id=inv_id
            ).first()

        if not investment:
            return HttpResponse("Invalid transaction", status=400)

        if investment.status == "completed":
            return HttpResponse("Already processed", status=200)

        if investment.status != "released":
            return HttpResponse("Invalid state", status=400)

        # Finalize
        investment.status = "completed"
        investment.save(update_fields=["status"])

        # Credit creator
        creator_wallet, _ = Wallet.objects.get_or_create(
            user=investment.project.creator
        )

        creator_wallet.balance += investment.creator_amount
        creator_wallet.save(update_fields=["balance"])

        # Credit platform
        bucket, _ = PlatformBucket.objects.get_or_create(
            name="Main Bucket"
        )

        bucket.balance += investment.bucket_amount
        bucket.save(update_fields=["balance"])

    return HttpResponse("Settlement completed ✅")


# ==================================================
# INVESTMENT STATUS API
# ==================================================

class InvestmentStatusAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, investment_id):

        investment = get_object_or_404(
            Investment,
            id=investment_id,
            investor=request.user
        )

        return Response({
            "id": investment.id,
            "status": investment.status,
            "amount": str(investment.total_amount),
            "finternet_txn_id": investment.finternet_txn_id,
        })
