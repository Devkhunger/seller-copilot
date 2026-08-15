import math

def detect_spikes(values: list[float], z_threshold: float = 2.0) -> list[int]:
    if len(values) < 3:
        return []
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)
    if std == 0.0:
        return []
    return [i for i, v in enumerate(values) if (v - mean) / std >= z_threshold]
