import os

import boto3
import moto
import pytest

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"


@pytest.fixture(scope="session", autouse=True)
def aws_mock():
    with (
        moto.mock_sns(),
        moto.mock_sqs(),
    ):
        yield


@pytest.fixture(name="topic")
def topic_fixture():
    sns = boto3.resource("sns")
    topic = sns.create_topic(Name="test-topic")
    yield topic
    topic.delete()


@pytest.fixture(name="queue")
def queue_fixture(topic):
    sqs = boto3.resource("sqs")
    queue = sqs.create_queue(QueueName="test-queue")
    topic.subscribe(Protocol="sqs", Endpoint=queue.attributes["QueueArn"])
    yield queue
    queue.delete()
