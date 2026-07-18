"""Root pytest fixtures shared by every test.

The session-scoped :func:`django_db_setup` override here is the single
mechanism that makes RLS-compatible test setup work. Migrations install
the strict ``tenant_id = current_setting('app.tenant_id')`` policy on
every tenant-scoped table; with the ``wa`` role running non-superuser,
any INSERT into a tenant-scoped table fails unless ``app.tenant_id`` is
set on the connection. Rather than forcing every test to set the GUC
invasively, we disable RLS for the whole test session and let the 2
RLS-specific tests re-enable it locally between their data setup and
their assertions.
"""

from collections.abc import Generator

import pytest
from pytest_django.plugin import DjangoDbBlocker

from tenants.rls import TENANT_SCOPED_TABLES, disable_rls_on


@pytest.fixture(scope="session")
def django_db_setup(
    request: pytest.FixtureRequest,
    django_test_environment: None,
    django_db_blocker: DjangoDbBlocker,
) -> Generator[None, None, None]:
    """Override pytest-django's session setup to disable RLS after migrations.

    Mirrors the default ``django_db_setup`` in pytest-django, then runs
    ``ALTER TABLE ... DISABLE ROW LEVEL SECURITY`` for every
    tenant-scoped table. The 2 RLS-specific tests re-enable RLS via
    :func:`tenants.rls.enable_rls_on` between their data setup and
    their assertions, so the policy itself is still exercised.
    """
    from django.test.utils import setup_databases, teardown_databases

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
        )
        for table in TENANT_SCOPED_TABLES:
            disable_rls_on(table)

    yield

    with django_db_blocker.unblock():
        try:
            teardown_databases(db_cfg, verbosity=request.config.option.verbose)
        except Exception as exc:  # noqa: BLE001
            request.node.warn(
                pytest.PytestWarning(
                    f"Error when trying to teardown test databases: {exc!r}"
                )
            )
