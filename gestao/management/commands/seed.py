import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from gestao.models import MedicationTransfer, MedicationTransferItem, CmmAdjustmentRequest, CmmAdjustmentItem


class Command(BaseCommand):
    help = "Popula o banco com usuários de teste e solicitações de exemplo"

    def handle(self, *args, **kwargs):
        self.stdout.write("Populando banco de dados...")

        user1, created = User.objects.get_or_create(username="user1")
        user1.set_password("user123")
        user1.save()
        self.stdout.write(self.style.SUCCESS("Usuário user1 pronto (senha: user123)"))

        user2, created = User.objects.get_or_create(username="user2")
        user2.set_password("user123")
        user2.save()
        self.stdout.write(self.style.SUCCESS("Usuário user2 pronto (senha: user123)"))

        admin1, created = User.objects.get_or_create(username="admin1")
        admin1.is_staff = True
        admin1.is_superuser = True
        admin1.set_password("admin123")
        admin1.save()
        self.stdout.write(self.style.SUCCESS("Admin admin1 pronto (senha: admin123)"))

        MedicationTransfer.objects.all().delete()
        CmmAdjustmentRequest.objects.all().delete()

        t1 = MedicationTransfer.objects.create(
            user=user1,
            requesting_unit="UBS Jardim das Palmeiras",
            status="PENDING",
            observation="Necessidade urgente devido ao aumento de atendimentos de gripe.",
        )
        MedicationTransferItem.objects.create(transfer=t1, medication="Dipirona 500mg", quantity=100, cmm=450, supri_code="101")
        MedicationTransferItem.objects.create(transfer=t1, medication="Soro Fisiológico 0.9%", quantity=200, cmm=500, supri_code="102")

        t2 = MedicationTransfer.objects.create(
            user=user2,
            requesting_unit="UPA Zona Norte",
            status="RETURNED",
            admin_observation="Favor revisar a quantidade de Insulina solicitada.",
        )
        MedicationTransferItem.objects.create(transfer=t2, medication="Insulina NPH", quantity=10, cmm=20, supri_code="301")

        today = timezone.now().date()
        days_to_tuesday = (1 - today.weekday()) % 7 or 7
        next_tuesday = today + timedelta(days=days_to_tuesday)
        past_tuesday = next_tuesday - timedelta(days=14)

        c1 = CmmAdjustmentRequest.objects.create(
            user=user1,
            health_unit="UBS Jardim das Palmeiras",
            effective_date=next_tuesday,
            requester_name="Dr. Carlos Eduardo",
            requester_role="Diretor Clínico",
            observation="Ajuste necessário conforme nova tabela licitatória.",
            status="OPEN",
        )
        CmmAdjustmentItem.objects.create(request=c1, medication="Anlodipino 5mg", current_quantity=1000, new_quantity=1500, supri_code="901")

        c2 = CmmAdjustmentRequest.objects.create(
            user=user2,
            health_unit="UPA Zona Norte",
            effective_date=past_tuesday,
            requester_name="Fernanda Lima",
            requester_role="Farmacêutica Responsável",
            status="COMPLETED",
            admin_observation="Reajuste CMM processado e aprovado com sucesso.",
        )
        CmmAdjustmentItem.objects.create(request=c2, medication="Omeprazol 20mg", current_quantity=800, new_quantity=1200, supri_code="902")

        self.stdout.write(self.style.SUCCESS("Seed concluído."))
