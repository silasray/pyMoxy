from httplib2 import Http
from abc import ABCMeta, abstractmethod
from string import Template
import json
from moxy.models import RuleModel, TRANSACTION_STAGES


class TransactionData(list):
    
    field_map = {field_data[1] : field_data[0] for field_data in enumerate(('original_request',
                                                                            'working_request',
                                                                            'original_response',
                                                                            'working_response'))}
    
    def __init__(self, original_request, working_request=None,
                 original_response=None, working_response=None):
        
        if isinstance(original_request, (list, tuple)):
            list.__init__(self, original_request)
        else:
            list.__init__(self, (original_request,
                                 working_request,
                                 original_response,
                                 working_response))
    
    def __getattr__(self, name):
        
        try:
            return self[TransactionData.field_map[name]]
        except KeyError:
            raise AttributeError
    
    def __setattr__(self, name, value):
        
        try:
            self[TransactionData.field_map[name]] = value
        except KeyError:
            list.__setattr__(self, name, value)


class Mock(object):
    
    def __init__(self, proxy, method_key):
        
        self._proxy = proxy
        self._method_key = method_key
    
    def process(self, request_data):
        
        data = TransactionData(request_data)
        method_rules = RuleModel.objects.filter(method_key=self._method_key)
        for rule in method_rules.filter(applied_during=TRANSACTION_STAGES.REQUEST):
            data = TransactionData(rule.apply_to(*data))
        if data.original_response is None:
            data.original_response = self._proxy(data.original_request if data.working_request is None else data.working_request)
        for rule in method_rules.filter(applied_during=TRANSACTION_STAGES.RESPONSE):
            data = TransactionData(rule.apply(*data))
        return data.original_response if data.working_response is None else data.working_response


class CallProxy(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self, http_method, host, path_pattern):
        
        self._http_method = http_method
        self._host = host
        self._path_template = Template(path_pattern)
    
    def __call__(self, request_data):
        
        http = Http(disable_ssl_certificate_validation=True)
        headers, body = http.request(self._get_uri(request_data),
                                     self._http_method,
                                     headers=self._get_headers(request_data),
                                     body=self._get_body(request_data))
        return self._parse_response(headers, body)
    
    def _get_uri(self, request_data):
        
        return self._host + self._path_template.substitute(request_data)
    
    def _get_headers(self, request_data):
        
        try:
            return request_data['headers']
        except KeyError:
            return None
    
    @abstractmethod
    def _get_body(self, request_data):
        
        raise NotImplementedError
    
    @abstractmethod
    def _parse_response(self, headers, body):
        
        raise NotImplementedError


class JsonProxy(CallProxy):
    
    def _get_body(self, request_data):
        
        try:
            return json.dumps(request_data['body'])
        except KeyError:
            return ''
    
    def _parse_response(self, headers, body):
        
        return {'headers' : headers, 'body' : json.loads(body)}