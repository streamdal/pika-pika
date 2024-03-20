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

1. Change directory to `examples/streamdal`
1. Start a local rabbitmq instance: `docker-compose up -d rabbitmq`
1. Install & start Streamdal: `curl -sSL https://sh.streamdal.com | sh`
1. Open a browser to verify you can see the streamdal UI at: `http://localhost:8080`
   - _It should look like this:_ ![streamdal-console-1](./assets/streamdal-console-1.png)
1. Launch a consumer:
    ```
    STREAMDAL_ADDRESS=localhost:8082 \
    STREAMDAL_TOKEN=1234 \
    STREAMDAL_SERVICE_NAME=demo \
    python consumer.py
    ```
1. In another terminal, launch a producer:
    ```
    STREAMDAL_ADDRESS=localhost:8082 \
    STREAMDAL_TOKEN=1234 \
    STREAMDAL_SERVICE_NAME=demo \
    python producer.py
    ```
1. Open the Streamdal Console in a browser [https://localhost:8080](https://localhost:8080)
   - _It should look like this:_ ![streamdal-console-2](./assets/streamdal-console-2.png)
1. Create a pipeline that detects and masks PII fields & attach it to the consumer
   - ![streamdal-console-3](./assets/streamdal-console-3.gif)
1. Produce a message in producer terminal: `testKey:{"email":"foo@bar.com"}`
1. You should see a masked message in the consumer terminal: `{"email":"fo*********"}`
   - _**Tip**: If you detach the pipeline from the consumer and paste the same message again, you
     will see the original, unmasked message._

## Passing "runtime" settings to the shim

By default, the shim will set the `component_name` to `rabbitmq` and the `operation_name`
to the name of the routing key you are producing to, or the string `f"{queue}_{binding_key}"` being consumed from

Also, by default, if the shim runs into any errors executing `.process()`,
it will swallow the errors and return the original value.

When producing, you can set `streamdal_cfg` in the `basic_publish()`:

```python
cfg_produce = StreamdalRuntimeConfig(
   audience=Audience(
      component_name="rabbitmq",
      operation_name="produce_msg",
      operation_type=OPERATION_TYPE_PRODUCER
   )
)

channel.basic_publish(
   exchange='',
   routing_key='test',
   body='Hello World!',
   streamdal_cfg=cfg_produce
)
```

When consuming, you can set `streamdal_cfg` in the `consume()` call:

```python
cfg_consume = StreamdalRuntimeConfig(
   audience=Audience(
      component_name="rabbitmq",
      operation_name="consume_msg",
      operation_type=OPERATION_TYPE_CONSUMER
   )
)

for method_frame, properties, body in channel.consume(queue='test', streamdal_cfg=cfg_consume):
    #...
```

## What's changed?

The goal of any shim is to make minimally invasive changes so that the original
library remains backwards-compatible and does not present any "surprises" at
runtime.

TODO
