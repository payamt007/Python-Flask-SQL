import re


def validate(date_from: str, date_to: str, origin: str, destination: str) -> list[str]:
    """
    This custom validator filter unwanted inputs from query parameters

    :param date_from: Initial target date
    :param date_to: Final target date
    :param origin: Origin of travel
    :param destination: Destination of travel
    :return: list of average prices per day
    """
    errors = []

    date_pattern = re.compile(r"^\d{4}-(0?[1-9]|1[012])-(0?[1-9]|[12][0-9]|3[01])$")
    region_code_pattern = re.compile(r"^[A-Z]{5}$")
    slug_pattern = re.compile(r"^[a-z]+(_[a-z]+)*$")

    if date_from and not date_pattern.match(date_from):
        errors.append("date_from format is not valid")
    if date_to and not date_pattern.match(date_to):
        errors.append("date_from format is not valid")
    if date_from == date_to:
        errors.append("date_from and date_to couldn't be same!")
    if origin is None:
        errors.append("origin should be determined")
    if destination is None:
        errors.append("destination should be determined")
    if date_to is None:
        errors.append("date_to should be determined")
    if date_from is None:
        errors.append("date_from should be determined")

    if not (region_code_pattern.match(origin) or slug_pattern.match(origin)):
        errors.append("origin format is not valid")
    if not (region_code_pattern.match(destination) or slug_pattern.match(destination)):
        errors.append("destination format is not valid")
    if origin and destination and origin == destination:
        errors.append("destination and region can not be same")

    return errors
