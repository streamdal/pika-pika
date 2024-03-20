# This file contains code for shimming this library with the Streamdal python SDK
import logging
import os
import threading
from dataclasses import dataclass
from streamdal import (Audience, StreamdalConfig, StreamdalClient, ProcessRequest,
                       EXEC_STATUS_ERROR, OPERATION_TYPE_PRODUCER, OPERATION_TYPE_CONSUMER)

__all__ = ("StreamdalRuntimeConfig", "Audience", "streamdal_setup",
           "streamdal_process", "OPERATION_TYPE_PRODUCER", "OPERATION_TYPE_CONSUMER")

STREAMDAL_ENV_ADDRESS = "STREAMDAL_ADDRESS"
STREAMDAL_ENV_AUTH_TOKEN = "STREAMDAL_AUTH_TOKEN"
STREAMDAL_ENV_SERVICE_NAME = "STREAMDAL_SERVICE_NAME"

STREAMDAL_DEFAULT_COMPONENT_NAME = "rabbitmq"
STREAMDAL_DEFAULT_OPERATION_NAME = "consume"

LOGGER = logging.getLogger(__name__)


@dataclass
class StreamdalRuntimeConfig:
    audience: Audience
    strict_errors: bool = False


def streamdal_setup():
    address = os.getenv("STREAMDAL_ADDRESS")
    if address is None:
        raise ValueError(f"Missing required environment variable STREAMDAL_ADDRESS")

    auth_token = os.getenv("STREAMDAL_TOKEN")
    if auth_token is None:
        raise ValueError(f"Missing required environment variable STREAMDAL_TOKEN")

    service_name = os.getenv("STREAMDAL_SERVICE_NAME")
    if service_name is None:
        raise ValueError(f"Missing required environment variable STREAMDAL_SERVICE_NAME")

    return StreamdalClient(
        StreamdalConfig(
            streamdal_url=address,
            streamdal_token=auth_token,
            service_name=service_name,
            exit=threading.Event(),
        )
    )


def streamdal_process(streamdal_client: StreamdalClient, operation_type: int, exchange_name: str, routing_key: str,
                      msg: bytes, cfg: StreamdalRuntimeConfig) -> bytes:
    if streamdal_client is None:
        return msg

    aud = streamdal_generate_audience(operation_type, exchange_name, routing_key, cfg)

    resp = streamdal_client.process(
        ProcessRequest(
            component_name=aud.component_name,
            operation_name=aud.operation_name,
            operation_type=aud.operation_type,
            data=msg,
        )
    )

    if resp.status == EXEC_STATUS_ERROR:
        # Check if we have an optional custom config passed to basic_publish()
        if isinstance(cfg, StreamdalRuntimeConfig) and cfg.strict_errors:
            # Strict errors specified, raise an exception
            raise Exception(f"Streamdal encountered an error processing a message: {resp.message}")
        else:
            # Strict errors not enabled or passed, just log and return original message
            LOGGER.error(f"Streamdal encountered an error processing a message: {resp.message}")
            # Return original message
            return msg

    # Return the processed message, may or may not be modified
    return resp.data


def streamdal_generate_audience(operation_type: int, exchange_name: str, routing_key: str,
                                cfg: StreamdalRuntimeConfig) -> Audience:
    component_name = STREAMDAL_DEFAULT_COMPONENT_NAME
    operation_name = STREAMDAL_DEFAULT_OPERATION_NAME

    if exchange_name != "":
        operation_name = exchange_name

    if routing_key != "":
        routing_key = routing_key.replace(".", "_")
        operation_name = f"{operation_name}_{routing_key}"

    if cfg is not None:
        component_name = cfg.audience.component_name
        operation_name = cfg.audience.operation_name

    return Audience(
        operation_type=operation_type,
        operation_name=operation_name,
        component_name=component_name,
    )
