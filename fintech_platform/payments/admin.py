from django.contrib import admin
from .models import Wallet, Project, Investment, PlatformBucket


admin.site.register(Wallet)
admin.site.register(Project)
admin.site.register(Investment)
admin.site.register(PlatformBucket)
