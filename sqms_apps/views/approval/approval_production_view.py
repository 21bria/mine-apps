from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from ...models.workflow_model import Workflow, WorkflowLog
from ...models.ore_productions_model import OreProductions
from ...models.mine_productions_model import mineProductions
from django.contrib.auth.decorators import login_required
from datetime import datetime
from ...utils.utils import generate_unique_approval
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from ...models.notification_model import Notification
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from ...utils.permissions import get_dynamic_permissions

def get_users_by_group(group_name):
    """Mengambil user berdasarkan grup."""
    return User.objects.filter(groups__name=group_name)

def send_group_email(subject, message, group_name, sender_alias=None, request=None):
    """Kirim email ke semua user dalam grup tertentu dengan format HTML."""
    if request is None or request.user is None:
        return "Error: 'request' or 'request.user' is None."

    users = get_users_by_group(group_name)  # Ambil user berdasarkan grup
    recipient_emails = [user.email for user in users if user.email]  # Hanya email valid
    
    # Periksa jika tidak ada email valid
    if not recipient_emails:
        return "No valid email addresses found for this group."
    
    # Gunakan alias jika diberikan, atau fallback ke DEFAULT_FROM_EMAIL
    sender_email = f"{sender_alias} <{settings.EMAIL_HOST_USER}>" if sender_alias else settings.DEFAULT_FROM_EMAIL

    # Render konten HTML untuk email
    html_content = f"""
    <html>
        <body>
            <div class="container">
                <h2 style="margin-top: 20px;">Hello,</h2>
                <p>{message} <strong>{request.user.username}</strong>.</p>
                <p>Please log in to review it.</p>
                <br>
                <p>Thank you,<br> Alpha System</p>
                <div class="footer">
                    <p>&copy; 2025 Alpha System. All rights reserved.</p>
                </div>
            </div>
        </body>
    </html>
    """

    try:
        # Kirim email dengan HTML menggunakan EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject,
            message,  # fallback jika email client tidak mendukung HTML
            sender_email,  # Pengirim
            recipient_emails
        )
        email.attach_alternative(html_content, "text/html")  # Lampirkan HTML
        email.send(fail_silently=False)
        return "Emails sent successfully."
    except Exception as e:
        return f"Error sending emails: {e}"


