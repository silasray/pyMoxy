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
response rules have triggered_by and applied_during set to REQUEST and applied_to set to RESPONSE automatically.  Rules 
are unique on the combination of triggered_by, applied_durung, applied_to, conditions, and method_key.

PUT/POST will create a new rule if none exists, otherwise they will add all replacements in the request to the existing 
rule.  200 on success, 500 if any error.
DELETE will delete an existing rule.  Everything other than the uniqueness constraints in the request is ignored.  200 
on success, 404 if no matching rule was found, 500 if any other error.

This tool will get the job done for most use cases, but it does still have many warts, so YMMV.  Requires Django, 
httplib2, and sqlite (default setup for Django).


Basic example useage:

The live Amazon RVS will respond with a valid ENTITLED type product to a GET on:

    [moxy host]/version/2.0/verify/developer/2:oPYK5fU9aIzIdQkXor93UI3mfqoexts1vPLEDtkkx2sz0imC70p1hp_Za3OVlOm3:RsR0
    W-BcE_HwCsq0VcSPCQ==/user/l3HL7XppEMhrOGDnur9-ulvqomrSg6qyODKmah76lJU=/purchaseToken/2:FlrXSsmgOBKXoBbf6BtIrBtmb
    ZLNr92laKjtTMTlz9tQyYUXl-vuEsdl1Hr8g0xxsQIa8JP3uIqNfmatmSRnOamsrYWGlpKFTrKb0IWXPlYlXhY4EH0ufJYuWzoOicNXCm6BBH9se
    KczkQ_I-QObpjCuHnlZk4pXgl3g_VggJZGpWBtuvYAqOVXYfcMjf268BaMjVX7plTQ_MPvzLrRNGQ==:qsy5n5MMZM4u-LlDrqGp5Q==

Returning:

    {"endDate":null,
     "itemType":"ENTITLED",
     "purchaseToken":"2:FlrXSsmgOBKXoBbf6BtIrBtmb%20%20%20%20%20ZLNr92laKjtTMTlz9tQyYUXl-vuEsdl1Hr8g0xxsQIa8JP3uIqNfm
     atmSRnOamsrYWGlpKFTrKb0IWXPlYlXhY4EH0ufJYuWzoOicNXCm6BBH9se%20%20%20%20%20KczkQ_I-QObpjCuHnlZk4pXgl3g_VggJZGpWBt
     uvYAqOVXYfcMjf268BaMjVX7plTQ_MPvzLrRNGQ==:qsy5n5MMZM4u-LlDrqGp5Q==",
     "sku":"com.amazon.android.comics.OCT110363",
     "startDate":null}

However, this is ungainly, and the test data can't be used to generate a CONSUMABLE type.  Let's make this better.  
If we submit the following requests to the moxy, we'll be able to compose a more consise call, and also have whatever 
piece of product code that is running through the moxy be able to recieve a CONSUMABLE type without having to do any 
changes to the Amazon or product code.

First, provide shorthands for developer_key, user_id, and purchase_token on the requests:

    POST
    [moxy host]/moxy/AmazonIAPRVS/value_replacement/
    {"triggered_by" : "REQUEST",
     "applied_to" : "REQUEST",
     "conditions" : {"developer_key" : "live_test"},
     "replacements" : {"developer_key" : "2:oPYK5fU9aIzIdQkXor93UI3mfqoexts1vPLEDtkkx2sz0imC70p1hp_Za3OVlOm3:RsR0
    W-BcE_HwCsq0VcSPCQ=="}}

    POST
    [moxy host]/moxy/AmazonIAPRVS/value_replacement/
    {"triggered_by" : "REQUEST",
     "applied_to" : "REQUEST",
     "conditions" : {"user_id" : "live_test"},
     "replacements" : {"user_id" : "l3HL7XppEMhrOGDnur9-ulvqomrSg6qyODKmah76lJU="}}

    POST
    [moxy host]/moxy/AmazonIAPRVS/value_replacement/
    {"triggered_by" : "REQUEST",
     "applied_to" : "REQUEST",
     "conditions" : {"purchase_token" : "live_test_entitlement_as_consumable"},
     "replacements" : {"purchase_token" : "2:FlrXSsmgOBKXoBbf6BtIrBtmbZLNr92laKjtTMTlz9tQyYUXl-vuEsdl1Hr8g0xxsQI
    a8JP3uIqNfmatmSRnOamsrYWGlpKFTrKb0IWXPlYlXhY4EH0ufJYuWzoOicNXCm6BBH9seKczkQ_I-QObpjCuHnlZk4pXgl3g_VggJZGpWBt
    uvYAqOVXYfcMjf268BaMjVX7plTQ_MPvzLrRNGQ==:qsy5n5MMZM4u-LlDrqGp5Q=="}}

Then replace the values coming back in the response:

    POST
    [moxy host]/moxy/AmazonIAPRVS/value_replacement/
    {"triggered_by" : "REQUEST",
     "applied_to" : "RESPONSE",
     "conditions" : {"purchase_token" : "live_test_entitlement_as_consumable"},
     "replacements" : {"body.purchaseToken" : "live_test_entitlement_as_consumable"}}

    POST
    [moxy host]/moxy/AmazonIAPRVS/value_replacement/
    {"triggered_by" : "REQUEST",
     "applied_to" : "RESPONSE",
     "conditions" : {"action" : "verify",
                     "purchase_token" : "live_test_entitlement_as_consumable"},
     "replacements" : {"body.itemType" : "CONSUMABLE",
                       "body.sku" : "com.amazon.android.comics.consumableHero"}}

Note that we created a rule to replace all purchase_token values in responses to requests with purchase_token values of 
live_test_entitlement_as_consumable with the same string, but are only replacing the itemType and sku for 
matching purchase_token values when the action is verify.  This keeps us from mangling renew calls.  After these calls, 
our previous call to RVS becomes:

    [moxy host]/version/2.0/verify/developer/live_test/user/live_test/purchaseToken/live_test_entitlement_as_consumable

Returning:

    {"sku": "com.amazon.android.comics.consumableHero",
     "startDate": null,
     "endDate": null,
     "itemType": "CONSUMABLE",
     "purchaseToken": "live_test_entitlement_as_consumable"}
