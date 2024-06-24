from typing import Union, List, Tuple
import re
from core.log import Log

# adapted from: https://www.freecodecamp.org/news/how-to-flatten-a-dictionary-in-python-in-4-different-ways/
def _flatten_dict_gen(
        d: dict,
        parent_key: Union[str, int, float],
        sep: str
):
    """Generator for flattening nested dictionaries. See ``flatten_dict`` for the documentation of the arguments."""
    for k, v in d.items():
        new_key = str(parent_key) + sep + str(k) if parent_key else str(k)
        if isinstance(v, dict):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v

# adapted from: https://www.freecodecamp.org/news/how-to-flatten-a-dictionary-in-python-in-4-different-ways/
def flatten_dict(
        d: dict,
        parent_key: Union[str, int, float] = '',
        sep: str = '|'
) -> dict:
    """Utility for flattening nested dictionaries.

    Args:
        d: Input nested dictionary.
        parent_key: If `d` is an item in a superordinate dictionary, pass the corresponding key for concatenation.
        sep: Separator between dictionary depth levels.

    Returns:
        A dictionary of depth one. Keys are converted to strings and concatenated using the specified
        separator.
    """
    return dict(_flatten_dict_gen(d, parent_key, sep))

def combine_stats_and_configs(
        stats: dict,
        configs: dict
) -> dict:
    """ Flatten the entries for each sample """

    # Some samples may exist in stats but not in config and vice versa -
    # make sure we cover them all!
    all_ids = set( list(stats.keys()) + list(configs.keys()) )

    combined = {}

    all_keys = set()

    for id in all_ids:
        entry = {
                "stats": {},
                "configs": {}
                }
        if id in stats.keys():
            entry["stats"] = stats[id]
        if id in configs.keys():
            entry["configs"] = configs[id]

        flat = flatten_dict( entry )
        for k in flat.keys():
            all_keys.add( k )
        combined[id] = flat

    msg = f"Avaibale keys for plotting:"
    for k in all_keys:
        msg += "\n\t" + k
    Log.log(severity="DETAIL", msg=msg, module="Analysis")
    return combined
        

def extract_values(
        data: dict,
        keys: List[str],
) -> Tuple[list]:
    """ Given a dictionary of stats for many samples, extract a subset of stats

    Args:
        data: Nested dictionary of sample statistics as
                    {sample.id: {key: value}}.
        keys: List of keys to extract

    Returns:
        A tuple of lists. The tuple has the same lengths as the 'keys' argument.
        Only samples are included for which there is a value for each of the keys.
        Samples which do not have entries for _all_ of the given keys are excluded.
        In other words: All extracted lists in the tuple will have the same length.

    """
    extracted = []
    for i in range(len(keys)):
        extracted.append( [] )
    for id, sample in data.items():
        entry = []
        all_keys_found_for_sample = True
        for key in keys:
            if key in sample.keys():
                entry.append( sample[key] )
            else:
                all_keys_found_for_sample = False
                break

        # If we found values for all of the keys, distribute them to the final lists:
        if all_keys_found_for_sample:
            for i, val in enumerate(entry):
                extracted[i].append( val )

    return tuple(extracted)
