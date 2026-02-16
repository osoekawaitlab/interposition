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

## Broker created via from_store replays recorded interaction

* Create empty cassette
* Configure mock live responder returning "from-store-data"
* Configure JSON file cassette store at temporary path
* Storing broker in "record" mode receives request for "test-proto" "fetch" "resource-123"
* Create broker from store in "replay" mode
* Broker replays request for "test-proto" "fetch" "resource-123"
* Response stream should contain "from-store-data"

## Broker created via from_store with auto mode forwards MISS to live responder

* Create empty cassette
* Configure mock live responder returning "live-auto-data"
* Configure JSON file cassette store at temporary path
* Save current cassette to file store
* Create broker from store in "auto" mode
* Broker replays request for "test-proto" "fetch" "resource-999"
* Response stream should contain "live-auto-data"
