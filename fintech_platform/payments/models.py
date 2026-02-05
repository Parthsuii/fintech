from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.user.username} Wallet"


class Project(models.Model):

    name = models.CharField(max_length=200)

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    creator_percent = models.FloatField()
    bucket_percent = models.FloatField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Investment(models.Model):

    STATUS_CHOICES = (
        ("initiated", "Initiated"),
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    investor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="investments"
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    creator_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    bucket_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="initiated"
    )

    finternet_txn_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Investment #{self.id}"


class PlatformBucket(models.Model):

    name = models.CharField(max_length=100, default="Main Bucket")

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.name} - {self.balance}"
