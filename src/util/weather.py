def k_to_c(k: float) -> float:
    return round(k - 273.15, 1)


def k_to_f(k: float) -> int:
    return round((9 / 5 * (k - 273.15) + 32))
