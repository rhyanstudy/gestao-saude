from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponseForbidden, Http404

from gestao.models import MedicationTransfer, MedicationTransferItem, CmmAdjustmentRequest, CmmAdjustmentItem
from gestao.forms import MedicationTransferForm, CmmAdjustmentRequestForm

USER_UNITS = {
    'user1': 'UBS Jardim das Palmeiras',
    'user2': 'UPA Zona Norte',
    'admin1': 'Administração Central',
}


def get_user_unit(user):
    return USER_UNITS.get(user.username, 'Unidade de Saúde Padrão')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = 'user123' if username in ['user1', 'user2'] else 'admin123'
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard_redirect')
        messages.error(request, "Erro ao autenticar o usuário de teste selecionado.")

    return render(request, 'gestao/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('dashboard_redirect')


@login_required
def dashboard_redirect(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('user_dashboard')


def _build_request_entry(obj, request_type, title, *, user=None):
    entry = {
        'id': obj.id,
        'type': request_type,
        'title': title,
        'date': obj.created_at,
        'status': obj.status,
        'status_display': obj.get_status_display(),
        'full_type': 'medication' if request_type == 'Transferência' else 'cmm',
    }
    if user is not None:
        entry['user'] = user
    return entry


def _medication_title(transfer):
    first_item = transfer.items.first()
    item_desc = first_item.medication if first_item else "Sem itens"
    if transfer.items.count() > 1:
        item_desc += f" e outros (+{transfer.items.count() - 1})"
    return f"Unidade Solicitante: {transfer.requesting_unit} ({item_desc})"


def _cmm_title(cmm_request):
    first_item = cmm_request.items.first()
    item_desc = first_item.medication if first_item else "Sem itens"
    if cmm_request.items.count() > 1:
        item_desc += f" e outros (+{cmm_request.items.count() - 1})"
    return f"Ajuste CMM - {cmm_request.health_unit} ({item_desc})"


@login_required
def user_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    requests_list = []
    for transfer in MedicationTransfer.objects.filter(user=request.user):
        requests_list.append(_build_request_entry(
            transfer, 'Transferência', _medication_title(transfer),
        ))
    for cmm_request in CmmAdjustmentRequest.objects.filter(user=request.user):
        requests_list.append(_build_request_entry(
            cmm_request, 'CMM', _cmm_title(cmm_request),
        ))

    requests_list.sort(key=lambda x: x['date'], reverse=True)

    cmm_requests = CmmAdjustmentRequest.objects.filter(user=request.user)
    can_create_cmm = not cmm_requests.exclude(status='COMPLETED').exists()
    active_cmm = cmm_requests.exclude(status='COMPLETED').first()

    return render(request, 'gestao/user_dashboard.html', {
        'requests_list': requests_list,
        'can_create_cmm': can_create_cmm,
        'active_cmm': active_cmm,
    })


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='dashboard_redirect')
def admin_dashboard(request):
    med_transfers = MedicationTransfer.objects.all()
    cmm_requests = CmmAdjustmentRequest.objects.all()

    pending_count = (
        med_transfers.filter(status='PENDING').count()
        + cmm_requests.filter(status='OPEN').count()
    )
    review_count = med_transfers.filter(status='IN_REVIEW').count()
    returned_count = (
        med_transfers.filter(status='RETURNED').count()
        + cmm_requests.filter(status='RETURNED').count()
    )
    completed_count = (
        med_transfers.filter(status='COMPLETED').count()
        + cmm_requests.filter(status='COMPLETED').count()
    )

    requests_list = []
    for transfer in med_transfers:
        requests_list.append(_build_request_entry(
            transfer, 'Transferência', _medication_title(transfer), user=transfer.user.username,
        ))
    for cmm_request in cmm_requests:
        requests_list.append(_build_request_entry(
            cmm_request, 'CMM', _cmm_title(cmm_request), user=cmm_request.user.username,
        ))

    requests_list.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'gestao/admin_dashboard.html', {
        'requests_list': requests_list,
        'pending_count': pending_count,
        'review_count': review_count,
        'returned_count': returned_count,
        'completed_count': completed_count,
        'total_med': med_transfers.count(),
        'total_cmm': cmm_requests.count(),
    })


