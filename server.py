# This is the server file.

import argparse
import asyncio
import logging

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived
from aioquic.quic.logger import QuicFileLogger

class ServerProtocol(QuicConnectionProtocol):
    def quic_event_received(self, event: QuicEvent):
        if isinstance(event, StreamDataReceived):
            # print received data
            print(event.data.decode())

            # serialize response
            query5 = "Here is the data you requested"
            response = bytes(query5, "utf-8")

            # send response
            self._quic.send_stream_data(event.stream_id, response, end_stream=True)


async def main(
    host: str,
    port: int,
    configuration: QuicConfiguration,
    retry: bool,
) -> None:
    await serve(
        host,
        port,
        configuration=configuration,
        create_protocol=ServerProtocol,
        retry=retry,
    )
    await asyncio.Future()


if __name__ == "__main__":
    # Arguments for running program - description in "help" tag
    parser = argparse.ArgumentParser(description="DNS over QUIC server")
    parser.add_argument(
        "--host",
        type=str,
        default="::",
        help="listen on the specified address (defaults to ::)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=853,
        help="listen on the specified port (defaults to 853)",
    )
    parser.add_argument(
        "-k",
        "--private-key",
        type=str,
        help="load the TLS private key from the specified file",
    )
    parser.add_argument(
        "-c",
        "--certificate",
        type=str,
        required=True,
        help="load the TLS certificate from the specified file",
    )
    parser.add_argument(
        "--retry",
        action="store_true",
        help="send a retry for new connections",
    )
    parser.add_argument(
        "-q",
        "--quic-log",
        type=str,
        help="log QUIC events to QLOG files in the specified directory",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase logging verbosity"
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    # create QUIC logger
    if args.quic_log:
        quic_logger = QuicFileLogger(args.quic_log)
    else:
        quic_logger = None

    # Configure QUIC
    configuration = QuicConfiguration(
        alpn_protocols=["doq"],
        is_client=False,
        quic_logger=quic_logger,
    )

    configuration.load_cert_chain(args.certificate, args.private_key)

    try:
        asyncio.run(
            main(
                host=args.host,
                port=args.port,
                configuration=configuration,
                retry=args.retry,
            )
        )
    except KeyboardInterrupt:
        pass