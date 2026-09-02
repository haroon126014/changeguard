from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded, tx_execution_failed

CONTRACT = "ChangeGuard"


def deploy():
    factory = get_contract_factory(CONTRACT)
    return factory.deploy()


def test_initial_state():
    contract = deploy()

    assert contract.get_title().call() == ""
    assert contract.get_old_url().call() == ""
    assert contract.get_new_url().call() == ""
    assert contract.get_verdict().call() == "NOT_EVALUATED"
    assert contract.get_change_type().call() == ""
    assert contract.get_changed_sections().call() == ""
    assert contract.get_impact().call() == ""
    assert contract.get_reasoning().call() == ""
    assert contract.is_evaluated().call() is False


def test_create_comparison():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "Terms update",
            "https://example.com/old",
            "https://example.com/new",
        ]
    ).transact()

    assert tx_execution_succeeded(tx)
    assert contract.get_title().call() == "Terms update"
    assert contract.get_old_url().call() == "https://example.com/old"
    assert contract.get_new_url().call() == "https://example.com/new"


def test_empty_title_rejected():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "",
            "https://example.com/old",
            "https://example.com/new",
        ]
    ).transact()

    assert tx_execution_failed(tx)


def test_empty_old_url_rejected():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "Terms update",
            "",
            "https://example.com/new",
        ]
    ).transact()

    assert tx_execution_failed(tx)


def test_empty_new_url_rejected():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "Terms update",
            "https://example.com/old",
            "",
        ]
    ).transact()

    assert tx_execution_failed(tx)


def test_same_urls_rejected():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "Terms update",
            "https://example.com/version",
            "https://example.com/version",
        ]
    ).transact()

    assert tx_execution_failed(tx)


def test_invalid_old_url_rejected():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "Terms update",
            "example.com/old",
            "https://example.com/new",
        ]
    ).transact()

    assert tx_execution_failed(tx)


def test_invalid_new_url_rejected():
    contract = deploy()

    tx = contract.create_comparison(
        args=[
            "Terms update",
            "https://example.com/old",
            "example.com/new",
        ]
    ).transact()

    assert tx_execution_failed(tx)


def test_duplicate_comparison_rejected():
    contract = deploy()

    first = contract.create_comparison(
        args=[
            "Terms update",
            "https://example.com/old",
            "https://example.com/new",
        ]
    ).transact()

    assert tx_execution_succeeded(first)

    second = contract.create_comparison(
        args=[
            "Another comparison",
            "https://example.com/v1",
            "https://example.com/v2",
        ]
    ).transact()

    assert tx_execution_failed(second)


def test_evaluate_without_comparison_rejected():
    contract = deploy()

    tx = contract.evaluate().transact()

    assert tx_execution_failed(tx)