@login_required
def create_approval(request):
    if request.method == 'POST':
        try:
            # Aturan validasi
            rules = {
                'register'       : ['required'],
                'team'           : ['required'],
                'date_production': ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
                'register.required'       : 'Register is required.',
                'team.required'           : 'Team is required.',
                'date_production.required': 'Date production is required.',
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            # Dapatkan data dari request
            team            = request.POST.get('team')
            date_production = request.POST.get('date_production')
            register        = request.POST.get('register')
            description     = request.POST.get('notes')

            # Konversi date_production_str ke objek datetime
            try:
                date_production = datetime.strptime(date_production, '%Y-%m-%d')  # Pastikan format sesuai
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Please use YYYY-MM-DD.'}, status=400)

             # Validasi apakah data dengan date_production ada di OreProductions dan mineProductions
            if not OreProductions.objects.filter(tgl_production=date_production).exists():
                return JsonResponse({'error': f'Data "{date_production.strftime("%Y/%m/%d")}" is not available in Ore Productions. Unable to create approval.'}, status=400)

            if not mineProductions.objects.filter(date_production=date_production).exists():
                return JsonResponse({'error': f'Data "{date_production.strftime("%Y/%m/%d")}" is not available in Mine Productions. Unable to create approval.'}, status=400)

            # Validasi apakah data dengan kombinasi date_production dan team sudah ada di Approval
            if Workflow.objects.filter(date_production=date_production, team=team).exists():
                return JsonResponse({'error': f'Data "{date_production.strftime("%Y/%m/%d")}" and team "{team}" already exist in Approval'}, status=400)
            

            title = f'Production/{team}/{date_production.strftime("%y%m%d")}'
            # Gunakan transaksi database untuk memastikan integritas data
            with transaction.atomic():
                # Simpan data baru
                approval = Workflow.objects.create(
                    title           = title,
                    description     = description,
                    date_production = date_production,
                    team            = team,
                    register        = register,
                    status          = 'submitted',
                    created_by      = request.user
                )

                # Update OreProduction
                OreProductions.objects.filter(
                    tgl_production=date_production
                ).update(
                    status_approval='submitted',
                )

                # Mencatat log pembuatan
                WorkflowLog.objects.create(
                    approval = approval,
                    status   = 'submitted',
                    user     = request.user,
                    notes    = 'Approval created by admin.'
                )

                # Kirim notifikasi berdasarkan grup user login
                if request.user.groups.filter(name='admin-mgoqa').exists():
                    group_name = 'superintendent-mgoqa'
                elif request.user.groups.filter(name='admin-mining').exists():
                    group_name = 'superintendent-mining'
                else:
                    return JsonResponse({'error': 'User does not belong to a valid group to send notifications.'}, status=400)

                # Kirim notifikasi ke user di group
                recipients = get_users_by_group(group_name)

                # Kirim notifikasi ke penerima yang sesuai
                for user in recipients:
                    Notification.objects.create(
                        user=user,
                        workflow=approval,
                        message=f"Workflow '{approval.title}' has been submitted by {request.user.username}. Please review it.",
                    )

                # Kirim email ke user di grup
                subject = f"Workflow Notification: {approval.title}"

                message = f"""
                    The workflow '{approval.title}' has been submitted by
                """
                send_group_email(
                    subject, 
                    message, 
                    group_name, 
                    sender_alias="SQMS Notifications",
                    request=request  # Pastikan Anda mengirimkan request yang benar di sini
                )

            # Kembalikan respons JSON sukses
            return JsonResponse({'success': True, 'message': 'Approval created successfully.'})

        except IntegrityError as e:
            return JsonResponse({'error': 'Terjadi kesalahan integritas database', 'message': str(e)}, status=400)

        except ValidationError as e:
            return JsonResponse({'error': 'Validasi gagal', 'message': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': 'Terjadi kesalahan', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Metode HTTP tidak diizinkan'}, status=405)

@login_required
def review_asisten(request):
    approval_id = request.POST.get('id')
    approval    = get_object_or_404(Workflow, id=approval_id)

    if request.method == 'POST':

        # Aturan validasi
            rules = {
                'id'         : ['required'],
                'action'     : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
            'id.required'      : 'Id is required.',
            'action.required'  : 'Action is required.',
            'comment.required_if_rejected': 'Comment is required when rejecting.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            action  = request.POST.get('action')
            comment = request.POST.get('comment')

            # Validasi tambahan: jika action adalah "rejected", maka comment harus diisi
            if action == 'rejected' and not comment:
                return JsonResponse({'error': custom_messages['comment.required_if_rejected']}, status=400)

            if action == 'approve':
                approval.status = 'reviewd'
                approval.save()

                # Mengirim notifikasi ke Manager setelah Assistant menyetujui
                if request.user.groups.filter(name='superintendent-mgoqa').exists():
                    group_name = 'manager-mgoqa'
                elif request.user.groups.filter(name='superintendent-mining').exists():
                    group_name = 'manager-mining'
                else:
                    return JsonResponse({'error': 'User does not belong to a valid group to send notifications.'}, status=400)
                
                # Kirim notifikasi ke user di group
                recipients = get_users_by_group(group_name)

                # Kirim notifikasi ke penerima yang sesuai
                for user in recipients:
                    Notification.objects.create(
                        user=user,
                        workflow=approval,
                        message=f"Workflow '{approval.title}' has been submitted by {request.user.username}. Please review it.",
                    )

                WorkflowLog.objects.create(
                    approval = approval,
                    status   = 'reviewd',
                    user     = request.user,
                    notes    = 'Approved by asisten. Moved to manager review.',
                    comment  = comment
                )

                # Kirim email ke user di grup
                subject = f"Workflow Notification: {approval.title}"
                message = f"""
                    The workflow '{approval.title}' has been submitted by
                """
                send_group_email(
                    subject, 
                    message, 
                    group_name, 
                    sender_alias="SQMS Notifications",
                    request=request
                )

                
            elif action == 'rejected':
                approval.status = 'rejected'
                approval.save()

                # Mengirim notifikasi ke Manager setelah Assistant menyetujui
                if request.user.groups.filter(name='superintendent-mgoqa').exists():
                    group_name = 'manager-mgoqa'
                elif request.user.groups.filter(name='superintendent-mining').exists():
                    group_name = 'manager-mining'
                else:
                    return JsonResponse({'error': 'User does not belong to a valid group to send notifications.'}, status=400)
                
                # Kirim notifikasi ke user di group
                recipients = get_users_by_group(group_name)

                # Kirim notifikasi ke penerima yang sesuai
                for user in recipients:
                    Notification.objects.create(
                        user=user,
                        workflow=approval,
                        message=f"Workflow '{approval.title}' rejected by {request.username}: {comment}"
                    )

                WorkflowLog.objects.create(
                    approval = approval,
                    status   = 'rejected',
                    user     = request.user,
                    notes    = 'Rejected by asisten. Status reverted to draft.',
                    comment  = comment
                )

                # Kirim email ke user di grup
                subject = f"Workflow Notification: {approval.title}"
                message = f"""
                The workflow '{approval.title}' has been rejected by.
                """

                # Kirim email ke grup dengan alias "SQMS" Notifications"
                send_group_email(
                    subject, 
                    message, 
                    group_name, 
                    sender_alias="SQMS Notifications",
                    request=request
                )

            return JsonResponse({'success': True, 'message': 'Approval status updated successfully.'})

@login_required
def review_manager(request):
    approval_id = request.POST.get('id')
    approval    = get_object_or_404(Workflow, id=approval_id)

    if request.method == 'POST':

        # Aturan validasi
            rules = {
                'id'         : ['required'],
                'action'     : ['required']
            }

            # Pesan kesalahan validasi yang disesuaikan
            custom_messages = {
            'id.required'      : 'Id is required.',
            'action.required'  : 'Action is required.',
            'comment.required_if_rejected': 'Comment is required when rejecting.'
            }

            # Validasi request
            for field, field_rules in rules.items():
                for rule in field_rules:
                    if rule == 'required':
                        if not request.POST.get(field):
                            return JsonResponse({'error': custom_messages[f'{field}.required']}, status=400)

            action  = request.POST.get('action')
            comment = request.POST.get('comment')

            # Validasi tambahan: jika action adalah "rejected", maka comment harus diisi
            if action == 'rejected' and not comment:
                return JsonResponse({'error': custom_messages['comment.required_if_rejected']}, status=400)

            if action == 'approve':
                approval.status = 'approved'
                approval.save()

                # Mengirim notifikasi ke Admin setelah Manager menyetujui
                if request.user.groups.filter(name='manager-mgoqa').exists():
                    group_name = 'admin-mgoqa'
                elif request.user.groups.filter(name='manager-mining').exists():
                    group_name = 'admin-mining'
                else:
                    return JsonResponse({'error': 'User does not belong to a valid group to send notifications.'}, status=400)
                
                # Kirim notifikasi ke user di group
                recipients = get_users_by_group(group_name)

                # Kirim notifikasi ke penerima yang sesuai
                for user in recipients:
                    Notification.objects.create(
                        user=user,
                        workflow=approval,
                        message=f"Workflow '{approval.title}' has been approved by {request.user.username}",
                    )

                WorkflowLog.objects.create(
                    approval = approval,
                    status   = 'approved',
                    user     = request.user,
                    notes    = 'Approved by manager.',
                    comment  = comment
                )
                # Kirim email ke user di grup
                subject = f"Workflow Notification: {approval.title}"
                message = f"""
                        The workflow '{approval.title}' has been submitted by 
                """
                # Kirim email ke grup dengan alias "SQMS" Notifications"
                send_group_email(
                    subject, 
                    message, 
                    group_name, 
                    sender_alias="SQMS Notifications",
                    request=request
                )
                
            elif action == 'rejected':
                approval.status = 'rejected'
                approval.save()

                # Mengirim notifikasi ke Admin setelah Manage menyetujui
                if request.user.groups.filter(name='manager-mgoqa').exists():
                    group_name = 'admin-mgoqa'
                elif request.user.groups.filter(name='manager-mining').exists():
                    group_name = 'admin-mining'
                else:
                    return JsonResponse({'error': 'User does not belong to a valid group to send notifications.'}, status=400)
                
                # Kirim notifikasi ke user di group
                recipients = get_users_by_group(group_name)

                # Kirim notifikasi ke penerima yang sesuai
                for user in recipients:
                    Notification.objects.create(
                        user=user,
                        workflow=approval,
                        message=f"Workflow '{approval.title}' rejected by {request.username}: {comment}"
                    )

                WorkflowLog.objects.create(
                    approval = approval,
                    status   = 'rejected',
                    user     = request.user,
                    notes    = 'Rejected by manager. Status reverted to draft.',
                    comment  = comment
                )

                # Kirim email ke user di grup
                subject = f"Workflow Notification: {approval.title}"
                message = f"""
                The workflow '{approval.title}' has been rejected by
                """
                # Kirim email ke grup dengan alias "SQMS" Notifications"
                send_group_email(
                    subject, 
                    message, 
                    group_name, 
                    sender_alias="SQMS Notifications",
                    request=request
                )

            return JsonResponse({'success': True, 'message': 'Approval status updated successfully.'})


# ========= render html GC ===========
@login_required
def create_approval_page(request):
    permissions = get_dynamic_permissions(request.user)

    today = datetime.today()
    # Ambil data dari request jika ada
    team = request.GET.get('team', 'GC')  # Default to 'GC' if not provided
    date_production = today.strftime('%Y-%m-%d')

    print(f'Team: {team}, Date Production: {date_production}')  # Debug print

    # Menghitung nomor unik menggunakan utilitas
    unique_number = generate_unique_approval(team, date_production)
    

    context = {
        'day_date': today.strftime('%Y-%m-%d'),
        'unique_number': unique_number,
        'permissions': permissions,
    }

    return render(request, 'approval/create_approval_gc.html', context)

@login_required
def asisten_approval_page(request):
    return render(request, 'approval/review_asisten_approval.html')

@login_required
def manager_approval_page(request):
    return render(request, 'approval/review_manager_approval.html')

# ===== render mining form approval ======

@login_required
def createApproval_page(request):
    permissions = get_dynamic_permissions(request.user)
    today = datetime.today()
    # Ambil data dari request jika ada
    team = request.GET.get('team', 'Mining')  # Default to 'Mining' if not provided
    date_production = today.strftime('%Y-%m-%d')

    print(f'Team: {team}, Date Production: {date_production}')  # Debug print

    # Menghitung nomor unik menggunakan utilitas
    unique_number = generate_unique_approval(team, date_production)

    context = {
        'day_date': today.strftime('%Y-%m-%d'),
        'unique_number': unique_number,
        'permissions': permissions,
    }

    return render(request, 'admin-mine/approval/create_approval.html', context)

@login_required
def asistenApproval_page(request):
    return render(request, 'admin-mine/approval/review_asisten_approval.html')

@login_required
def managerApproval_page(request):
    return render(request, 'admin-mine/approval/review_manager_approval.html')