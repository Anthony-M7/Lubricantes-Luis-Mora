from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

# class RestrictAdminMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         if request.path.startswith(reverse('admin:index')):
#             if not request.user.is_superuser:
#                 return HttpResponseForbidden("Acceso denegado al panel de administración")