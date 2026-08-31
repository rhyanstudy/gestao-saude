from django import forms
from django.utils import timezone
from gestao.models import MedicationTransfer, CmmAdjustmentRequest


class MedicationTransferForm(forms.ModelForm):
    class Meta:
        model = MedicationTransfer
        fields = ['observation']
        widgets = {
            'observation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais (opcional)',
            }),
        }


class CmmAdjustmentRequestForm(forms.ModelForm):
    class Meta:
        model = CmmAdjustmentRequest
        fields = ['effective_date', 'requester_name', 'requester_role', 'observation']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'requester_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do Responsável',
            }),
            'requester_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Função do Responsável',
            }),
            'observation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais (opcional)',
            }),
        }

    def clean_effective_date(self):
        effective_date = self.cleaned_data.get('effective_date')
        if effective_date:
            if effective_date < timezone.now().date():
                raise forms.ValidationError(
                    "A data para efetivação do reajuste não pode ser anterior à data atual."
                )
            if effective_date.weekday() != 1:
                raise forms.ValidationError(
                    "A data para efetivação do reajuste deve ser obrigatoriamente uma terça-feira."
                )
        return effective_date
