import pika_streamdal as pika
import time
import signal

from pika.streamdal import *

# Consumer Audience
cfg_consume = StreamdalRuntimeConfig(
    audience=Audience(
        component_name="rabbitmq",
        operation_name="consume_msg",
        operation_type=OPERATION_TYPE_CONSUMER
    )
)

# Producer Audience
cfg_produce = StreamdalRuntimeConfig(
    audience=Audience(
        component_name="rabbitmq",
        operation_name="produce_msg",
        operation_type=OPERATION_TYPE_PRODUCER
    )
)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(enable_streamdal=True))
    channel = connection.channel()

    # Declare exchange if it does not exist
    channel.exchange_declare(exchange='events', exchange_type='topic')

    # Declare queue if it does not exist
    channel.queue_declare(queue='streamdal')

    # Bind queue to exchange
    channel.queue_bind(exchange='events', queue='streamdal', routing_key='orders.new')

    # Clean shutdown
    def sigterm_handler(signum, frame):
        connection.close()
        time.sleep(1)
        exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    # Consume the message
    for method_frame, properties, body in channel.consume(queue='test', streamdal_cfg=cfg_consume):
        print(method_frame, properties, body)
        channel.basic_ack(method_frame.delivery_tag)
        time.sleep(1)


if __name__ == '__main__':
    main()
