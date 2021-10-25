# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient
import json

img_path = r"test.jpg"

def store_blob(blob_info, file_name):
    try:
        sas_url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )

        print("\nUploading file: {} to Azure Storage as blob: {} in container {}\n".format(file_name, blob_info["blobName"], blob_info["containerName"]))

        # Upload the specified file
        with BlobClient.from_blob_url(sas_url) as blob_client:
            with open(file_name, "rb") as f:
                result = blob_client.upload_blob(f, overwrite=True)
                return (True, result)

    except FileNotFoundError as ex:
        # catch file not found and add an HTTP status code to return in notification to IoT Hub
        ex.status_code = 404
        return (False, ex)

    except AzureError as ex:
        # catch Azure errors that might result from the upload operation
        return (False, ex)

async def main():
    # Fetch the connection string from an enviornment variable
    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")

    # Create instance of the device client using the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # Connect the device client.
    await device_client.connect()

    #Upload blob
    blob_name = os.path.basename(img_path)
    storage_info = await device_client.get_storage_info_for_blob(blob_name)

    success, result = store_blob(storage_info, img_path)

    #Create a message
    telemetry = {'desc' : 'Upload test image from Raspberry Pi to Blob Storage',
                 'success' : success,
                 'blob' : storage_info['blobName']}

    msg = Message(json.dumps(telemetry))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"

    # Send a single message
    print("Sending message...")
    await device_client.send_message(msg)
    print("Message successfully sent!")

    # Finally, shut down the client
    await device_client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

    # If using Python 3.6 or below, use the following code instead of asyncio.run(main()):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()
