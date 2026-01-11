# Replay specification

## Broker replays matching interaction

* Create cassette with recorded interaction for "test-proto" "fetch" "resource-123"
* Broker receives identical request for "test-proto" "fetch" "resource-123"
* Response stream should contain recorded chunks in order
* Response stream should complete without errors

## Broker raises error for unmatched request

* Create cassette with recorded interaction for "test-proto" "fetch" "resource-123"
* Broker receives different request for "test-proto" "store" "resource-456"
* Broker should raise InteractionNotFoundError

## Broker returns first matching interaction

* Create cassette with two identical interactions for "test-proto" "fetch" "resource-123"
* Broker receives request for "test-proto" "fetch" "resource-123"
* Response stream should contain chunks from FIRST recorded interaction

## Broker treats header order as significant

* Create cassette with recorded interaction headers "X-First:1,X-Second:2"
* Broker receives request with headers "X-Second:2,X-First:1"
* Broker should raise InteractionNotFoundError
