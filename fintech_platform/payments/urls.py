from django.urls import path
from django.urls import path
from .views import (
    InvestAPIView,
    pay_view,
    confirm_payment,
    submit_delivery,
    payment_callback,
)

urlpatterns = [

    path("invest/", InvestAPIView.as_view()),

    path("pay/<str:intent_id>/", pay_view),
    path("confirm/<str:intent_id>/", confirm_payment),

    path("deliver/<int:investment_id>/", submit_delivery),

    path("callback/<str:txn_id>/", payment_callback),
]
