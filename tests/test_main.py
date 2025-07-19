from crypto_converter.main import main


def test_main() -> None:
    assert main() == "Hello!"
