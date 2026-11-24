"""The numbers of the strategy screen, computed by the service and never taken from a model."""

from chat_bridge.strategy.schemas import DiffRow, TargetRow


def target_rows(symbols: list[str], current: dict[str, int]) -> list[TargetRow]:
    """The current target of each holding, in the profile's order."""
    return [TargetRow(symbol=symbol, current=current[symbol]) for symbol in symbols]


def diff_rows(
    symbols: list[str], current: dict[str, int], proposed: dict[str, int]
) -> list[DiffRow]:
    """Current, proposed and change for each holding, in the profile's order."""
    return [
        DiffRow(
            symbol=symbol,
            current=current[symbol],
            proposed=proposed[symbol],
            change=proposed[symbol] - current[symbol],
        )
        for symbol in symbols
    ]
