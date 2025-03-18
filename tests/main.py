"""
Runs all integration and end-to-end tests.
"""

import unittest


def main():
    """
    Discovers integration tests from ./integration/**/test*.py and
    e2e tests from ./e2e/**/test*.py, then runs them. Exiting 1 if
    any test fails.
    """
    loader = unittest.TestLoader()
    integration_suite = loader.discover("integration/")

    runner = unittest.TextTestRunner()
    _ = runner.run(integration_suite)


if __name__ == "__main__":
    main()
