# Persistence specification

## Broker with cassette store saves to file on record

* Create empty cassette
* Configure mock live responder returning "persisted-data"
* Configure JSON file cassette store at temporary path
* Storing broker in "record" mode receives request for "test-proto" "fetch" "resource-123"
* Response stream should contain "persisted-data"
* Cassette file should exist at configured path

## Recorded cassette can be saved to file and reloaded for replay

* Create empty cassette
* Configure mock live responder returning "persisted-data"
* Configure JSON file cassette store at temporary path
* Storing broker in "record" mode receives request for "test-proto" "fetch" "resource-123"
* Load cassette from file store
* Broker in "replay" mode receives request for "test-proto" "fetch" "resource-123"
* Response stream should contain "persisted-data"
