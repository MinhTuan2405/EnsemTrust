
from dagster import asset, Definitions

@asset
def my_simple_asset():
  """
  Một asset Dagster đơn giản chỉ in ra thông báo.
  A simple Dagster asset that just prints a message.
  """
  print("Hello from my_simple_asset!")
  return "Asset executed successfully!"


defs = Definitions(
    assets=[my_simple_asset],
)
