from django import forms
from django.forms import ModelForm
from .models import Bullet
# VeloVolunteer, BulletsRunner

class RegisterForm(ModelForm):
	over_18 = forms.BooleanField(label='Please confirm you are over 18?')

	class Meta:
		model = Bullet
		fields = ['name', 'postcode', 'email', 'contact_no', 'get_emails']
	
	def save(self, commit=True):
        # do something with self.cleaned_data['temp_id']
		m = super(RegisterForm, self).save(commit=False)
		m.over_18 = True
		if commit:
			m.save()
		return m


class UnRegisterForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100)
  #  surname = forms.CharField(label='Surname', max_length=100)
    email = forms.EmailField(label='Email address', max_length=200)


class ContactForm(forms.Form):
    name = forms.CharField(label="Your name", max_length=100)
    email = forms.EmailField(label='Your email', max_length=200)
    comment = forms.CharField(widget=forms.Textarea)



#class BulletsRunnerForm(ModelForm):
#	class Meta:
#		model = BulletsRunner
#		fields = ['name', 'address', 'email', 'gender', 'contact_no', 'emergency_contact_no', 'age', 'club', 'race']



#class VeloForm(forms.Form):
#	RIDER = "r"
#	NON_RIDER = "n"
#	VOLUNTEER_TYPE_CHOICES = (
#		(RIDER, "rider"),
#		(NON_RIDER, "non-rider")
#	)
#	email = forms.EmailField(label='Email address', max_length=200)	
#
#	volunteer_type = forms.ChoiceField(choices=VOLUNTEER_TYPE_CHOICES)

#SIZE_XS = 'xs'
#SIZE_S = 's'
#SIZE_M = 'm'
#SIZE_L = 'l'
#SIZE_XL = 'xl'
#SIZE_XXL = 'xxl'
#SIZE_XXXL = 'xxxl'

#KIT_SIZE_CHOICES = (
#	(SIZE_XS, 'X Small'),
#	(SIZE_S, 'Small'),
#	(SIZE_M, 'Medium'),
#	(SIZE_L, 'Large'),
#	(SIZE_XL, 'X Large'),
#	(SIZE_XXL, 'XX Large'),
#	(SIZE_XXXL, 'XXX Large')
#)
	
#MALE = 'm'
#FEMALE = 'f'
#KIT_SEX_CHOICES = (
#	(MALE, 'male-fit'),
#	(FEMALE, 'female-fit')
#)



#class VeloRiderForm(forms.Form):
#	address = forms.CharField(label="Your address", widget=forms.Textarea)
#
#	entered_velo = forms.BooleanField(label="Have you entered the Velo?", required=False)
#	average_speed = forms.CharField(label='Average Speed (mph)', max_length=10, help_text="What speed do you think you would average on a 100 mile ride?")
#	kit_sex = forms.ChoiceField(label='Kit type?', choices=KIT_SEX_CHOICES, help_text="Please indicate whether you require men's or women's-fit kit") 
#
#	jersey_size = forms.ChoiceField(label='Jersey size', choices=KIT_SIZE_CHOICES, help_text="Please see the <a href='https://www.primaleurope.com/pages/fit-guide' target='_blank'>Fit Guide</a> for more information on sizes")
#	short_size =  forms.ChoiceField(label='Bib short size', choices=KIT_SIZE_CHOICES, help_text="Please see the <a href='https://www.primaleurope.com/pages/fit-guide' target='_blank'>Fit Guide</a> for more information on sizes")
#
#
#class VeloRunnerForm(forms.Form):
#	name = forms.CharField(label="Your name") 
#	address = forms.CharField(label="Your address", widget=forms.Textarea)
#	contact_no = forms.CharField(label="Contact number")
#	tshirt_size = forms.ChoiceField(label="T-shirt size", choices=KIT_SIZE_CHOICES)
#	drive_van = forms.BooleanField(label="Are you willing to drive a van?", required=False)
#	drive_bus = forms.BooleanField(label="Are you willing to drive a minibus?", required=False, help_text="Please note: By saying you are able to drive a minibus, you are also confirming that you have a Category D1 driving licence, which means you can drive a minibus with up to 16 passenger seats without needing an additional driving test.")




## Special for Peter upload Bullets
#class UploadCSVForm(forms.Form):
#    engaged = forms.BooleanField(label="Are you engaged?")
#    reallyenaged = forms.BooleanField(label="Are you really engaged?")
#    csv_file = forms.FileField()


class tdbForm(forms.Form):
	strava_id = forms.IntegerField(label="Athlete ID")

