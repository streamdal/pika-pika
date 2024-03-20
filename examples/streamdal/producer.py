import pika_streamdal as pika
import time
import signal

from pika.streamdal import *


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

    try:
        # Declare exchange if it does not exist
        channel.exchange_declare(exchange='events', exchange_type='topic')
    except Exception:
        pass

    # Clean shutdown
    def sigterm_handler(signum, frame):
        connection.close()
        time.sleep(1)
        exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    while True:
        print("Publishing message")
        # Publish our example payload
        channel.basic_publish(
            exchange='events',
            routing_key='orders.new',
            body=b'{"key": "value"}',
            streamdal_cfg=cfg_produce)

        time.sleep(5)


if __name__ == '__main__':
    main()