def _parse_transfer_items(request, form):
    medications = request.POST.getlist('medication[]')
    quantities = request.POST.getlist('quantity[]')
    cmms = request.POST.getlist('cmm[]')
    supri_codes = request.POST.getlist('supri_code[]')

    if not medications:
        form.add_error(None, "Adicione pelo menos um item para remanejamento.")
        return None
    if not (len(medications) == len(quantities) == len(cmms) == len(supri_codes)):
        form.add_error(None, "Erro de integridade na lista de itens.")
        return None

    items_data = []
    for i in range(len(medications)):
        med = medications[i].strip()
        qty = int(quantities[i])
        cmm_val = int(cmms[i])
        sup_c = supri_codes[i].strip()

        if not med or not sup_c:
            raise ValueError("Medicamento e Código SUPRI são obrigatórios.")
        if qty <= 0:
            raise ValueError("A quantidade deve ser um número positivo maior que zero.")
        if cmm_val < 0:
            raise ValueError("O CMM não pode ser negativo.")
        if not sup_c.isdigit():
            raise ValueError("O código SUPRI deve ser estritamente numérico.")

        items_data.append({
            'medication': med,
            'quantity': qty,
            'cmm': cmm_val,
            'supri_code': sup_c,
        })
    return items_data


def _parse_cmm_items(request, form):
    medications = request.POST.getlist('medication[]')
    current_quantities = request.POST.getlist('current_quantity[]')
    new_quantities = request.POST.getlist('new_quantity[]')
    supri_codes = request.POST.getlist('supri_code[]')

    if not medications:
        form.add_error(None, "Adicione pelo menos um medicamento para reajuste.")
        return None
    if not (len(medications) == len(current_quantities) == len(new_quantities) == len(supri_codes)):
        form.add_error(None, "Erro de integridade na lista de medicamentos.")
        return None

    items_data = []
    for i in range(len(medications)):
        med = medications[i].strip()
        cur_q = int(current_quantities[i])
        new_q = int(new_quantities[i])
        sup_c = supri_codes[i].strip()

        if not med or not sup_c:
            raise ValueError("Medicamento e Código SUPRI são obrigatórios.")
        if cur_q < 0 or new_q < 0:
            raise ValueError("As quantidades não podem ser valores negativos.")
        if not sup_c.isdigit():
            raise ValueError("O código SUPRI deve ser estritamente numérico.")

        items_data.append({
            'medication': med,
            'current_quantity': cur_q,
            'new_quantity': new_q,
            'supri_code': sup_c,
        })
    return items_data


