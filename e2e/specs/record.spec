# Record specification

## Broker raises error for MISS in replay mode

* Create empty cassette
* Broker in "replay" mode receives request for "test-proto" "fetch" "resource-123"
* Broker should raise InteractionNotFoundError

## Broker forwards MISS to live upstream in auto mode

* Create empty cassette
* Configure mock live responder returning "live-response-data"
* Broker in "auto" mode receives request for "test-proto" "fetch" "resource-123"
* Response stream should contain "live-response-data"
* Cassette should contain one recorded interaction
