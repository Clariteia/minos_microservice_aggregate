import unittest
from abc import (
    ABC,
)
from collections.abc import (
    AsyncIterator,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
    call,
)
from uuid import (
    uuid4,
)

from minos.aggregate import (
    TRANSACTION_CONTEXT_VAR,
    Aggregate,
    Condition,
    Ordering,
    SnapshotRepository,
    TransactionEntry,
)
from minos.common import (
    MinosSetup,
)
from tests.utils import (
    FakeAsyncIterator,
)


class _SnapshotRepository(SnapshotRepository):
    """For testing purposes."""

    async def _get(self, *args, **kwargs) -> Aggregate:
        """For testing purposes."""

    def _find(self, *args, **kwargs) -> AsyncIterator[Aggregate]:
        """For testing purposes."""

    async def _synchronize(self, **kwargs) -> None:
        """For testing purposes."""


class TestSnapshotRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.snapshot_repository = _SnapshotRepository()

        self.synchronize_mock = AsyncMock()
        self.get_mock = AsyncMock(return_value=1)
        self.find_mock = MagicMock(return_value=FakeAsyncIterator(range(5)))

        self.snapshot_repository._get = self.get_mock
        self.snapshot_repository._find = self.find_mock
        self.snapshot_repository._synchronize = self.synchronize_mock

    def test_subclass(self):
        self.assertTrue(issubclass(SnapshotRepository, (ABC, MinosSetup)))

    def test_abstract(self):
        # noinspection PyUnresolvedReferences
        self.assertEqual({"_get", "_find", "_synchronize"}, SnapshotRepository.__abstractmethods__)

    async def test_get(self):
        transaction = TransactionEntry()
        uuid = uuid4()
        observed = await self.snapshot_repository.get("path.to.Aggregate", uuid, transaction)
        self.assertEqual(1, observed)

        self.assertEqual(1, self.synchronize_mock.call_count)
        self.assertEqual(call(), self.synchronize_mock.call_args)

        self.assertEqual(1, self.get_mock.call_count)
        args = call(aggregate_name="path.to.Aggregate", uuid=uuid, transaction=transaction)
        self.assertEqual(args, self.get_mock.call_args)

    async def test_get_transaction_null(self):
        await self.snapshot_repository.get("path.to.Aggregate", uuid4())

        self.assertEqual(1, self.get_mock.call_count)
        self.assertEqual(None, self.get_mock.call_args.kwargs["transaction"])

    async def test_get_transaction_context(self):
        transaction = TransactionEntry()
        TRANSACTION_CONTEXT_VAR.set(transaction)
        await self.snapshot_repository.get("path.to.Aggregate", uuid4())

        self.assertEqual(1, self.get_mock.call_count)
        self.assertEqual(transaction, self.get_mock.call_args.kwargs["transaction"])

    async def test_find(self):
        transaction = TransactionEntry()
        iterable = self.snapshot_repository.find(
            "path.to.Aggregate", Condition.TRUE, Ordering.ASC("name"), 10, True, transaction
        )
        observed = [a async for a in iterable]
        self.assertEqual(list(range(5)), observed)

        self.assertEqual(1, self.synchronize_mock.call_count)
        self.assertEqual(call(), self.synchronize_mock.call_args)

        self.assertEqual(1, self.find_mock.call_count)
        args = call(
            aggregate_name="path.to.Aggregate",
            condition=Condition.TRUE,
            ordering=Ordering.ASC("name"),
            limit=10,
            streaming_mode=True,
            transaction=transaction,
        )
        self.assertEqual(args, self.find_mock.call_args)

    async def test_find_transaction_null(self):
        [a async for a in self.snapshot_repository.find("path.to.Aggregate", Condition.TRUE)]

        self.assertEqual(1, self.find_mock.call_count)
        self.assertEqual(None, self.find_mock.call_args.kwargs["transaction"])

    async def test_find_transaction_context(self):
        transaction = TransactionEntry()
        TRANSACTION_CONTEXT_VAR.set(transaction)
        [a async for a in self.snapshot_repository.find("path.to.Aggregate", Condition.TRUE)]

        self.assertEqual(1, self.find_mock.call_count)
        self.assertEqual(transaction, self.find_mock.call_args.kwargs["transaction"])

    async def test_synchronize(self):
        await self.snapshot_repository.synchronize()

        self.assertEqual(1, self.synchronize_mock.call_count)
        self.assertEqual(call(), self.synchronize_mock.call_args)


if __name__ == "__main__":
    unittest.main()
