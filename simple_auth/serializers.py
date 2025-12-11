from rest_framework import serializers
from django.contrib.auth.models import User
from phonenumber_field.serializerfields import PhoneNumberField


class StartAuthSerializer(serializers.Serializer):
	phone = PhoneNumberField(
		region="IR",
		error_messages={
			'required': 'وارد کردن شماره موبایل اجباریه!',
			'blank': 'شماره موبایل نمیتونه خالی باشه!',
			'null': 'شماره موبایل نمیتونه خالی باشه!',
			'invalid': 'شماره موبایل وارد شده معتبر نیست.',
		},
	)


class VerifyOTPSerializer(serializers.Serializer):
	phone = PhoneNumberField(
		region="IR",
		error_messages={
			'required': 'وارد کردن شماره موبایل اجباریه!',
			'blank': 'شماره موبایل نمیتونه خالی باشه!',
			'null': 'شماره موبایل نمیتونه خالی باشه!',
			'invalid': 'شماره موبایل وارد شده معتبر نیست.',
		},
	)
	otp = serializers.CharField(
		max_length=6,
		error_messages={
			'required': 'وارد کردن کد یکبار مصرف اجباریه!',
			'blank': 'کد یکبار مصرف نمیتونه خالی باشه!',
			'null': 'کد یکبار مصرف نمیتونه خالی باشه!',
			'invalid': 'کد یکبار مصرف وارد شده معتبر نیست.',
			'max_length': 'کد یکبار مصرف باید ۶ رقم باشه.',
		},
	)


class CompleteSignupSerializer(serializers.Serializer):
	token = serializers.CharField(  # Temporary token from OTP verification
		max_length=36,
		error_messages={
			'required': 'توکن نامعتبره. دوباره وارد شو.',
			'blank': 'توکن نامعتبره. دوباره وارد شو.',
			'null': 'توکن نامعتبره. دوباره وارد شو.',
			'invalid': 'توکن نامعتبره. دوباره وارد شو.',
			'max_length': 'توکن نامعتبره. دوباره وارد شو.',
		},
	)
	first_name = serializers.CharField(
		max_length=30,
		error_messages={
			'required': 'وارد کردن نام اجباریه!',
			'blank': 'نام نمیتونه خالی باشه!',
			'null': 'نام نمیتونه خالی باشه!',
			'max_length': 'نام نمیتونه بیشتر از ۳۰ کاراکتر باشه.',
		},
	)
	last_name = serializers.CharField(
		max_length=30,
		error_messages={
			'required': 'وارد کردن نام خانوادگی اجباریه!',
			'blank': 'نام خانوادگی نمیتونه خالی باشه!',
			'null': 'نام خانوادگی نمیتونه خالی باشه!',
			'max_length': 'نام خانوادگی نمیتونه بیشتر از ۳۰ کاراکتر باشه.',
		},
	)
	email = serializers.EmailField(
		max_length=254,
		error_messages={
			'required': 'وارد کردن ایمیل اجباریه!',
			'blank': 'ایمیل نمیتونه خالی باشه!',
			'null': 'ایمیل نمیتونه خالی باشه!',
			'max_length': 'ایمیل نمیتونه بیشتر از ۲۵۴ کاراکتر باشه.',
		},
	)
	password = serializers.CharField(
		write_only=True, min_length=8, max_length=128,
		error_messages={
			'required': 'وارد کردن رمز اجباریه!',
			'blank': 'رمز نمیتونه خالی باشه!',
			'null': 'رمز نمیتونه خالی باشه!',
			'max_length': 'رمز نمیتونه بیشتر از ۱۲۸ کاراکتر باشه.',
			'min_length': 'رمز نمیتونه کمتر از ۸ کاراکتر باشه.',
		},
	)


class DefendedTokenObtainPairSerializer(serializers.Serializer):
	username = PhoneNumberField(
		region="IR",
		error_messages={
			'required': 'وارد کردن شماره موبایل اجباریه!',
			'blank': 'شماره موبایل نمیتونه خالی باشه!',
			'null': 'شماره موبایل نمیتونه خالی باشه!',
			'invalid': 'شماره موبایل وارد شده معتبر نیست.',
		},
	)
	password = serializers.CharField(
		write_only=True,
		error_messages={
			'required': 'وارد کردن رمز اجباریه!',
			'blank': 'رمز نمیتونه خالی باشه!',
			'null': 'رمز نمیتونه خالی باشه!',
		},
	)
