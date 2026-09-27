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


class ProductoForm(forms.ModelForm):
    """
    Formulario para creación y actualización de componentes de hardware (RF-01 y RF-03).
    Aplica diseño estructurado y validaciones contra números negativos.
    """
    class Meta:
        model = Producto
        fields = [
            'sku',
            'nombre',
            'categoria',
            'descripcion',
            'precio',
            'cantidad',
            'stock_minimo',
            'estado',
            'activo',
        ]
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: CPU-AMD-7800X3D'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: AMD Ryzen 7 7800X3D 8-Core'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Especificaciones técnicas detalladas (arquitectura, frecuencias, puertos, etc.)'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'placeholder': '0'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'placeholder': '5'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError("La cantidad no puede ser negativa.")
        return cantidad

    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo is not None and stock_minimo < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return stock_minimo


class AjusteStockForm(forms.Form):
    """
    Formulario para ajustar existencias (aumentar/disminuir) según RF-05.
    """
    ACCION_CHOICES = (
        ('sumar', 'Incrementar Stock (+ Ingreso)'),
        ('restar', 'Decrementar Stock (- Salida)'),
    )
    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cantidad a ajustar",
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '1'})
    )
    motivo = forms.CharField(
        max_length=200,
        required=False,
        label="Motivo del ajuste (Opcional)",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Recepción de lote, corrección de inventario...'})
    )

