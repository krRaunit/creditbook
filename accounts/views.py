import base64
import os
from datetime import datetime
from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Payment

def home(request):
    return render(request, 'accounts/home.html')


def help(request):
    return render(request, 'accounts/help.html')


def about(request):
    return render(request, 'accounts/about.html')

@login_required
def scan_qr(request):
    return render(request, 'accounts/scanqr.html')


def customer_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('customer-dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'accounts/customer-login.html')


def customer_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, "Customer registered successfully!")
                return redirect('customer-login')
            else:
                messages.error(request, "Username already exists.")
        else:
            messages.error(request, "Passwords do not match")
    return render(request, 'accounts/customer-registration.html')


def merchant_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('merchant-dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'accounts/merchant-login.html')


def merchant_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, "Merchant registered successfully!")
                return redirect('merchant-login')
            else:
                messages.error(request, "Username already exists.")
        else:
            messages.error(request, "Passwords do not match")
    return render(request, 'accounts/merchant-registration.html')


@login_required
def customer_dashboard(request):
    payments = Payment.objects.filter(sender=request.user).exclude(amount=0)

    return render(request, 'accounts/customer-dashboard.html', {'payments': payments})



def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def my_qr_code(request):

    # Generate the QR code for the merchant's payment page
    if request.user.is_authenticated:
        merchant_username = request.user.username  # Get the logged-in merchant's username
        payment_url = f"{request.scheme}://{request.get_host()}/process-payment?receiver={merchant_username}"  # Dynamic URL

        # Generate the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)

        # Convert QR code to image
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()  # Convert image to base64 for display in template
        buffer.close()

    if request.method == 'POST':
        receiver_username = request.POST['receiver']
        amount = request.POST['amount']
        comment = request.POST['comment']

        try:
            receiver = User.objects.get(username=receiver_username)
            Payment.objects.create(sender=request.user, receiver=receiver, amount=amount, comment=comment)
            messages.success(request, "Payment processed successfully!")
            return redirect('customer-dashboard')
        except User.DoesNotExist:
            messages.error(request, "Receiver does not exist!")

    return render(request, 'accounts/myqr.html', {'qr_code': img_base64})




@login_required
def process_payment(request):
    # Initialize context for modal display
    context = {'show_modal': False}

    if request.method == 'POST':
        username = request.POST['username']  # Hidden input field
        amount = request.POST['amount']
        comment = request.POST['comment']

        try:
            # Get the receiver user
            user = User.objects.get(username=username)

            # Create the payment record
            Payment.objects.create(sender=request.user, receiver=user, amount=amount, comment=comment)

            # Set context for success modal
            context.update({
                'show_modal': True,
                'status': 'success',
                'receiver_name': user.username,
                'amount': amount,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': "Credit recorded successfully!"
            })

        except User.DoesNotExist:
            # Set context for failure modal
            context.update({
                'show_modal': True,
                'status': 'failure',
                'message': "Receiver does not exist! Please try again."
            })
    else:
        # For GET request, pre-fill receiver_username in the form
        receiver_username = request.GET.get('receiver', '')
        context['receiver_username'] = receiver_username

    return render(request, 'accounts/process-payment.html', context)


@login_required
def merchant_dashboard(request):
    
    payments = Payment.objects.filter(receiver=request.user).exclude(status__in=['Paid', 'Accepted'])

    return render(request, 'accounts/merchant-dashboard.html', {'payments': payments})


@login_required
def accept_payment(request, payment_id):
    """Accepts a payment and updates the customer's total credit."""
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.status == 'Pending':
        payment.status = 'Accepted'
        payment.save()
        messages.success(request, "Payment request accepted.")
    return redirect('merchant-dashboard')


@login_required
def reject_payment(request, payment_id):
    """Rejects a payment and allows the merchant to delete it."""
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.status == 'Pending':
        payment.status = 'Rejected'
        payment.save()
        messages.success(request, "Payment request rejected.")
    return redirect('merchant-dashboard')


@login_required
def delete_payment(request, payment_id):
    """Deletes a rejected payment."""
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == "POST" and payment.status == "Rejected":
        payment.delete()
        messages.success(request, "The transaction has been deleted successfully.")
    return redirect('merchant-dashboard')


@login_required
def generate_qr_code(request):
    # Get the current merchant (logged-in user)
    merchant = request.user
    # Generate the QR code URL pointing to the process-payment page
    qr_url = f"{settings.SITE_URL}/process-payment/?receiver={merchant.username}"  # Adjust SITE_URL in settings.py

    # Create QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save the QR Code image to the media folder
    qr_path = os.path.join(settings.MEDIA_ROOT, f"qr_codes/{merchant.username}_qr.png")
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    img.save(qr_path)

    return redirect('merchant-dashboard')  # Redirect back to the dashboard

from django.db.models import Sum
from django.db.models import Q

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, F, ExpressionWrapper, DurationField
from datetime import timedelta
from .models import User, Payment  # Ensure Payment model is correctly imported

from datetime import timedelta
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DurationField

