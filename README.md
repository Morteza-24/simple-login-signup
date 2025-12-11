# Simple Authentication using Django Rest Framework with Rate-Limiting

## Postman Collections

Import the [`Simple Auth.postman_collection.json`](https://github.com/Morteza-24/simple-login-signup/blob/main/Simple%20Auth.postman_collection.json) file in Postman.

## Quick Start

1. Clone the repository:
	```bash
	git clone https://github.com/Morteza-24/simple-login-signup.git
	```
2. Enter the directory:
	```bash
	cd simple-login-signup/
	```

3. Create a virtual environment:
	```bash
	python -m venv vnv
	```

4. Activate the virtual environment:
	```bash
	source vnv/bin/activate	# on Linux
	```

5. Install the required packages:
	```bash
	pip install -r requirements.txt
	```

6. Run a redis server on `127.0.0.1:6379`:
	```bash
	sudo systemctl start redis-server  # on Linux
	```

7. Run the Django project:

	```bash
	python manage.py runserver
	```

## Architectural Decisions

**Why `django-defender`?** django-defender is added to provide lightweight protection against brute-force attacks. Custom re-implementations of security controls are dangerous and not recommended. Relying on well-reviewed libraries and frameworks (like Django Defender) is good practice.

**Why use `DEFENDER_DISABLE_IP_LOCKOUT`?** By default, django-defender only works on login, but I wanted to use it on both login and signup. So I handled these multiple defended endpoints by using different usernames in django-defeder. Therefore, I had to use username lockouts to handle both IP and username lockouts.

**Why Simple JWT?** Simple JWT provides a standard JWT authentication layer. Using JWT tokens instead of server-side sessions is a trade-off, it offers stateless, scalable authentication but requires careful handling of token storage, expiration, and revocation.

**Why the `Profile` model?** I wanted to store users' phone numbers. According to [Django's documentations](https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#extending-the-existing-user-model), "if you wish to store information related to `User`, you can use a `OneToOneField` to a model containing the fields for additional information. This one-to-one model is often called a profile model, as it might store non-auth related information about a site user."

## Time Spent on This Project

~ 2 days
