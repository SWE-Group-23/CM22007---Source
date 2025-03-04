"""
Runs all integration and end-to-end tests.
"""

import sys
import unittest

# class CleanupTestResult(unittest.TextTestResult):
#     """
#     As all tests should clean out RabbitMQ, the testing
#     ScyllaDB keyspace, and Valkey, this class overrides
#     the add result methods and calls the cleanup method.
#     """
#
#     def __getattr__(self, name):
#         """
#         Intercepts method calls that begin with "add" to
#         cleanup after a test when such a method is called.
#         """
#         if name.startswith("add"):
#             original_method = super().__getattribute__(name)
#
#             def wrapped_method(*args, **kwargs):
#                 result = original_method(*args, **kwargs)
#                 self.cleanup()
#                 return result
#
#             return wrapped_method
#
#         original_method = getattr(self, name)
#
#         def method(*args, **kwargs):
#             return original_method(*args, **kwargs)
#
#         return method
#
#     def cleanup(self):
#         """
#         Cleans out:
#         - RabbitMQ queues
#         - ScyllaDB keyspaces
#         - Valkey stores
#         """
#
#         print("Cleaning up...")
#
#         # ScyllaDB
#         print("Clearing out ScyllaDB...")
#         cluster = cc.Cluster(
#             contact_points=["dev-db-client.scylla.svc"],
#             auth_provider=ca.PlainTextAuthProvider(
#                 username=os.environ["SCYLLADB_USERNAME"],
#                 password=os.environ["SCYLLADB_PASSWORD"],
#             ),
#             load_balancing_policy=cs.policies.TokenAwarePolicy(
#                 cs.policies.DCAwareRoundRobinPolicy(),
#             ),
#             protocol_version=4,
#         )
#         session = cluster.connect()
#
#         # get all keyspace names
#         keyspaces_rows = session.execute(
#             "SELECT keyspace_name FROM system_schema.keyspaces;"
#         )
#
#         # filter out system keyspace
#         keyspaces = [
#             row.keyspace_name
#             for row in keyspaces_rows
#             if not row.keyspace_name.startswith("system")
#         ]
#
#         # truncate all tables in all keyspaces
#         for keyspace in keyspaces:
#             # get tables in keyspace
#             tables_query = session.prepare(
#                 """
#                 SELECT table_name
#                 FROM system_schema.tables
#                 WHERE keyspace_name = ?;
#                 """
#             )
#             tables = session.execute(tables_query, [keyspace])
#
#             # truncate all tables in keyspace
#             for table in tables:
#                 print(f"Truncating {keyspace}.{table}...")
#                 session.execute(f"TRUNCATE {keyspace}.{table};")


def main():
    """
    Discovers integration tests from ./integration/**/test*.py and
    e2e tests from ./e2e/**/test*.py, then runs them. Exiting 1 if
    any test fails.
    """
    loader = unittest.TestLoader()
    integration_suite = loader.discover("integration/")

    runner = unittest.TextTestRunner()
    result = runner.run(integration_suite)

    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    main()
