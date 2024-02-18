import base64
import itertools
import json
import uuid
from unittest.mock import Mock

import boto3

from sns_batch_client import SNSBatchClient


def get_attribute_value(attribute):
    if attribute["DataType"] == "String":
        return attribute["StringValue"]
    return base64.b64encode(attribute["BinaryValue"]).decode()


def transform_attributes(attributes):
    return {
        k: {
            "Type": v["DataType"],
            "Value": get_attribute_value(v),
        }
        for k, v in attributes.items()
    }


async def test_publish(topic, queue):
    client = boto3.client("sns")
    batch_client = SNSBatchClient(client=client, max_attempts=4)
    invalid_entries = [
        {
            "Id": str(uuid.uuid4()),
            "Message": "message",
            "MessageGroupId": "",
        }
        for i in range(20)
    ]
    entries = [
        {
            "Id": str(uuid.uuid4()),
            "Message": f"message{i}",
            "MessageAttributes": {
                "attr1": {
                    "DataType": "String",
                    "StringValue": f"value{i}",
                },
                "attr2": {
                    "DataType": "Binary",
                    "BinaryValue": f"value{i}".encode(),
                },
            },
        }
        for i in range(20)
    ]

    response = await batch_client.publish_messages(topic.arn, itertools.chain(*zip(invalid_entries, entries)))
    assert len(response["Successful"]) == len(entries)
    assert len(response["Failed"]) == len(invalid_entries)

    messages = []
    while True:
        response = queue.receive_messages(MaxNumberOfMessages=10)
        if not response:
            break
        messages.extend(json.loads(message.body) for message in response)

    assert len(messages) == len(entries)
    for sent, received in zip(entries, messages):
        assert sent["Message"] == received["Message"]
        assert transform_attributes(sent["MessageAttributes"]) == received["MessageAttributes"]


class PublishBatchMock:
    def __init__(self, error_count):
        self.error_count = error_count
        self.calls = 0

    # pylint: disable-next=invalid-name,unused-argument
    def publish_batch(self, TopicArn, PublishBatchRequestEntries):
        self.calls += 1
        if self.calls < self.error_count:
            successful = PublishBatchRequestEntries[::2]
            failed = PublishBatchRequestEntries[1::2]
        else:
            successful = PublishBatchRequestEntries
            failed = []
        return {
            "Successful": [
                {
                    "Id": entry["Id"],
                }
                for entry in successful
            ],
            "Failed": [
                {
                    "Id": entry["Id"],
                    "SenderFault": False,
                }
                for entry in failed
            ],
        }


async def test_publish_should_retry_on_retryable_errors():
    max_attempts = 4
    client = Mock(publish_batch=Mock())
    client.publish_batch.side_effect = PublishBatchMock(max_attempts).publish_batch
    batch_client = SNSBatchClient(client=client, max_attempts=max_attempts)
    entries = [
        {
            "Id": str(uuid.uuid4()),
            "Message": f"message{i}",
        }
        for i in range(20)
    ]

    response = await batch_client.publish_messages("test", entries)
    assert len(response["Successful"]) == len(entries)
    assert len(response["Failed"]) == 0