def calculate_score(payments):
    """Calculate customer score (5 to 100) based on various credit factors."""
    
    if not payments.exists():
        return 60  # Minimum credit score
    
    # Total Credit and Total Paid
    total_credit = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    total_paid = payments.aggregate(Sum('paid'))['paid__sum'] or 0
    num_transactions = payments.count()

    # Credit Utilization (30% weight)
    credit_utilization = (total_paid / total_credit) * 100 if total_credit > 0 else 0
    utilization_score = min(30, (credit_utilization / 100) * 30)

    # Repayment Timeliness (40% weight)
    payments_with_diff = payments.annotate(
        repayment_diff=ExpressionWrapper(
            F('repayment_time') - F('timestamp'),
            output_field=DurationField()
        )
    )
    avg_time_to_repay = payments_with_diff.aggregate(Avg('repayment_diff'))['repayment_diff__avg']
    avg_time_days = avg_time_to_repay.total_seconds() / (60 * 60 * 24) if avg_time_to_repay else 0

    if avg_time_days <= 7:
        timeliness_score = 40
    elif avg_time_days <= 14:
        timeliness_score = 30
    elif avg_time_days <= 30:
        timeliness_score = 20
    else:
        timeliness_score = 10

    # Payment History (20% weight)
    on_time_payments = payments_with_diff.filter(repayment_diff__lte=timedelta(days=7)).count()
    payment_history_score = (on_time_payments / num_transactions) * 20 if num_transactions > 0 else 0

    # Transaction Volume (10% weight)
    transaction_score = min(10, (num_transactions / 50) * 10)  # Assuming 50 transactions for full score

    # Final Score Calculation (Scaled to 5-100)
    raw_score = utilization_score + timeliness_score + payment_history_score + transaction_score
    credit_score = int(5 + (raw_score / 100) * 95)  # Scaling to 5-100

    return max(5, min(100, credit_score))  # Ensuring score stays within 5-100 range


def customer_analytics(request):
    """View for displaying customer analytics."""
    context = {}
    return render(request, 'accounts/customer_analytics.html', context)

import openpyxl
from django.http import HttpResponse

@login_required
def export_customers_excel(request):
    payments = Payment.objects.filter(receiver=request.user).exclude(Q(status='Pending') | Q(status='Rejected'))
    customer_data = payments.values('sender__username').annotate(total_credit=Sum('amount'))

    # Create a new Excel workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Customer Credit Details"

    # Define headers
    headers = ["Customer Username", "Total Credit"]
    ws.append(headers)

    # Add customer data
    for customer in customer_data:
        ws.append([customer["sender__username"], customer["total_credit"]])

    # Create response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="customer_credit_details.xlsx"'
    wb.save(response)

    return response


@login_required
def merchant_customers(request):
    # Fetch only accepted and paid payments
    payments = Payment.objects.filter(receiver=request.user).exclude(status__in=['Pending', 'Rejected'])

    customer_data = payments.values('sender__username').annotate(
        total_credit=Sum('amount', filter=Q(paid=False))  # Sum only unpaid amounts
    )

    return render(request, 'accounts/customers.html', {'customer_data': customer_data})

@login_required
def mark_as_paid(request):
    if request.method == 'POST':
        customer_username = request.POST.get('customer_username')
        merchant = request.user

        # Get all unpaid payments of the customer
        payments = Payment.objects.filter(
            sender__username=customer_username, receiver=merchant, paid=False
        ).exclude(status__in=['Pending', 'Rejected'])

        # If there are unpaid payments, mark them as paid
        if payments.exists():
            payments.update(paid=True, status='Paid')
            messages.success(request, f"All credit for {customer_username} has been marked as paid.")
        else:
            messages.warning(request, f"No outstanding credit found for {customer_username}.")

        return redirect('merchant-customers')
    

@login_required
def customer_profile(request, username):
    # Fetch the customer by their username
    user = get_object_or_404(User, username=username)

    # Get the logged-in merchant
    merchant = request.user  

    # Filter payments only for this merchant and customer
    payments = Payment.objects.filter(sender=user, receiver=merchant).exclude(amount=0)

    # Calculate Total Credit (only Accepted & Paid transactions)
    from django.db.models import Sum

    #total_credit = payments.exclude(status__in=['Rejected', 'Paid', 'Pending']).aggregate(Sum('amount'))['amount__sum'] or 0
    total_credit = Payment.objects.filter(sender=user, status='Accepted').aggregate(Sum('amount'))['amount__sum'] or 0
 # Calculate Total Paid
    total_paid = payments.filter(status='Paid').aggregate(Sum('paid'))['paid__sum'] or 0

    # Calculate the average time to repay (excluding NULL repayment_time)
    valid_payments = payments.filter(status='Paid').exclude(repayment_time__isnull=True)
    
    payments_with_diff = valid_payments.annotate(
        repayment_diff=ExpressionWrapper(
            F('repayment_time') - F('timestamp'),
            output_field=DurationField()
        )
    )
    
    avg_time_to_repay = payments_with_diff.aggregate(Avg('repayment_diff'))['repayment_diff__avg'] or 0
    avg_time_in_days = avg_time_to_repay.total_seconds() / (60 * 60 * 24) if avg_time_to_repay else 0

    # Calculate Customer Score
    customer_score = calculate_score(valid_payments)

    context = {
        'total_credit': total_credit,
        'total_paid': total_paid,
        'avg_time_to_repay': avg_time_in_days,
        'customer_score': customer_score,
        'payments': payments,  # Now only payments with the logged-in merchant
        'user': user,
        'selected_merchant': merchant,
    }

    return render(request, 'accounts/customer-profile.html', context)

@login_required
def export_customer_profile_excel(request, username):
    # Fetch customer
    user = get_object_or_404(User, username=username)
    merchant = request.user  # Logged-in merchant

    # Filter payments for this customer and merchant
    payments = Payment.objects.filter(sender=user, receiver=merchant).exclude(amount=0)

    # Create a new Excel workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{user.username} Credit Details"

    # Define headers
    headers = ["Date", "Amount", "Comment", "Status"]
    ws.append(headers)

    # Add payment data
    for payment in payments:
        ws.append([
            payment.timestamp.strftime("%d-%m-%Y %H:%M"),
            payment.amount,
            payment.comment,
            payment.status
        ])

    # Create response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{user.username}_credit_details.xlsx"'
    wb.save(response)

    return response

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})
