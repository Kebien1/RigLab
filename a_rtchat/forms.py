from django.forms import ModelForm
from django import forms
from .models import *


class FormularioCrearMensaje(ModelForm):
    class Meta:
        model = MensajeChat
        fields = ['cuerpo']
        widgets = {
            'cuerpo': forms.Textarea(attrs={
                'placeholder': 'Escribe un mensaje...',
                'class': 'min-h-[3rem] max-h-32 flex-1 resize-y rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-4 py-2.5 sm:py-3 text-sm leading-relaxed text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20',
                'maxlength': '2000',
                'rows': '1',
                'autofocus': True,
            }),
        }
