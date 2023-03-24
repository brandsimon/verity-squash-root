from collections.abc import Mapping


def info_to_dict(output: str, sep: str = ":") -> Mapping[str, str]:
    result = {}
    for line in output.split("\n"):
        if sep not in line:
            continue
        s = line.split(sep, 2)
        key = s[0].strip()
        result[key] = s[1].strip()
    return result
