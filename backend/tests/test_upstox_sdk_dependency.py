import importlib.util


def test_upstox_sdk_dependency_is_declared():
    requirements = open("requirements.txt", encoding="utf-8").read().splitlines()
    assert any(line.strip().lower().startswith("upstox-python-sdk") for line in requirements)


def test_upstox_generated_feed_module_is_importable_when_sdk_is_installed():
    module_name = "upstox_client.feeder.market_data_feed_v3_pb2"
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        # CI environments that have not installed requirements should fail clearly
        # rather than treating the adapter as production-ready.
        raise AssertionError(f"Missing official Upstox protobuf module: {module_name}")
