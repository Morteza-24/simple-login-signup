from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField


class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	phone = PhoneNumberField(unique=True, blank=False, region="IR")

	def __str__(self):
		return f"{self.user.get_full_name()} - {self.phone}"
