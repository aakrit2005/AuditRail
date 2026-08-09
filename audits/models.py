from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Links a Django auth User to a role. This is the piece that makes login
    know whether someone lands on the manager dashboard or their own
    workspace, and (for auditors) which Auditor row is "them".
    """
    ROLE_MANAGER = 'manager'
    ROLE_AUDITOR = 'auditor'
    ROLE_CHOICES = [(ROLE_MANAGER, 'Manager'), (ROLE_AUDITOR, 'Auditor')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    auditor = models.OneToOneField(
        'Auditor', on_delete=models.CASCADE, null=True, blank=True, related_name='profile'
    )

    def __str__(self):
        return f'{self.user.username} ({self.role})'


class Auditor(models.Model):
    """One row per field auditor. Matches the `auditors` table in the original brief."""

    name = models.CharField(max_length=120)
    initials = models.CharField(max_length=4)
    region = models.CharField(max_length=60)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    """One row per site that gets audited. Matches the `locations` table."""

    name = models.CharField(max_length=150)
    client_name = models.CharField(max_length=150, blank=True)
    region = models.CharField(max_length=60)
    address = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return self.name


class AuditTemplate(models.Model):
    """A checklist definition, e.g. 'Statutory' or 'Quarterly Site Standard'.
    Matches `audit_templates`. The individual questions live in ChecklistItem
    below instead of a JSON blob, since a real relational column per item is
    easier to query/report on than parsing JSON in every view."""

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class ChecklistItem(models.Model):
    """One checklist question belonging to a template, grouped into a section
    (e.g. 'Safety', 'Compliance') and given an explicit order so the form
    renders in a consistent sequence."""

    template = models.ForeignKey(AuditTemplate, on_delete=models.CASCADE, related_name='items')
    section = models.CharField(max_length=100)
    label = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.section}: {self.label}'


class Audit(models.Model):
    """One audit assignment - a specific auditor, at a specific location,
    following a specific template, due on a specific date. Matches `audits`."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In progress'),
        ('completed', 'Completed'),
    ]

    code = models.CharField(max_length=20, unique=True, help_text="Display ID, e.g. AUD-1041")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='audits')
    auditor = models.ForeignKey(Auditor, on_delete=models.CASCADE, related_name='audits')
    template = models.ForeignKey(AuditTemplate, on_delete=models.PROTECT, related_name='audits')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return self.code

    @property
    def items_total(self):
        return self.template.items.count()

    @property
    def items_scored(self):
        return self.responses.exclude(score__isnull=True).count()

    @property
    def score_percent(self):
        """Average score across answered items, scaled to a 0-100 percent.
        Each checklist item is scored 0-5, so percent = (sum of scores) / (items * 5) * 100."""
        answered = self.responses.exclude(score__isnull=True)
        if not answered.exists():
            return None
        total_possible = answered.count() * 5
        total_scored = sum(r.score for r in answered)
        return round((total_scored / total_possible) * 100)

    @property
    def flagged_count(self):
        return self.responses.filter(flagged=True).count()


class AuditResponse(models.Model):
    """One answered checklist item within an audit: the score given, any
    remark, whether it's flagged, and whether a photo was attached.
    Matches `audit_responses`. flagged is stored explicitly (rather than
    derived purely from score) so a manager can flag something outside the
    normal score threshold if needed."""

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name='responses')
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='responses')
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    remark = models.TextField(blank=True)
    flagged = models.BooleanField(default=False)
    has_photo = models.BooleanField(default=False)

    class Meta:
        unique_together = ('audit', 'checklist_item')

    def save(self, *args, **kwargs):
        # Auto-flag low scores unless a manager already flagged/unflagged it manually
        if self.score is not None and self.score <= 2:
            self.flagged = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.audit.code} - {self.checklist_item.label}'
