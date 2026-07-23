from django import forms
from .models import Employee, Attendance

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'designation',
            'department',
            'date_joined',
            'salary',
            'is_active'
        ]
        widgets = {
            'date_joined': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@company.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 (555) 000-0000'}),
            'designation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Software Engineer'}),
            'department': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Engineering'}),
            'salary': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Annual Salary'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['status', 'check_in', 'check_out', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'check_in': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'check_out': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-input', 'placeholder': 'Additional remarks...'}),
        }
