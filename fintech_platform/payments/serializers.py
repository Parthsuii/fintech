from rest_framework import serializers


class InvestmentCreateSerializer(serializers.Serializer):

    project_id = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )
