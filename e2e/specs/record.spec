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

## Broker forwards MISS to live upstream in record mode

* Create empty cassette
* Configure mock live responder returning "live-response-data"
* Broker in "record" mode receives request for "test-proto" "fetch" "resource-123"
* Response stream should contain "live-response-data"
* Cassette should contain one recorded interaction

## Broker does not forward HIT in auto mode

* Create cassette with recorded interaction for "test-proto" "fetch" "resource-123"
* Configure tracking live responder returning "live-response-data"
* Broker in "auto" mode receives request for "test-proto" "fetch" "resource-123"
* Live responder should not be called

## Broker always forwards to live in record mode even on HIT

* Create cassette with recorded interaction for "test-proto" "fetch" "resource-123"
* Configure tracking live responder returning "fresh-live-data"
* Broker in "record" mode receives request for "test-proto" "fetch" "resource-123"
* Live responder should be called
* Response stream should contain "fresh-live-data"
