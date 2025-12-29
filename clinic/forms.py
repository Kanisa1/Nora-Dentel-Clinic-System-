from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name", "last_name", "national_id", "phone", "dob",
            "gender", "province", "district", "sector", "cell",
            "is_insured", "insurer", "insurer_other", "insurance_coverage_pct", "membership_number"
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make insurance fields not required
        self.fields['insurer'].required = False
        self.fields['insurer_other'].required = False
        self.fields['membership_number'].required = False
        self.fields['insurance_coverage_pct'].required = False


from django import forms
from .models import Patient, Appointment, Visit, Department, ClinicUser
from django.utils import timezone

INSURANCE_PCTS = [(i, f"{i}%") for i in [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100]]

class PatientRegistrationForm(forms.ModelForm):
    insurance_coverage_pct = forms.ChoiceField(choices=INSURANCE_PCTS, required=False)
    
    class Meta:
        model = Patient
        fields = ['first_name','last_name','national_id','parent_name','nationality','gender',
                  'province','district','sector','cell','village','phone','occupation','affiliation',
                  'religion','is_insured','insurer','insurer_other','membership_number',
                  'insurance_coverage_pct','dob']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parent/Guardian Name'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'sector': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sector'}),
            'cell': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cell'}),
            'village': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Affiliation/Organization'}),
            'religion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Religion'}),
            'is_insured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insurer': forms.Select(attrs={'class': 'form-control'}),
            'insurer_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify Other Insurance'}),
            'membership_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Insurance Membership Number'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class ScheduleAppointmentForm(forms.ModelForm):
    scheduled_at_date = forms.DateField(required=True, initial=timezone.localdate)
    scheduled_at_time = forms.TimeField(required=True, initial=timezone.localtime)
    class Meta:
        model = Appointment
        fields = ['patient','department','doctor','notes']
