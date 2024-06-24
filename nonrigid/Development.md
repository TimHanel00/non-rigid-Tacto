# Development guidelines:

## Coding conventions:
Please use the conventions defined in PEP 8 wherever possible:
https://peps.python.org/pep-0008/

- 4 spaces for indentation (no tabs)
- Class names in CapWords (also known as CamelCase)
- lower-case function names with underscores (snake_case)
- non-public attributes of a class start with an underscore
- use f-strings to format strings
- function/method names should start with a verb and describe what it does, e.g. clear_scene(...), select_other_vert(...), perturb_direction(...), check_side_overlap(...)

## Dependencies:
This pipeline already has quite a few dependencies. If possible, avoid adding more!
If you really have to add a dependency, one that is installable via pip is always preferred over other ways of installing.

## Exceptions:
Use exceptions to raise issues when a function cannot proceed. Wherever sensible, use [python's Exception types](https://docs.python.org/3/library/exceptions.html).

Note: When a sample cannot be processed due to numerical issues, being out of range etc., this should usually not be considered a fatal error! In order for the pipeline to process this correctly, please raise a SampleProcessingException (see exceptions.py) in order for the pipeline to correctly continue!

## Documentation
Documentation style follows Google style with Python 3 type annotations according to PEP 484. This means that the input types should be defined in the input list and not in the docstring. Google python style guide can be found [at this link](https://google.github.io/styleguide/pyguide.html). 

Some general rules:
- Define input and output types.
- Follow the indentation rule as in the example below.

Example documentation for functions and classes:
```
def func(
    arg1: int, 
    arg2: str,
) ->bool:
    """Summary line.

    Extended description of function.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    """
    return True

class Class:
    """Summary line.

    Extended description of class.

    """

    def __init__(
        self, 
        arg1: int,
        arg2: str,
    ) -> None:
        """Initializes the class.

        Args:
            arg1: This is the first argument
            arg2: This is the second argument
        """
        pass
```
