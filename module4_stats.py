"""Module 4 - Small reusable statistic functions (+ a little numpy)."""

import numpy as np


def calculate_average(total, count):
    if count == 0:
        return 0
    return total / count


def calculate_percentage(part, whole):
    if whole == 0:
        return 0
    return (part / whole) * 100


def find_top(data_dict):
    # Find the key with the biggest value.
    top_key = None
    top_value = None
    for key in data_dict:
        value = data_dict[key]
        if top_value is None or value > top_value:
            top_key = key
            top_value = value
    return top_key, top_value


def _value_of(item):
    # Helper so sorted() stays simple (no lambda).
    return item[1]


def sort_desc(data_dict):
    # Same dict items, biggest first.
    items = list(data_dict.items())
    return sorted(items, key=_value_of, reverse=True)


def format_money_table(data_dict, total, top_n=None):
    # Lines like:  Drama : USD 123,456 (12.1%).
    lines = ""
    items = sort_desc(data_dict)
    if top_n is not None:
        items = items[:top_n]
    for key, value in items:
        percent = calculate_percentage(value, total)
        lines = lines + f"{str(key):<22}: USD {value:>15,.0f}  ({percent:>5.1f}%)\n"
    return lines


def format_count_table(data_dict, total, top_n=None):
    # Lines like:  Drama : 1234 (12.1%).
    lines = ""
    items = sort_desc(data_dict)
    if top_n is not None:
        items = items[:top_n]
    for key, value in items:
        percent = calculate_percentage(value, total)
        lines = lines + f"{str(key):<22}: {value:>6}  ({percent:>5.1f}%)\n"
    return lines


# ---------- small numpy helpers ----------
def _clean_numbers(values):
    # Keep only real numbers, drop missing ones.
    out = []
    for v in list(values):
        try:
            number = float(v)
        except (ValueError, TypeError):
            continue
        if np.isnan(number):
            continue
        out.append(number)
    return out


def np_mean(values):
    nums = _clean_numbers(values)
    if len(nums) == 0:
        return 0.0
    return float(np.mean(nums))


def np_median(values):
    nums = _clean_numbers(values)
    if len(nums) == 0:
        return 0.0
    return float(np.median(nums))


def np_std(values):
    nums = _clean_numbers(values)
    if len(nums) <= 1:
        return 0.0
    return float(np.std(nums, ddof=1))


def roi_stats(df):
    # Mean and median ROI for movies that have a budget.
    rois = []
    for value in df["ROI"]:
        try:
            number = float(value)
        except (ValueError, TypeError):
            continue
        if np.isnan(number):
            continue
        if number == float("inf") or number == float("-inf"):
            continue
        rois.append(number)
    if len(rois) == 0:
        return {"n": 0, "mean": 0.0, "median": 0.0}
    return {"n": len(rois), "mean": float(np.mean(rois)), "median": float(np.median(rois))}


def top_n_share(data_dict, n=3):
    # What percent of the total do the top-n keys hold?
    ordered = sort_desc(data_dict)
    top_values = []
    for i in range(min(n, len(ordered))):
        top_values.append(ordered[i][1])
    total = 0
    for key in data_dict:
        total = total + data_dict[key]
    if total == 0:
        return 0.0
    part = 0
    for v in top_values:
        part = part + v
    return part / total * 100
