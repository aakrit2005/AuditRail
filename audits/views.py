import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Audit, AuditResponse, Auditor, AuditTemplate, Location


def _is_manager(user):
    return hasattr(user, 'profile') and user.profile.role == 'manager'


def _home_for(user):
    if _is_manager(user):
        return redirect('manager_dashboard')
    return redirect('auditor_workspace', auditor_id=user.profile.auditor_id)


def _nav_context(user, active_nav):
    if not _is_manager(user):
        return {'nav_links': False}

    first_auditor = Auditor.objects.first()
    return {
        'nav_links': True,
        'active_nav': active_nav,
        'nav_audits_url': reverse('auditor_workspace', args=[first_auditor.id]) if first_auditor else reverse('manager_dashboard'),
    }


@login_required
def manager_dashboard(request):
    if not _is_manager(request.user):
        return _home_for(request.user)

    audits = Audit.objects.select_related('location', 'auditor', 'template').all()
    total_count = audits.count()
    locations_count = audits.values('location_id').distinct().count()
    completed_count = audits.filter(status='completed').count()
    draft_count = audits.filter(status='in-progress').count()

    completed = audits.filter(status='completed')
    percents = [a.score_percent for a in completed if a.score_percent is not None]
    avg_score = round(sum(percents) / len(percents)) if percents else None

    location_data = {}
    for a in completed:
        if a.score_percent is not None:
            if a.location.name not in location_data:
                location_data[a.location.name] = []
            location_data[a.location.name].append(a.score_percent)
            
    location_labels = list(location_data.keys())
    location_scores = [round(sum(scores) / len(scores)) for scores in location_data.values()]

    flagged_responses = (
        AuditResponse.objects.filter(flagged=True)
        .select_related('checklist_item', 'audit', 'audit__location', 'audit__auditor')
        .order_by('audit__code')
    )

    auditors = list(Auditor.objects.prefetch_related('audits__location'))
    for a in auditors:
        a.open_count = sum(1 for x in a.audits.all() if x.status != 'completed')
        a.primary_location = next(iter(a.audits.all()), None)

    context = {
        'audits': audits,
        'total_count': total_count,
        'locations_count': locations_count,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'avg_score': avg_score,
        'flagged_responses': flagged_responses,
        'flagged_count': flagged_responses.count(),
        'auditors': auditors,
        'location_labels': json.dumps(location_labels),
        'location_scores': json.dumps(location_scores),
        **_nav_context(request.user, 'dashboard'),
    }
    return render(request, 'audits/manager_dashboard.html', context)


@login_required
def auditor_workspace(request, auditor_id):
    auditor = get_object_or_404(Auditor, pk=auditor_id)

    if not _is_manager(request.user) and request.user.profile.auditor_id != auditor.id:
        return _home_for(request.user)

    tasks = auditor.audits.select_related('location', 'template').all()

    all_auditors = list(Auditor.objects.all())
    for a in all_auditors:
        a.first_name = a.name.split(' ')[0]

    context = {
        'auditor': auditor,
        'tasks': tasks,
        'submitted_count': tasks.filter(status='completed').count(),
        'total_count': tasks.count(),
        'locations': auditor.audits.select_related('location')
            .values_list('location__name', flat=True).distinct(),
        'all_auditors': all_auditors,  
        'can_switch': _is_manager(request.user),
        **_nav_context(request.user, 'audits'),
    }
    return render(request, 'audits/auditor_workspace.html', context)


@login_required
def audit_detail(request, audit_code):
    audit = get_object_or_404(
        Audit.objects.select_related('location', 'auditor', 'template'), code=audit_code
    )
    if not _is_manager(request.user) and request.user.profile.auditor_id != audit.auditor_id:
        return _home_for(request.user)

    items = audit.template.items.all()
    responses = {r.checklist_item_id: r for r in audit.responses.all()}
    for item in items:
        item.response = responses.get(item.id)

    return render(request, 'audits/audit_detail.html', {
        'audit': audit,
        'items': items,
        **_nav_context(request.user, 'audits'),
    })


@login_required
def audit_form(request, audit_code):
    audit = get_object_or_404(
        Audit.objects.select_related('location', 'auditor', 'template'), code=audit_code
    )
    if not _is_manager(request.user) and request.user.profile.auditor_id != audit.auditor_id:
        return _home_for(request.user)

    items = list(audit.template.items.all())

    if request.method == 'POST':

        with transaction.atomic():
            for item in items:
                score_raw = request.POST.get(f'score_{item.id}')
                remark = request.POST.get(f'remark_{item.id}', '').strip()
                photo = request.FILES.get(f'photo_{item.id}')

                if score_raw is None and not remark and not photo:
                    continue

                response, _created = AuditResponse.objects.get_or_create(
                    audit=audit, checklist_item=item
                )
                
                score_val = int(score_raw) if score_raw not in (None, '') else None
                response.score = score_val
                response.remark = remark
                if photo:
                    response.has_photo = True
                    
                response.flagged = (score_val is not None and score_val <= 2)
                
                response.save() 

            audit.status = 'completed' if 'submit_report' in request.POST else 'in-progress'
            if audit.status == 'completed':
                audit.submitted_at = timezone.now()
            audit.save()

        if 'submit_report' in request.POST:
            messages.success(request, f'{audit.code} submitted.')
            return redirect('audit_detail', audit_code=audit.code)
        messages.success(request, f'{audit.code} draft saved.')
        return redirect('audit_form', audit_code=audit.code)

    responses = {r.checklist_item_id: r for r in audit.responses.all()}
    sections = {}
    for item in items:
        item.response = responses.get(item.id)
        sections.setdefault(item.section, []).append(item)

    context = {
        'audit': audit,
        'sections': sections,
        'score_range': range(0, 6),
        **_nav_context(request.user, 'audits'),
    }
    return render(request, 'audits/audit_form.html', context)


@login_required
def assign_task(request):
    if not _is_manager(request.user):
        return _home_for(request.user)

    if request.method == 'POST':
        auditor_id = request.POST.get('auditor')
        location_id = request.POST.get('location')
        template_id = request.POST.get('template')
        code = request.POST.get('code', '').strip()
        due_date = request.POST.get('due_date')

        if not all([auditor_id, location_id, template_id, code, due_date]):
            messages.error(request, 'All fields are required.')
        elif Audit.objects.filter(code=code).exists():
            messages.error(request, f'Audit code "{code}" is already in use.')
        else:
            Audit.objects.create(
                code=code, auditor_id=auditor_id, location_id=location_id,
                template_id=template_id, due_date=due_date, status='pending',
            )
            messages.success(request, f'{code} assigned.')
            return redirect('assign_task')

    context = {
        'auditors': Auditor.objects.all(),
        'locations': Location.objects.all(),
        'templates': AuditTemplate.objects.all(),
        'recent_audits': Audit.objects.select_related('auditor', 'location', 'template').order_by('-id')[:10],
        'preselected_auditor': request.GET.get('auditor', ''),
        **_nav_context(request.user, 'auditors'),
    }
    return render(request, 'audits/assign_task.html', context)