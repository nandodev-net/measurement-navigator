# Django imports
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic           import TemplateView
from django.views.generic.edit import UpdateView, CreateView
from django.views.generic import DetailView
from django.contrib.auth.hashers import make_password
import random
import string

# Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin

# Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta

# Local imports
from apps.main.users.models import CustomUser
from .forms import CustomUserForm, CustomUserPassForm

# Permission imports
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from apps.main.users import decorators

@method_decorator([login_required, decorators.admin_required], name='dispatch')
class UsersList(VSFLoginRequiredMixin, TemplateView):

    template_name = "registration/list-users.html"
    queryset = CustomUser.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = CustomUser.objects.order_by('id')
        
        context['object_list'] = []

        for i in query:
            if i.is_admin:
                role = 'Admin'
            elif i.is_analist:
                role = 'Analist'
            elif i.is_editor:
                role = 'Editor'
            else:
                role = 'Guest'

            if i.is_superuser:
                role ='Superuser'

            if i.raw_pss:
                raw_pass = True
            else:
                raw_pass = False
                
            context['object_list'].append({'id':i.id,'username':i.username, 'first_name':i.first_name, 
            'last_name':i.last_name, 'email':i.email,'role':role, 'is_active':i.is_active, 'raw_pass': raw_pass })
        return context  


@method_decorator([login_required, decorators.admin_required], name='dispatch')

class UserCreateView(VSFLoginRequiredMixin, CreateView):
    model = CustomUser
    queryset = CustomUser.objects.all()
    form_class = CustomUserForm
    template_name = "registration/create-users.html"
    success_url = "/dashboard/users/"

    def get_random_alphanumeric_string(self, length):
        letters_and_digits = string.ascii_letters + string.digits
        result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
        return result_str

    def get_context_data(self, **kwargs):

        context = super(UserCreateView, self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):

        self.object = None
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        
        password = self.get_random_alphanumeric_string(8)
        self.object = CustomUser(
            username = form.cleaned_data['username'],
            first_name = form.cleaned_data['first_name'],
            last_name = form.cleaned_data['last_name'],
            email = form.cleaned_data['email'],
            raw_pss = password,
            password = make_password(password),
            is_active = True,
            date_joined = datetime.now()
        )

        if form.cleaned_data['role'] == "2":
            self.object.is_admin = True
            self.object.is_staff = True

        elif form.cleaned_data['role'] == "3":
            self.object.is_analist = True
            self.object.is_staff = True
        
        elif form.cleaned_data['role'] == "4":
            self.object.is_editor = True
            self.object.is_staff = True
        
        else:
            self.object.is_guest = True
            self.object.is_staff = True            


        if form.cleaned_data['role'] == "1":
            self.object.is_admin = True
            self.object.is_analist = True
            self.object.is_editor = True
            self.object.is_guest = True
            self.object.is_staff = True
            self.object.is_superuser = True
        
        self.object.save()
        return HttpResponseRedirect("/dashboard/users/")

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form,
            )
        )

@method_decorator([login_required, decorators.admin_required], name='dispatch')

