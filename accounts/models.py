from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

class Payment(models.Model):
    sender = models.ForeignKey(User, related_name='sent_payments', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=now)
    paid = models.BooleanField(default=False)
    repayment_time = models.DateTimeField(null=True, blank=True)  # Correctly defined
    is_deleted_by_merchant = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')],
        default='Pending'
    )

    def __str__(self):
       return f"{self.sender.username} -> {self.receiver.username}: {self.amount} ({self.status})"
