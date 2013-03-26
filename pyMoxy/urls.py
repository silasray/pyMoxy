from django.conf.urls import patterns, include, url
from moxy.views import ValueReplacementRuleResource, CannedResponseRuleResource
from amazonIAPRVS.views import IAPRVSResource

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pyMoxy.views.home', name='home'),
    # url(r'^pyMoxy/', include('pyMoxy.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^moxy/(?P<method_key>.+)/value_replacement/$', ValueReplacementRuleResource.as_view()),
    url(r'^moxy/(?P<method_key>.+)/canned_response/$', CannedResponseRuleResource.as_view()),
    url(r'^version/2.0/(?P<action>.+)/developer/(?P<developer_key>.+)'
        r'/user/(?P<user_id>.+)/purchaseToken/(?P<purchase_token>.+)$',
        IAPRVSResource.as_view())
)