class UserUpdateView(VSFLoginRequiredMixin, UpdateView):
    form_class = CustomUserForm
    model = CustomUser 
    queryset = CustomUser.objects.all()
    template_name = "registration/user-edit-form.html"
    success_url = "/dashboard/users/"

    def get_context_data(self, **kwargs):

        context = super(UserUpdateView, self).get_context_data(**kwargs)

        i = get_object_or_404(CustomUser, pk=self.kwargs['pk'])

        if i.is_admin:
            role = 2
            
        elif i.is_analist:
            role = 3

        elif i.is_editor:
            role = 4

        else:
            role = 5

        if i.is_superuser:
            role = 1

        context['form'] = CustomUserForm(
           initial = {
                'username':i.username,
                'first_name':i.first_name,
                'last_name':i.last_name,
                'email':i.email,
                'role': [role]            
           }
        )
        
        return context  


    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):

        self.object.username = form.cleaned_data['username']
        self.object.first_name = form.cleaned_data['first_name']
        self.object.last_name = form.cleaned_data['last_name']
        self.object.email = form.cleaned_data['email']   


        if form.cleaned_data['role'] == "1":
            self.object.is_admin = True
            self.object.is_analist = True
            self.object.is_editor = True
            self.object.is_guest = True
            self.object.is_staff = True
            self.object.is_superuser = True
            self.object.save()
            return HttpResponseRedirect("/dashboard/users/")

        elif form.cleaned_data['role'] == "2":
            self.object.is_admin = True
            self.object.is_analist = False
            self.object.is_editor = False
            self.object.is_guest = False
            self.object.is_staff = True
            self.object.is_superuser = False
            self.object.save()
            return HttpResponseRedirect("/dashboard/users/")

        elif form.cleaned_data['role'] == "3":
            self.object.is_admin = False
            self.object.is_analist = True
            self.object.is_editor = False
            self.object.is_guest = False
            self.object.is_staff = True
            self.object.is_superuser = False
            self.object.save()
            return HttpResponseRedirect("/dashboard/users/")
        
        elif form.cleaned_data['role'] == "4":
            self.object.is_admin = False
            self.object.is_analist = False
            self.object.is_editor = True
            self.object.is_guest = False
            self.object.is_staff = True
            self.object.is_superuser = False
            self.object.save()
            return HttpResponseRedirect("/dashboard/users/")
        
        else:
            self.object.is_admin = False
            self.object.is_analist = False
            self.object.is_editor = False
            self.object.is_guest = True
            self.object.is_staff = True
            self.object.is_superuser = False
            self.object.save()
            return HttpResponseRedirect("/dashboard/users/")        


    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form
            )
        )


@method_decorator([login_required, decorators.admin_required], name='dispatch')
class UserCreateModalView(VSFLoginRequiredMixin, CreateView):
    model = CustomUser
    queryset = CustomUser.objects.all()
    form_class = CustomUserForm
    template_name = "registration/create-user-form.html"
    success_url = "/dashboard/users/"

    def get_random_alphanumeric_string(self, length):
        letters_and_digits = string.ascii_letters + string.digits
        result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
        return result_str

    def get_context_data(self, **kwargs):

        context = super(UserCreateModalView, self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):

        self.object = None
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        
        password = self.get_random_alphanumeric_string(8)
        self.object = CustomUser(
            username = form.cleaned_data['username'],
            first_name = form.cleaned_data['first_name'],
            last_name = form.cleaned_data['last_name'],
            email = form.cleaned_data['email'],
            raw_pss = password,
            password = make_password(password),
            is_active = True,
            date_joined = datetime.now()
        )

        if form.cleaned_data['role'] == "2":
            self.object.is_admin = True
            self.object.is_staff = True

        elif form.cleaned_data['role'] == "3":
            self.object.is_analist = True
            self.object.is_staff = True
        
        elif form.cleaned_data['role'] == "4":
            self.object.is_editor = True
            self.object.is_staff = True
        
        else:
            self.object.is_guest = True
            self.object.is_staff = True  


        if form.cleaned_data['role'] == "1":
            self.object.is_admin = True
            self.object.is_analist = True
            self.object.is_editor = True
            self.object.is_guest = True
            self.object.is_staff = True
            self.object.is_superuser = True
        
        self.object.save()
        return HttpResponseRedirect("/dashboard/users/")

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form,
            )
        )


@method_decorator([login_required, decorators.admin_required], name='dispatch')
class CustomUserPasswdRevealView(VSFLoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = "registration/reveal-user-psswd.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context




def CurtomUserActivationView(request, pk):
    custom_usr = get_object_or_404(CustomUser, id = pk)

    if custom_usr.is_active:
        custom_usr.is_active = False
    else:
        custom_usr.is_active = True
    
    custom_usr.save()

    return HttpResponseRedirect("/dashboard/users/")




class CustomUserCreatePass(VSFLoginRequiredMixin, UpdateView):
    form_class = CustomUserPassForm
    model = CustomUser 
    queryset = CustomUser.objects.all()
    template_name = "registration/user-update-pass.html"
    success_url = "/dashboard/logout/"

    def get_context_data(self, **kwargs):

        context = super(CustomUserCreatePass, self).get_context_data(**kwargs)
        return context  


    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid() and (form.cleaned_data['password1'] == form.cleaned_data['password2']):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
            

    def form_valid(self, form):
        self.object.password = make_password(form.cleaned_data['password1'])
        self.object.raw_pss = None
        self.object.save()
        return HttpResponseRedirect("/dashboard/logout/")


    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form
            )
        )