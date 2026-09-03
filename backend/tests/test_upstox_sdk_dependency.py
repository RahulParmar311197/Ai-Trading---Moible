import importlib.util
from pathlib import Path


def test_upstox_sdk_dependency_is_declared():
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    requirements = requirements_path.read_text(encoding="utf-8").splitlines()
    assert any(line.strip().lower().startswith("upstox-python-sdk") for line in requirements)


def test_upstox_generated_feed_module_is_importable_when_sdk_is_installed():
    module_name = "upstox_client.feeder.proto.MarketDataFeedV3_pb2"
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise AssertionError(f"Missing official Upstox protobuf module: {module_name}")
