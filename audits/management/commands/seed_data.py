from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from audits.models import (
    Audit,
    AuditResponse,
    Auditor,
    AuditTemplate,
    ChecklistItem,
    Location,
    UserProfile,
)

DEMO_PASSWORD = 'auditrail123'
DEMO_USERNAMES = ['manager', 'priya', 'marcus', 'elena', 'raj', 'neha', 'vikram']


class Command(BaseCommand):
    help = 'Wipes and reloads the database with data matching the AudiTrail HTML mockups.'

    @transaction.atomic
    def handle(self, *args, **options):
        AuditResponse.objects.all().delete()
        Audit.objects.all().delete()
        ChecklistItem.objects.all().delete()
        AuditTemplate.objects.all().delete()
        Location.objects.all().delete()
        UserProfile.objects.filter(user__username__in=DEMO_USERNAMES).delete()
        User.objects.filter(username__in=DEMO_USERNAMES).delete()
        Auditor.objects.all().delete()

        # --- Auditors ---
        # Priya/Marcus/Elena are the three in the "viewing as" switcher on
        # manager-side-audits-tab.html. Raj/Neha/Vikram only ever appear in
        # manager-side.html's table and assignments card, not the switcher —
        # but since the switcher is now a real {% for %} loop over every
        # Auditor row, they get a workspace tab too now (an upgrade over the
        # static mockup, which had no way to reach them).
        priya = Auditor.objects.create(name='Priya Raman', initials='PR', region='South')
        marcus = Auditor.objects.create(name='Marcus Chen', initials='MC', region='Central')
        elena = Auditor.objects.create(name='Elena Torres', initials='ET', region='West')
        raj = Auditor.objects.create(name='Raj Singh', initials='RS', region='Central')
        neha = Auditor.objects.create(name='Neha Patel', initials='NP', region='West')
        vikram = Auditor.objects.create(name='Vikram Sharma', initials='VS', region='West')

        # --- Locations --- (name/client_name split so "{{ name }} · {{ client_name }}"
        # reproduces the audit-name text exactly, e.g. "Chennai Plant · Automotive Div")
        mangluru = Location.objects.create(name='Mangluru Warehouse', client_name='Logistics', region='South')
        chennai = Location.objects.create(name='Chennai Plant', client_name='Automotive Div', region='South')
        cdh = Location.objects.create(name='Central Distribution Hub', client_name='Fulfillment', region='Central')
        mumbai = Location.objects.create(name='Mumbai Hub', client_name='Retail Network', region='West')
        pune = Location.objects.create(name='Pune Tech Park', client_name='IT Infrastructure', region='West')
        # Not in any mockup — added only so Marcus and Elena have something
        # to show in their workspace tab instead of an empty state.
        blr = Location.objects.create(name='Bengaluru Depot', client_name='Distribution', region='Central')
        hyd = Location.objects.create(name='Hyderabad Facility', client_name='Manufacturing', region='West')

        # --- Templates ---
        # form.html (the only checklist mockup we have) is for the
        # "Statutory" template. Every other template reuses the same
        # Safety/Housekeeping/Compliance checklist — matching how the
        # original seed_data.py was structured (one shared checklist,
        # copied per template) and how the flagged issues on
        # manager-side.html reference the same item labels across
        # Quarterly Site Standard, Cyber Compliance, etc.
        quarterly = AuditTemplate.objects.create(name='Quarterly Site Standard')
        statutory = AuditTemplate.objects.create(name='Statutory')
        ops_deep_dive = AuditTemplate.objects.create(name='Operations Deep Dive')
        annual_hs = AuditTemplate.objects.create(name='Annual Health & Safety')
        cyber = AuditTemplate.objects.create(name='Cyber Compliance')

        checklist_spec = [
            ('Safety', [
                'Fire exits unobstructed and clearly signed',
                'Extinguishers inspected within last 12 months',
                'First aid kit stocked and in date',
            ]),
            ('Housekeeping', [
                'Waste segregation followed correctly',
                'Back-of-house floors clean and dry',
            ]),
            ('Compliance', [
                'Cold storage logs completed daily',
                'Staff certifications on file and current',
            ]),
        ]

        def build_checklist(template):
            order = 0
            for section, labels in checklist_spec:
                for label in labels:
                    ChecklistItem.objects.create(template=template, section=section, label=label, order=order)
                    order += 1

        for template in (quarterly, statutory, ops_deep_dive, annual_hs, cyber):
            build_checklist(template)

        def item(template, label):
            return ChecklistItem.objects.get(template=template, label=label)

        # --- Audits --- (codes/dates/status copied straight from the table
        # in manager-side.html)
        a_mlr = Audit.objects.create(
            code='IND-MLR-01', location=mangluru, auditor=priya, template=quarterly,
            status='completed', due_date='2026-08-02',
        )
        a_che = Audit.objects.create(
            code='IND-CHE-04', location=chennai, auditor=priya, template=statutory,
            status='in-progress', due_date='2026-08-18',
        )
        a_cdh = Audit.objects.create(
            code='IND-CDH-05', location=cdh, auditor=raj, template=ops_deep_dive,
            status='pending', due_date='2026-08-18',
        )
        a_mum = Audit.objects.create(
            code='IND-MUM-02', location=mumbai, auditor=vikram, template=annual_hs,
            status='completed', due_date='2026-07-25',
        )
        a_pun = Audit.objects.create(
            code='IND-PUN-08', location=pune, auditor=neha, template=cyber,
            status='in-progress', due_date='2026-08-15',
        )
        # Not in any mockup — give Marcus/Elena a task each.
        Audit.objects.create(
            code='IND-BLR-02', location=blr, auditor=marcus, template=quarterly,
            status='pending', due_date='2026-08-25',
        )
        Audit.objects.create(
            code='IND-HYD-01', location=hyd, auditor=elena, template=statutory,
            status='pending', due_date='2026-08-22',
        )

        # --- Responses ---
        # IND-MLR-01: completed, 1 flagged item (matches the "1" flag count
        # and the first entry in manager-side.html's issues-list).
        AuditResponse.objects.create(audit=a_mlr, checklist_item=item(quarterly, 'Fire exits unobstructed and clearly signed'), score=5)
        AuditResponse.objects.create(
            audit=a_mlr, checklist_item=item(quarterly, 'Extinguishers inspected within last 12 months'), score=2,
            remark='Tag expired June 2026 — replacement requested.',
        )
        AuditResponse.objects.create(audit=a_mlr, checklist_item=item(quarterly, 'First aid kit stocked and in date'), score=5)
        AuditResponse.objects.create(audit=a_mlr, checklist_item=item(quarterly, 'Waste segregation followed correctly'), score=5)
        AuditResponse.objects.create(audit=a_mlr, checklist_item=item(quarterly, 'Back-of-house floors clean and dry'), score=4)
        AuditResponse.objects.create(audit=a_mlr, checklist_item=item(quarterly, 'Cold storage logs completed daily'), score=5)
        AuditResponse.objects.create(audit=a_mlr, checklist_item=item(quarterly, 'Staff certifications on file and current'), score=5)

        # IND-CHE-04: in progress, 2 flagged items so far (matches the "2"
        # flag count and the two Chennai entries in the issues-list).
        AuditResponse.objects.create(
            audit=a_che, checklist_item=item(statutory, 'First aid kit stocked and in date'), score=2,
        )
        AuditResponse.objects.create(
            audit=a_che, checklist_item=item(statutory, 'Cold storage logs completed daily'), score=1,
            remark='Two consecutive days missing from chiller log.',
        )

        # IND-MUM-02: completed, 0 flags — every score stays above 2.
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'Fire exits unobstructed and clearly signed'), score=5)
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'Extinguishers inspected within last 12 months'), score=5)
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'First aid kit stocked and in date'), score=4)
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'Waste segregation followed correctly'), score=5)
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'Back-of-house floors clean and dry'), score=5)
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'Cold storage logs completed daily'), score=4)
        AuditResponse.objects.create(audit=a_mum, checklist_item=item(annual_hs, 'Staff certifications on file and current'), score=5)

        # IND-PUN-08: in progress, 3 flagged items (matches the "3" flag
        # count and all three Pune entries in the issues-list).
        AuditResponse.objects.create(
            audit=a_pun, checklist_item=item(cyber, 'First aid kit stocked and in date'), score=2,
            remark='Kit missing burn dressings.',
        )
        AuditResponse.objects.create(
            audit=a_pun, checklist_item=item(cyber, 'Staff certifications on file and current'), score=2,
            remark='Two forklift certs lapsed.',
        )
        AuditResponse.objects.create(
            audit=a_pun, checklist_item=item(cyber, 'Waste segregation followed correctly'), score=2,
            remark='Mixed waste in general stream.',
        )

        # --- Login users ---
        # One manager account, one per auditor, all sharing the same demo
        # password. UserProfile.auditor is what lets an auditor's login
        # land on their own workspace and nowhere else.
        manager_user = User.objects.create_user('manager', password=DEMO_PASSWORD)
        UserProfile.objects.create(user=manager_user, role=UserProfile.ROLE_MANAGER)

        for username, auditor in [
            ('priya', priya), ('marcus', marcus), ('elena', elena),
            ('raj', raj), ('neha', neha), ('vikram', vikram),
        ]:
            u = User.objects.create_user(username, password=DEMO_PASSWORD)
            UserProfile.objects.create(user=u, role=UserProfile.ROLE_AUDITOR, auditor=auditor)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {Auditor.objects.count()} auditors, {Location.objects.count()} locations, '
            f'{AuditTemplate.objects.count()} templates, {Audit.objects.count()} audits, '
            f'{AuditResponse.objects.count()} responses, {User.objects.filter(username__in=DEMO_USERNAMES).count()} login users.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Log in as any of {DEMO_USERNAMES} with password '{DEMO_PASSWORD}'."
        ))
