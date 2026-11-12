import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

ACTION_LABELS = {
    "created": _("Created"),
    "updated": _("Updated"),
    "status_changed": _("Status changed"),
    "deleted": _("Deleted"),
    "configured": _("Configured"),
}

ENTITY_LABELS = {
    "catalog.Product": _("Product"),
    "catalog.Category": _("Category"),
    "catalog.ProductTranslation": _("Translations"),
    "operations.OperationalTask": _("Task"),
    "auth.User": _("User"),
    "auth.Group": _("Groups"),
}


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=40)
    entity = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["entity", "entity_id"], name="audit_entity_idx")]

    def __str__(self):
        return f"{self.action} {self.entity} ({self.timestamp:%Y-%m-%d %H:%M})"

    @property
    def action_label(self):
        return ACTION_LABELS.get(self.action, self.action.replace("_", " ").capitalize())

    @property
    def entity_label(self):
        return ENTITY_LABELS.get(self.entity, self.entity)
