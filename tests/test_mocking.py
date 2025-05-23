from unittest.mock import patch

import pytest
from bson import ObjectId
from pymongo import ReadPreference
from pymongo.results import UpdateResult

from mongomock_motor import AsyncMongoMockClient
from mongomock_motor.patches import _patch_iter_documents_and_get_dataset


@pytest.mark.anyio
async def sample_function(collection):
    result = await collection.update_one(
        filter={'_id': ObjectId()},
        update={'$set': {'field': 'value'}},
        upsert=True,
    )

    if result.acknowledged is False:
        raise RuntimeError()


def async_wrapper(value):
    async def wrapper(*args, **kwargs):
        return value

    return wrapper


@pytest.mark.anyio
async def test_patch():
    collection = AsyncMongoMockClient()['test']['test']

    with patch(
        'mongomock_motor.AsyncMongoMockCollection.update_one',
        new=async_wrapper(UpdateResult({}, False)),
    ):
        with pytest.raises(RuntimeError):
            await sample_function(collection)


@pytest.mark.anyio
async def test_patch_object():
    collection = AsyncMongoMockClient()['test']['test']

    with patch.object(
        collection, 'update_one', new=async_wrapper(UpdateResult({}, False))
    ):
        with pytest.raises(RuntimeError):
            await sample_function(collection)


@pytest.mark.anyio
async def test_no_multiple_patching():
    database = AsyncMongoMockClient()['test']

    with patch(
        'mongomock_motor.patches._patch_iter_documents_and_get_dataset',
        wraps=_patch_iter_documents_and_get_dataset,
    ) as patch_iter_documents:
        for _ in range(2):
            collection = database['test']
            assert collection

        assert patch_iter_documents.call_count == 1

        for _ in range(2):
            # passing non default options force mongomock to create a new collection
            collection = database.get_collection(
                'test',
                read_preference=ReadPreference.PRIMARY_PREFERRED,
            )
            assert collection

        assert patch_iter_documents.call_count == 3

        for _ in range(2):
            collection = database.get_collection('test')
            assert collection

        assert patch_iter_documents.call_count == 3
