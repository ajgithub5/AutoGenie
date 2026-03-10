from __future__ import annotations

from modules.models import Car, CarSearchCriteria, CarResult
from modules.config import get_settings

import json
from pathlib import Path

def load_catalog(path: Path) -> list[Car]:
    """
    Loads the json catalog and returns list of cars and its details in a list format

    Arg:
    path: Path of the json file containing the details of all car models.

    Returns:
    List of cars available in the database
    """
    with path.open("r", encoding = "utf-8") as f:
        raw = json.load(f)
    return [Car(**item) for item in raw]

settings = get_settings()
catalog = load_catalog(settings.car_catalog_path)

def search_cars(criteria: CarSearchCriteria) -> list[CarResult]:
    """
    Filter cars by budget, country, and optional body type.

    Arg:
    criteria: Parameters to be used for filetering cars.

    Returns:
    List of cars matching the provided criteria.
    """
    current_year = max(car.year for car in catalog)
    min_threshold_year = current_year - 2

    filtered_results = []
    for car in catalog:
        if car.year < min_threshold_year:
            continue
        if criteria.country.upper() not in [country.upper for country in car.countries_available]:
            continue
        if criteria.body_type and criteria.body_type.lower() != car.body_type.lower():
            continue
        if criteria.budget_min is not None and car.base_price_usd < criteria.budget_min:
            continue
        if criteria.budget_max is not None and car.base_price_usd > criteria.budget_max:
            continue

        reason = (
            f"{car.make} {car.model} fits your budget and is available in {criteria.country.upper()}"
        )
        filtered_results.append(CarResult(car=car, reason=reason))

    return filtered_results


