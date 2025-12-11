from rest_framework import exceptions
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
	response = exception_handler(exc, context)
	custom_response_data = {'detial': ''}

	match type(exc):
		case exceptions.Throttled:
			custom_response_data['detial'] = 'تعداد درخواست‌هات بیش از حد مجازه. کمی صبر کن!'
			response.data = custom_response_data
		case exceptions.AuthenticationFailed:
			match exc.detail.code:
				case "no_active_account":
					custom_response_data['detial'] = 'هیچ حسابی با این مشخصات پیدا نشد.'
					response.data = custom_response_data

	return response
