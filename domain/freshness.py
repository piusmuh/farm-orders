from datetime import date

from domain.produce import Produce


class FreshnessPolicy:
    """BR4 Domain Service: needs the produce (shelf life) and the lot (harvest date).

    This decision does not belong on ProduceOrder (orders should not know lots)
    or on StockLot (a lot should not own produce-wide shelf-life policy).
    The last day of the shelf life still counts as fresh.
    """

    def is_fresh(self, produce: Produce, harvest_date: date, on_date: date) -> bool:
        age = (on_date - harvest_date).days
        return 0 <= age <= produce.shelf_life_days
