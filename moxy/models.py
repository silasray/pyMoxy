from django.db import models
import copy
import json
from types import NoneType

class __Tuple(tuple):
    
    def __getattr__(self, name):
        
        try:
            return self.index(name)
        except (ValueError, TypeError):
            raise AttributeError


TRANSACTION_STAGES = __Tuple(('REQUEST', 'RESPONSE'))
__VALUE_TYPES = (('UNKNOWN', lambda value: None, NoneType),
                 ('STRING', lambda value: None if value is None else value, basestring),
                 ('BOOL', lambda value: None if value is None else value == 'True', bool),
                 ('INT', lambda value: None if value is None else int(value), int),
                 ('FLOAT', lambda value: None if value is None else float(value), float))
VALUE_TYPES = __Tuple(value_type[0] for value_type in __VALUE_TYPES)
COERCE_VALUE = __Tuple(value_type[1] for value_type in __VALUE_TYPES)
VALUE_TYPE_MAP = {mapping[1] : mapping[0] for mapping in enumerate(value_type[2] for value_type in __VALUE_TYPES)}
__MESSAGE_FORMATS = (('JSON', json.loads, json.dumps),)
MESSAGE_FORMATS = __Tuple(message_format[0] for message_format in __MESSAGE_FORMATS)
DESERIALIZE_MESSAGE = __Tuple(message_format[1] for message_format in __MESSAGE_FORMATS)
SERIALIZE_MESSAGE = __Tuple(message_format[2] for message_format in __MESSAGE_FORMATS)


class RuleModel(models.Model):
    
    method_key = models.CharField(max_length=128)
    triggered_by = models.SmallIntegerField(choices=enumerate(TRANSACTION_STAGES))
    applied_during = models.SmallIntegerField(choices=enumerate(TRANSACTION_STAGES))
    applied_to = models.SmallIntegerField(choices=enumerate(TRANSACTION_STAGES))
    
    def apply_to(self, original_request, working_request=None,
                 original_response=None, working_response=None):
        
        transaction_stage = TRANSACTION_STAGES.REQUEST if original_response is None else TRANSACTION_STAGES.RESPONSE
        if self.applied_during == transaction_stage:
            trigger = original_request if self.triggered_by == TRANSACTION_STAGES.REQUEST else original_response
            for condition_model in self.ruleconditionmodel_set.all():
                if not condition_model.satisfied_by(trigger):
                    break
            else:
                if self.applied_to == TRANSACTION_STAGES.REQUEST:
                    if working_request is None:
                        working_request = copy.deepcopy(original_request)
                    for replacement_model in self.replacementvaluemodel_set.all():
                        replacement_model.apply(working_request)
                else:
                    if transaction_stage == TRANSACTION_STAGES.REQUEST:
                        for canned_response in self.cannedresponsemodel_set.all():
                            original_response = canned_response.as_dict()
                    else:
                        if working_response is None:
                            working_response = copy.deepcopy(original_response)
                        for replacement_model in self.replacementvaluemodel_set.all():
                            replacement_model.apply(working_response)
        return [original_request, working_request, original_response, working_response]


class RuleAttributeModel(models.Model):
    
    class Meta(object):
        
        abstract = True
    
    rule_model = models.ForeignKey(RuleModel)


class ValueModel(models.Model):
    
    class Meta(object):
        
        abstract = True
    
    name = models.CharField(max_length=128)
    value_type = models.SmallIntegerField(choices=enumerate(VALUE_TYPES))
    _value = models.TextField(null=True)
    
    @property
    def value(self):
        
        return COERCE_VALUE[self.value_type](self._value)
    
    @value.setter
    def value(self, input):
        
        try:
            self.value_type = VALUE_TYPE_MAP[type(input)]
        except KeyError:
            for value_type, index in VALUE_TYPE_MAP.iteritems():
                if isinstance(input, value_type):
                    self.value_type = index
                    break
            else:
                raise ValueError
        self._value = None if input is None else str(input)


class RuleConditionModel(RuleAttributeModel, ValueModel):
    
    def satisfied_by(self, data):
        
        cursor = data
        for name_component in self.name.split('.'):
            try:
                cursor = cursor[name_component]
            except KeyError:
                return False
        return cursor == self.value


class RuleReplacementModel(models.Model):
    
    class Meta(object):
        
        abstract = True


class ReplacementValueModel(RuleAttributeModel, RuleReplacementModel, ValueModel):
    
    def apply(self, target):
        
        name_components = self.name.split('.')
        for name_component in name_components[:-1]:
            if name_component not in target:
                target[name_component] = {}
            target = target[name_component]
        target[name_components[-1]] = self.value


class CannedResponseModel(RuleAttributeModel, RuleReplacementModel):
    
    _headers = models.TextField()
    _body = models.TextField()
    message_format = models.SmallIntegerField(choices=enumerate(MESSAGE_FORMATS))
    
    @property
    def body(self):
        
        return DESERIALIZE_MESSAGE[self.message_format](self._body)
    
    @body.setter
    def body(self, value):
        
        self._body = SERIALIZE_MESSAGE[self.message_format](value)
    
    @property
    def headers(self):
        
        return json.loads(self._headers)
    
    @headers.setter
    def headers(self, value):
        
        self._headers = json.dumps(value)
    
    def as_dict(self):
        
        return {'headers' : self.headers,
                'body' : self.body}
    
    @classmethod
    def from_dict(cls, data):
        
        return cls(message_format=getattr(MESSAGE_FORMATS, data['message_format']),
                   headers=data['headers'],
                   body=data['body'])