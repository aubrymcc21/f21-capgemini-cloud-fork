# import statements
import os
import json
import asyncio
from time import sleep
import datetime

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient

from smbus2 import SMBus
from mlx90614 import MLX90614
import picamera

# Global variables
device_id = "simDevice"

def iothub_initialize():
    # Fetch the connection string from an enviornment variable
    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")

    # Create instance of the device client using the connection string
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # Connect the device client.
    await device_client.connect()

    return device_client

def format_url(blob_info):
    url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )
    return url

def store_blob(sas_url, file_name):
    try:
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
    #Setup camera
    camera = picamera.PiCamera()
    camera.start_preview()

    sleep(2)

    #Setup temperature sensor
    bus = SMBus(1)
    sensor = MLX90614(bus, address=0x5A)

    #Connect to IoT Hub
    iot_device = iothub_initialize()

    # Loop
    while (1):
        # Get employee ID input
        employee_id = input()

        timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        entry_id = device_id + "_" + timestamp

        # Take picture
        img_name = entry_id + ".jpg"
        camera.capture(img_name)
        
        # Get temperature
        obj_temp = sensor.get_object_1()
        amb_temp = sensor.get_ambient()

        # Upload image as blob
        storage_info = await device_client.get_storage_info_for_blob(img_name)
        url = format_url(storage_info)
        success, result = store_blob(url, img_name)

        # Create IoT Hub message
        telemetry = {
                 'obj_temp' : obj_temp,
                 'amb_temp' : amb_temp,
                 'img_success' : success,
                 'blob_url' : url
                }

        msg = Message(json.dumps(telemetry))
        msg.content_encoding = "utf-8"
        msg.content_type = "application/json"

        # Send IoT Hub telemetry
        await device_client.send_message(msg)


# Main
if __name__ == "__main__":
    asyncio.run(main())