import time
import asyncio
import json
from config import logger, az
from llm import SingleFileScanUpload, SingleFileUpload


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        logger.info("Starting ACI Container")
        az.configure_clients()
        scan_upload = SingleFileScanUpload()
        upload = SingleFileUpload()
        logger.info(f"Starting Task Worker. Queue: {az.STORAGE_QUEUE}")
        while True:
            try:
                message = [_ for _ in az.queue.receive_messages(max_messages=1)][0]
                logger.info(f"Received message: {message}")
                body = json.loads(message["content"])
                if body["v-scan"]:
                    result = loop.run_until_complete(scan_upload.run(body["filename"]))
                else:
                    result = loop.run_until_complete(upload.run(body["filename"]))
                logger.info(f"Result: {result}")
                response = az.queue.delete_message(message)

            except IndexError:
                logger.info("No messages in queue")
                time.sleep(10)
    except Exception as ex:
        logger.exception(ex)
        time.sleep(30)
        raise ex
