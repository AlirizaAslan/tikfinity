"""
URL configuration for DjangoAdmin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _


from django.contrib.sitemaps.views import sitemap
from .sitemaps import  sitemap_view

from django.urls import path, re_path
from django.views.generic import TemplateView

from django.shortcuts import redirect

def home_redirect(request):
    return redirect('/tiktok/')

urlpatterns = [
    path('', home_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('tiktok/', include('tiktok_live.urls')),
    
    #re_path(r'^.*/$', TemplateView.as_view(template_name='404.html'), name='404'),
    
    #path('', include('Calculator.urls')),
    #path('translated-urls/', views.translated_urls, name='translated_urls'),
      #path('<str:language_code>/<str:page_name>/', views.index, name='index'),
      
    #path('<str:language_code>/<path:url>/', views.page_view, name='page_view'),  # Diğer dinamik URL'ler
    #path('i18n/setlang/', views.set_language, name='set_language'),  # Dil değiştirme URL'si
    
]

# urls.py'ye eklenecek view
# def custom_sitemap_view(request):
#     sitemaps = {
#         'dynamic': MultilingualSitemap,
#     }
#     return sitemap(request, sitemaps)

urlpatterns += i18n_patterns(
    #path('set_language/', views.set_language, name='set_language'),
    # Diğer uluslararasılaştırma URL desenleriniz
    

     







 #path(_('pregnancy-calculator/'), views.pregnancy_calculator, name='pregnancy_calculator'), #hata veriypr
#path(_('melatonin-dosage-calculator/'), views.melatonin_calculator, name='melatonin_calculator'), # hata veriyor
#path(_('weight-loss-calculator/'), views.weight_loss_calculator, name='weight_loss_calculator'),  # hata var kodda düzelt


































prefix_default_language=False,
)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
