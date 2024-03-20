Pika RabbitMQ Client (instrumented with Streamdal)
=====================================================================================

This library has been instrumented with [Streamdal's Python SDK](https://github.com/streamdal/streamdal/tree/main/sdks/python).

## Getting Started

The following environment variables must be set before launching a producer or consumer:

1. `STREAMDAL_ADDRESS`
    - Address for the streamdal server (Example: `localhost:8082`)
1. `STREAMDAL_TOKEN`
    - Authentication token used by the server (Example: `1234`)
1. `STREAMDAL_SERVICE_NAME`
    - How this application/service will be identified in Streamdal Console (Example: `billing-svc`)

By default, the library will not have Streamdal instrumentation enabled; to enable it,
you will need to set `enable_streamdal=True` in the pika connection params:

```python
pika.ConnectionParameters(enable_streamdal=True)
```

<sub>For more in-depth explanation of the changes and available settings, see [What's changed?](#whats-changed).</sub>

## Example

A fully working example is provided in [examples/streamdal/app.py](examples/streamdal/consumer.py).

To run the example:

1. Change directory to `examples/go-kafkacat-streamdal`
1. Start a local rabbitmq instance: `docker-compose up -d`
1. Install & start Streamdal: `curl -sSL https://sh.streamdal.com | sh`
1. Open a browser to verify you can see the streamdal UI at: `http://localhost:8080`
    - _It should look like this:_ ![streamdal-console-1](./assets/streamdal-console-1.png)
1. Launch a consumer:
    ```
    STREAMDAL_ADDRESS=localhost:8082 \
    STREAMDAL_AUTH_TOKEN=1234 \
    STREAMDAL_SERVICE_NAME=kafkacat \
    go run go-kafkacat-streamdal.go --broker localhost:9092 consume --group testgroup test
    ```
1. In another terminal, launch a producer:
    ```
    STREAMDAL_ADDRESS=localhost:8082 \
    STREAMDAL_AUTH_TOKEN=1234 \
    STREAMDAL_SERVICE_NAME=kafkacat \
    go run go-kafkacat-streamdal.go produce --broker localhost:9092 --topic test --key-delim=":"
    ```
1. In the `producer` terminal, produce some data by pasting: `testKey:{"email":"foo@bar.com"}`
1. In the `consumer` terminal, you should see: `{"email":"foo@bar.com"}`
1. Open the Streamdal Console in a browser [https://localhost:8080](https://localhost:8080)
    - _It should look like this:_ ![streamdal-console-2](./assets/streamdal-console-2.png)
1. Create a pipeline that detects and masks PII fields & attach it to the consumer
    - ![streamdal-console-3](./assets/streamdal-console-3.gif)
1. Produce a message in producer terminal: `testKey:{"email":"foo@bar.com"}`
1. You should see a masked message in the consumer terminal: `{"email":"fo*********"}`
    - _**Tip**: If you detach the pipeline from the consumer and paste the same message again, you
      will see the original, unmasked message._

## Passing "runtime" settings to the shim

By default, the shim will set the `ComponentName` to "kafka" and the `OperationName`
to the name of the topic you are producing to or consuming from.

Also, by default, if the shim runs into any errors executing `streamdal.Process()`,
it will swallow the errors and return the original value.

When producing, you can set `StreamdalRuntimeConfig` in the `ProducerMessage`:

```go
p, _ := kafka.NewAsyncProducer(brokers, config)

msg := &ProducerMessage{
    Topic: "test",
    Value: []byte("hello, world"),
    StreamdalRuntimeConfig: &StreamdalRuntimeConfig{
        ComponentName: "custom-component-name",
        OperationName: "custom-operation-name",
    },
}

p.Input() <- msg

// This will cause the producer to show up in Streamdal Console with the
// OperationName "custom-operation-name" and it will show as connected to
// "custom-component-name" (instead of the default "kafka").
```

**Passing `StreamdalRuntimeConfig` in the consumer is not implemented yet!**

## What's changed?

The goal of any shim is to make minimally invasive changes so that the original
library remains backwards-compatible and does not present any "surprises" at
runtime.

<sub>NOTE: `IBM/sarama` is significantly more complex than other Go Kafka libraries,
due to this, integration is a bit more invasive than other shims.</sub>

The following changes have been made to the original library:

1. Added `EnableStreamdal` bool to the main `Config` struct
    - This is how you enable the Streamdal instrumentation in the library.
1. Added Streamdal setup in `newAsyncProducer()` and `newConsumer()`
    - `newAsyncProducer()` is used for both `NewSyncProducer()` and `NewAsyncProducer()`
1. Updated `async_producer.go:dispatcher()` to call on Streamdal's `.Process()
    - This function is called for every message produced to Kafka via the `Input()` channel
1. Updated `consumer.go:responseFeeder()` to call on Streamdal's `.Process()
    - This function feeds messages to `Consume()`
1. A new file [./streamdal.go](./streamdal.go) has been added to the library that
   contains helper funcs, structs and vars used for simplifying Streamdal
   instrumentation in the core library.
