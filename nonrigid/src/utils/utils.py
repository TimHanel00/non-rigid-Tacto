import random

from core.log import Log

def trunc_norm(
        rnd: random.Random,
        mu: float = 0.0,
        sigma: float = 1.0,
        min: float = -0.5,
        max: float = 0.5
) -> float:
    """
    Sample a value from a truncated normal distribution using the provided random number generator.

    Args:
        rnd: Random number generator instance to use, possibly `sample.random()` from a `core.DataSample`.
        mu: Mean of the truncated normal distribution.
        sigma: Standard deviation of the truncated normal distribution.
        min: Lower clip value in sample space (not in number of standard deviations).
        max: Upper clip value in sample space (not in number of standard deviations).

    Returns:
        A single random number from the specified distribution.
    """

    # make sure range is valid
    if min > max:
        msg = "Had to flip the range values for the truncated normal distribution!"
        Log.log(severity="WARN", msg=msg, module="Random Sampling")
        tmp = min
        min = max
        max = tmp
    elif min == max:
        msg = "Truncated normal distribution clipped with min=max! Returning that value."
        Log.log(severity="WARN", msg=msg, module="Random Sampling")
        return min
    elif mu < min or mu > max:
        msg = f"Truncated normal distribution parametrized badly! Mu: {mu}, min: {min}, max: {max}"
        raise ValueError(msg)

    draw = min - 1
    while (draw < min or draw > max):
        draw = rnd.normalvariate(mu=mu, sigma=sigma)

    return draw