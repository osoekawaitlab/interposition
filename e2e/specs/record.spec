# Record specification

## Broker raises error for MISS in replay mode

* Create empty cassette
* Broker in "replay" mode receives request for "test-proto" "fetch" "resource-123"
* Broker should raise InteractionNotFoundError
