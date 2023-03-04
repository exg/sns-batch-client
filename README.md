# SNS Batch Client

SNSBatchClient is a class that provides an async interface to publish
multiple messages to an SNS topic by delegating to the `publish_batch`
method of [Boto3 SNS
Client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html).


## Usage

First, create an SNS Batch Client:
```python
import boto3
from sns_batch_client import SNSBatchClient
client = boto3.client("sns")
batch_client = SNSBatchClient(client=client, max_attempts=4)
```

Then create and publish some messages:
```python
import asyncio

entries = [
    {
        "Id": "1",
        "Message": "message1",
        "MessageAttributes": {
            "type": {
                "DataType": "String",
                "StringValue": "type1",
            }
        },
    },
    {
        "Id": "2",
        "Message": "message2",
        "MessageAttributes": {
            "type": {
                "DataType": "String",
                "StringValue": "type2",
            }
        },
    },
]

loop = asyncio.get_event_loop()
coro = await batch_client.publish_messages("topic", entries)
response = loop.run_until_complete(coro)
```
`publish_messages` returns the successful and failed responses in the same
format as that returned by the `publish_batch` method of Boto3 SNS
client.
