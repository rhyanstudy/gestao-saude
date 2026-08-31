from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [
    ('PENDING', 'Pendente'),
    ('IN_REVIEW', 'Em Análise'),
    ('RETURNED', 'Retornado'),
    ('COMPLETED', 'Concluído'),
]


class MedicationTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medication_transfers')
    requesting_unit = models.CharField(max_length=255, verbose_name="Unidade Solicitante")
    observation = models.TextField(blank=True, null=True, verbose_name="Observação (Opcional)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    admin_observation = models.TextField(blank=True, null=True, verbose_name="Observação do Administrador")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Transferência #{self.id} - {self.requesting_unit} ({self.get_status_display()})"


class MedicationTransferItem(models.Model):
    transfer = models.ForeignKey(MedicationTransfer, on_delete=models.CASCADE, related_name='items')
    medication = models.CharField(max_length=255, verbose_name="Medicamento")
    quantity = models.IntegerField(verbose_name="Quantidade")
    cmm = models.IntegerField(verbose_name="CMM", default=0)
    supri_code = models.CharField(max_length=50, verbose_name="Código SUPRI")

    def __str__(self):
        return f"{self.medication} ({self.quantity} un / CMM: {self.cmm}) - SUPRI: {self.supri_code}"


class CmmAdjustmentRequest(models.Model):
    CMM_STATUS_CHOICES = [
        ('OPEN', 'Aberto'),
        ('RETURNED', 'Retornado'),
        ('COMPLETED', 'Concluído'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cmm_requests')
    health_unit = models.CharField(max_length=255, verbose_name="Unidade de Saúde")
    effective_date = models.DateField(verbose_name="Data para Efetivação")
    requester_name = models.CharField(max_length=255, verbose_name="Responsável pela Solicitação")
    requester_role = models.CharField(max_length=255, verbose_name="Função do Responsável")
    observation = models.TextField(blank=True, null=True, verbose_name="Observações (Opcional)")

    status = models.CharField(max_length=20, choices=CMM_STATUS_CHOICES, default='OPEN', verbose_name="Status")
    admin_observation = models.TextField(blank=True, null=True, verbose_name="Observação do Administrador")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CMM #{self.id} - {self.health_unit} ({self.get_status_display()})"


class CmmAdjustmentItem(models.Model):
    request = models.ForeignKey(CmmAdjustmentRequest, on_delete=models.CASCADE, related_name='items')
    medication = models.CharField(max_length=255, verbose_name="Medicamento")
    current_quantity = models.IntegerField(verbose_name="Quantidade Atual")
    new_quantity = models.IntegerField(verbose_name="Nova Quantidade")
    supri_code = models.CharField(max_length=50, verbose_name="Código SUPRI")

    def __str__(self):
        return f"{self.medication} (Atual: {self.current_quantity} / Novo: {self.new_quantity}) - SUPRI: {self.supri_code}"