@login_required
def submit_medication(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = MedicationTransferForm(request.POST)
        if form.is_valid():
            try:
                items_data = _parse_transfer_items(request, form)
                if items_data is None:
                    pass
                else:
                    with transaction.atomic():
                        transfer = form.save(commit=False)
                        transfer.user = request.user
                        transfer.requesting_unit = get_user_unit(request.user)
                        transfer.save()
                        for item in items_data:
                            MedicationTransferItem.objects.create(transfer=transfer, **item)

                    messages.success(request, "Solicitação de remanejamento enviada com sucesso!")
                    return redirect('user_dashboard')
            except ValueError as e:
                form.add_error(None, f"Validação de item: {str(e)}")
            except Exception:
                form.add_error(None, "Erro interno ao processar a transferência.")
    else:
        form = MedicationTransferForm()

    return render(request, 'gestao/medication_form.html', {
        'form': form,
        'user_unit': get_user_unit(request.user),
    })


@login_required
def request_detail(request, request_type, pk):
    if request_type == 'medication':
        obj = get_object_or_404(MedicationTransfer, pk=pk)
    elif request_type == 'cmm':
        obj = get_object_or_404(CmmAdjustmentRequest, pk=pk)
    else:
        raise Http404("Tipo de requisição inválido.")

    is_owner = obj.user == request.user
    if not is_owner and not request.user.is_staff:
        return HttpResponseForbidden("Você não tem permissão para acessar esta solicitação.")

    if request.method == 'POST':
        if not request.user.is_staff:
            return HttpResponseForbidden("Apenas administradores podem atualizar o status.")

        new_status = request.POST.get('status')
        admin_observation = request.POST.get('admin_observation', '')

        if new_status in dict(obj._meta.get_field('status').choices):
            obj.status = new_status
            obj.admin_observation = admin_observation
            obj.save()
            messages.success(request, f"Status do pedido atualizado para: {obj.get_status_display()}")
            return redirect('request_detail', request_type=request_type, pk=pk)

    return render(request, 'gestao/request_detail.html', {
        'obj': obj,
        'request_type': request_type,
        'is_owner': is_owner,
        'status_choices': obj._meta.get_field('status').choices,
    })


@login_required
def submit_cmm_request(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    has_active_cmm = CmmAdjustmentRequest.objects.filter(user=request.user).exclude(status='COMPLETED').exists()
    if has_active_cmm:
        messages.error(request, "Você já possui uma solicitação de reajuste CMM em andamento.")
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = CmmAdjustmentRequestForm(request.POST)
        if form.is_valid():
            try:
                items_data = _parse_cmm_items(request, form)
                if items_data is None:
                    pass
                else:
                    with transaction.atomic():
                        cmm_req = form.save(commit=False)
                        cmm_req.user = request.user
                        cmm_req.health_unit = get_user_unit(request.user)
                        cmm_req.save()
                        for item in items_data:
                            CmmAdjustmentItem.objects.create(request=cmm_req, **item)

                    messages.success(request, "Solicitação de reajuste CMM criada com sucesso!")
                    return redirect('user_dashboard')
            except ValueError as e:
                form.add_error(None, f"Validação de item: {str(e)}")
            except Exception:
                form.add_error(None, "Erro interno ao processar reajuste CMM.")
    else:
        form = CmmAdjustmentRequestForm()

    return render(request, 'gestao/cmm_form.html', {
        'form': form,
        'is_edit': False,
        'user_unit': get_user_unit(request.user),
    })


@login_required
def edit_cmm_request(request, pk):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    cmm_req = get_object_or_404(CmmAdjustmentRequest, pk=pk)

    if cmm_req.user != request.user:
        return HttpResponseForbidden("Você não tem permissão para editar esta solicitação.")

    if cmm_req.status not in ['OPEN', 'RETURNED']:
        messages.error(request, "Esta solicitação foi concluída e não pode ser editada.")
        return redirect('request_detail', request_type='cmm', pk=pk)

    if request.method == 'POST':
        form = CmmAdjustmentRequestForm(request.POST, instance=cmm_req)
        if form.is_valid():
            try:
                items_data = _parse_cmm_items(request, form)
                if items_data is None:
                    pass
                else:
                    with transaction.atomic():
                        form.save()
                        cmm_req.items.all().delete()
                        for item in items_data:
                            CmmAdjustmentItem.objects.create(request=cmm_req, **item)

                    messages.success(request, "Solicitação de reajuste CMM atualizada com sucesso!")
                    return redirect('request_detail', request_type='cmm', pk=cmm_req.id)
            except ValueError as e:
                form.add_error(None, f"Validação de item: {str(e)}")
            except Exception:
                form.add_error(None, "Erro interno ao atualizar reajuste CMM.")
    else:
        form = CmmAdjustmentRequestForm(instance=cmm_req)

    return render(request, 'gestao/cmm_form.html', {
        'form': form,
        'is_edit': True,
        'obj': cmm_req,
        'user_unit': get_user_unit(request.user),
    })
