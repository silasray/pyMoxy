from django.http import HttpResponse
from django.views.generic.base import View
from moxy.core import Mock, JsonProxy
import json


class IAPRVSResource(View):
    
    def get(self, request, action, developer_key, user_id, purchase_token):
        
        proxy = JsonProxy('GET',
                          'https://appstore-sdk.amazon.com',
                          '/version/2.0/${action}/developer/${developer_key}/user/${user_id}/'
                          'purchaseToken/${purchase_token}')
        mock = Mock(proxy, 'AmazonIAPRVS')
        headers = {k.split('HTTP_', 1)[-1] : v for k, v in request.META.iteritems() if
                   k.startswith('HTTP_') or k in ('CONTENT_TYPE', 'CONTENT_LENGTH')}
        response_data = mock.process({'headers' : headers,
                                      'action' : action,
                                      'developer_key' : developer_key,
                                      'user_id' : user_id,
                                      'purchase_token' : purchase_token})
        response = HttpResponse(json.dumps(response_data['body']), status=response_data['headers'].pop('status'))
        for name, value in response_data['headers'].iteritems():
            response[name] = value
        return response