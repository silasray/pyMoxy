from django.views.generic import View
from moxy.models import (RuleModel, RuleConditionModel, DelayResponseModel,
                         ReplacementValueModel, CannedResponseModel,
                         TRANSACTION_STAGES, VALUE_TYPES, MESSAGE_FORMATS)
import json
from django.http import HttpResponse


def get_rule(method_key, conditions_dict, triggered_by, applied_during, applied_to):
    
    for rule in RuleModel.objects.filter(triggered_by=triggered_by,
                                         applied_during=applied_during,
                                         applied_to=applied_to,
                                         method_key=method_key,
                                         ruleconditionmodel__name__in=conditions_dict.keys()).distinct():
        if rule.ruleconditionmodel_set.count() != len(conditions_dict):
            continue
        for condition in rule.ruleconditionmodel_set.all():
            if conditions_dict[condition.name] != condition.value:
                break
        else:
            return rule
    return None


class ValueReplacementRuleResource(View):
    
    @staticmethod
    def extract_stage_data(body):
        
        triggered_by = getattr(TRANSACTION_STAGES, body['triggered_by'].upper())
        applied_during = applied_to = getattr(TRANSACTION_STAGES, body['applied_to'].upper())
        return triggered_by, applied_during, applied_to
    
    def post(self, request, method_key):
        
        body = json.loads(request.body)
        triggered_by, applied_during, applied_to = ValueReplacementRuleResource.extract_stage_data(body)
        rule = get_rule(method_key, body['conditions'], triggered_by, applied_during, applied_to)
        if rule is None:
            rule = RuleModel(method_key=method_key,
                             triggered_by=triggered_by,
                             applied_during=applied_during,
                             applied_to=applied_to)
            rule.save()
            for name, value in body['conditions'].iteritems():
                RuleConditionModel(rule_model=rule,
                                   name=name,
                                   value=value).save()
        for name, value in body['replacements'].iteritems():
            ReplacementValueModel(rule_model=rule,
                                  name=name,
                                  value=value).save()
        return HttpResponse()
    
    def put(self, request, method_key):
        
        return self.post(request, method_key)
    
    def delete(self, request, method_key):
        
        body = json.loads(request.body)
        triggered_by, applied_during, applied_to = ValueReplacementRuleResource.extract_stage_data(body)
        rule = get_rule(method_key, body['conditions'], triggered_by, applied_during, applied_to)
        if rule is None:
            return HttpResponse(status=404)
        else:
            rule.delete()
            return HttpResponse()


class CannedResponseRuleResource(View):
    
    @staticmethod
    def extract_stage_data(body):
        
        triggered_by = applied_during = TRANSACTION_STAGES.REQUEST
        applied_to = TRANSACTION_STAGES.RESPONSE
        return triggered_by, applied_during, applied_to
    
    def post(self, request, method_key):
        
        body = json.loads(request.body)
        triggered_by, applied_during, applied_to = CannedResponseRuleResource.extract_stage_data(body)
        rule = get_rule(method_key, body['conditions'], triggered_by, applied_during, applied_to)
        if rule is None:
            rule = RuleModel(method_key=method_key,
                             triggered_by=triggered_by,
                             applied_during=applied_during,
                             applied_to=applied_to)
            rule.save()
            for name, value in body['conditions'].iteritems():
                RuleConditionModel(rule_model=rule,
                                   name=name,
                                   value=value).save()
        canned_response = CannedResponseModel.from_dict(body)
        rule.cannedresponsemodel_set.add(canned_response)
        canned_response.save()
        return HttpResponse()
    
    def put(self, request, method_key):
        
        return self.post(request, method_key)
    
    def delete(self, request, method_key):
        
        body = json.loads(request.body)
        triggered_by, applied_during, applied_to = CannedResponseRuleResource.extract_stage_data(body)
        rule = get_rule(method_key, body['conditions'], triggered_by, applied_during, applied_to)
        if rule is None:
            return HttpResponse(status=404)
        else:
            rule.delete()
            return HttpResponse()


class DelayResponseRuleResource(View):
    
    @staticmethod
    def extract_stage_data(body):
        
        triggered_by = getattr(TRANSACTION_STAGES, body['triggered_by'].upper())
        # Allow for delay on request, default to delay on response
        try:
            applied_to = applied_during = getattr(TRANSACTION_STAGES, body.get('applied_during', body['applied_to']).upper())
        except KeyError:
            applied_to = applied_during = TRANSACTION_STAGES.RESPONSE
        return triggered_by, applied_during, applied_to
    
    def post(self, request, method_key):
        
        body = json.loads(request.body)
        triggered_by, applied_during, applied_to = DelayResponseRuleResource.extract_stage_data(body)
        rule = get_rule(method_key, body['conditions'], triggered_by, applied_during, applied_to)
        if rule is None:
            rule = RuleModel(method_key=method_key,
                             triggered_by=triggered_by,
                             applied_during=applied_during,
                             applied_to=applied_to)
            rule.save()
            for name, value in body['conditions'].iteritems():
                RuleConditionModel(rule_model=rule,
                                   name=name,
                                   value=value).save()
        DelayResponseModel(rule_model=rule, delay=body['delay']).save()
        return HttpResponse()
    
    def put(self, request, method_key):
        
        return self.post(request, method_key)
    
    def delete(self, request, method_key):
        
        body = json.loads(request.body)
        triggered_by, applied_during, applied_to = DelayResponseRuleResource.extract_stage_data(body)
        rule = get_rule(method_key, body['conditions'], triggered_by, applied_during, applied_to)
        if rule is None:
            return HttpResponse(status=404)
        else:
            rule.delete()
            return HttpResponse()


class RuleQueryResource(View):
    
    def post(self, request):
        
        query_data = json.loads(request.body)
        conditions_dict = query_data.pop("conditions", {})
        if conditions_dict:
            query_data['ruleconditionmodel__name__in'] = conditions_dict.keys()
        matching_rules = []
        for rule in RuleModel.objects.filter(**query_data).distinct():
            rule_dict = {'conditions' : {}}
            for condition in rule.ruleconditionmodel_set.all():
                if condition.name in conditions_dict.keys() and conditions_dict[condition.name] != condition.value:
                    break
                rule_dict['conditions'][condition.name] = condition.value
            else:
                rule_dict['method_key'] = rule.method_key
                rule_dict['triggered_by'] = rule.get_triggered_by_display()
                rule_dict['applied_to'] = rule.get_applied_to_display()
                rule_dict['applied_during'] = rule.get_applied_during_display()
                if rule.replacementvaluemodel_set.count():
                    rule_dict['replacements'] = {}
                    for replacement in rule.replacementvaluemodel_set.all():
                        rule_dict['replacements'][replacement.name] = replacement.value
                if rule.cannedresponsemodel_set.count():
                    rule_dict['canned_responses'] = [canned_response.as_dict() for canned_response in rule.cannedresponsemodel_set.all()]
                if rule.delayresponsemodel_set.count():
                    rule_dict['delays'] = [delay.delay for delay in rule.delayresponsemodel_set.all()]
                matching_rules.append(rule_dict)
        response = HttpResponse(json.dumps(matching_rules))
        response['Content-Type'] = 'application/json'
        return response