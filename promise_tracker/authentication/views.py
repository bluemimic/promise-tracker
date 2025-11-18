from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View

from promise_tracker.authentication.forms import LoginForm
from promise_tracker.authentication.services import AuthService
from promise_tracker.common.utils import bootstrapify_form
from promise_tracker.core.exceptions import ApplicationError


class LoginView(SuccessMessageMixin, View):
    template_name = "auth/login.html"
    success_message = _("User have successfully logged in!")

    def get(self, request, *args, **kwargs):
        form = LoginForm()
        form = bootstrapify_form(form)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            auth_service = AuthService(request)

            try:
                auth_service.login(email=email, password=password)
                next_url = self.request.GET.get("next")

                return redirect(next_url or settings.LOGIN_REDIRECT_URL)
            except ApplicationError as e:
                form.add_error(None, e.message)

        form = bootstrapify_form(form)
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    template_name = "auth/logged_out.html"

    def get(self, request, *args, **kwargs):
        auth_service = AuthService(request)
        auth_service.logout()

        return render(request, self.template_name)
