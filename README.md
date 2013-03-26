pyMoxy
======
Tool, intended for use in test environments, for mocking/proxying REST services that provides a RESTful interface 
(as well as a web app interface, not yet implemented) for managing value replacment and canned response rules.  
Current version has an example impelementation for the Amazon In App Purchase Receipt Verification Service API.

Endpoints:
-   [host]/moxy/[method_key]/value_replacement/

        {"triggered_by" : ("REQUEST"/"RESPONSE"),
         "applied_to" : ("REQUEST"/"RESPONSE"),
         "conditions" : {"condition_name_0" : condition_value_0,
                         "condition_name_1" : condition_value_1,
                         "condition_name_n" : condition_value_n},
         "replacements" : {"replacement_name_0" : replacement_value_0,
                           "replacement_name_1" : replacement_value_1,
                           "replacement_name_n" : replacement_value_n}}
-   [host]/moxy/[method_key]/canned_response/

        {"conditions" : {"condition_name_0" : condition_value_0,
                         "condition_name_1" : condition_value_1,
                         "condition_name_n" : condition_value_n},
         "headers" : {"header_name_0" : header_value_0,
                           "header_name_1" : header_value_1,
                           "header_name_n" : header_value_n}
         "message_format" : "JSON",
         "body" : {(arbitrary JSON data)}
-   [host]/[Amazon IAP RVS URI]
        See Amazon docs for RVS API

All value replacement rules have an applied_during value equal to the applied_to value provided at creation.  Canned 
response rules have triggered_by and applied_durng set to REQUEST and applied_to set to RESPONSE automatically.  Rules 
are unique on the combination of triggered_by, applied_durung, applied_to, conditions, and method_key.

PUT/POST will create a new rule if none exists, otherwise they will add all replacements in the request to the existing 
rule.  200 on success, 500 if any error.
DELETE will delete an existing rule.  Everything other than the uniqueness constraints in the request is ignored.  200 
on success, 404 if no matching rule was found, 500 if any other error.

This tool will get the job done for most use cases, but it does still have many warts, so YMMV.  Requires Django, 
httplib2, and sqlite (default setup for Django).
