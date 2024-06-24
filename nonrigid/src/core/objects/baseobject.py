import string
from typing import Dict, Any, List
from enum import Enum
import os
import re

class BaseObject():
    file_basename = "base_this_should_never_appear"
    file_extension = "obj"

    def __init__(
        self,
        id: int,
        file_basename: str = "",
        file_extension: str = "",
        source_file: str = "",
        tag: str = None,

    ) ->None:
        """
        Base class for all scene objects.

        Args:
            source_file: Filename from which a mesh should be loaded instead of
                randomly generated
            tag: Unique name for the scene object for cross referencing
        """
        # self.parameters = parameters
        self.file_basename = file_basename
        char_id = BaseObject.int_id_to_char( id )
        self.filename = f"{file_basename}_{char_id}.{file_extension}"
        self.source_file = source_file
        if tag is not None:
            self.tag = tag

    def get_config_parameters(
        self,
    ) ->dict:
        params = {}

        save_types = [int, float, list, tuple, str, bool]

        attribute_names = self.__dir__()
        for name in attribute_names:
            attr = getattr( self, name )
            if type(attr) in save_types:
                params[name] = attr
            elif isinstance(attr, Enum):
                params[name] = str(attr)
        return params

    @classmethod
    def construct_filepattern(
            cls,
            postfix: str = "",
    ) -> str:
        """
        Constructs a file pattern matching a scene object with the class' base_name,
        any obj_id within the sceneobject.filename and a given postfix between the
        sceneobject.filename and the class' extension.
        Actually, I think this is not needed according to the use in the blocks and
        has_files in the DataSample.
        """
        #return f"{cls.file_basename}.*{postfix}\.{cls.file_extension}"
        return f"{cls.file_basename}{postfix}.*.{cls.file_extension}"

    @classmethod
    def construct_filename(
            cls,
            filename: str = None,
            postfix: str = "",
            extension: str = "",
    ) -> str:
        """
        Used to create names for additional files that belong to this scene object but don't
        contain its 3D representation, e.g. parameter files.

        This naming is merged here for generating the file patterns before instantiation
        and for creating the actual file names at creation in order to keep it consistent.
        However, keeping postfix and extension consistent is up to the scene object.

        Args:
            filename: File name of the scene object at instantiation, e.g. 'force_A.obj'.
                Will be taken apart to extract only 'force'.
            postfix: Name describing the type of additional file, e.g. '_parameters'.
            extension: File extension of the additional file without the leading dot,
                e.g. 'txt'.

        Returns:
            if filename: According to the example, 'force_A_parameters.txt'
            else: According to the example, 'force__parameters.txt'
        """
        additional_filename = ""
        # this is used with the instantiated scene object's whole file name including ID
        if filename is not None:
            name, _ = os.path.splitext(filename)
            additional_filename = f"{name}{postfix}.{extension}"
        # this is used before the instantiation of the scene object with only its base name
        else:
            additional_filename = cls.construct_filepattern(postfix=postfix)
        return additional_filename

    @classmethod
    def name_additional_files(cls) -> List[str]:
        """
        Construct file patterns to match additional files that this scene object definition
        will cause in the run of the program.

        Used to let blocks know their output up front when it depends on the scene objects.
        """
        return []

    def get_filename_elements(self):
        """Extract the file base name and the character ID part of the file name.

        Example:
            surface_A.obj -> 'surface', '_A'
        """
        base_name, _ = os.path.splitext(self.filename)
        id_match = re.search(r"(_[A-Z]?)\.", self.filename)
        if id_match is not None:
            id = id_match.group(1)
            base = base_name.replace(id, '')
        else:
            id = ''
            base = base_name
        return base, id

    @staticmethod
    def int_id_to_char( id: int ) -> str:
        """ Convert a positive integer to a letter between A and Z.

        0 -> A
        1 -> B
        25 -> Z

        If the integer is greater than 25, use multiple letters.
        """
        assert id >= 0

        # Zero-based:
        id = id + 1

        chars = []
        while id > 0:
            id, d = divmod(id, 26)
            chars.append(string.ascii_uppercase[d - 1])
        char_id = ''.join(reversed(chars))
        return char_id

    @staticmethod
    def check_parameters(**kwargs: Dict[str, Any]) -> None:
        """
        Perform a sanity check on parameters that will be used for initialization.

        Since the scene object generator block will first add the description of the
        scene objects to a template list before actually initializing them in its
        run() method, it makes sense to sanity check passed parameter values and
        potentially throw an error at setup before run() is called on each sample.

        Args:
            **kwargs:
        """
        pass

    @staticmethod
    def update_parameters_from_templates(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update parameters that will be used for initialization based on new information
        from other scene object templates that have been defined for this scene.

        Sometimes, information required for the creation of a scene object is not
        available when its description is generated, e.g. references to other
        scene object templates. This method can be used to update the description of the desired
        scene object with the new information. It is created to avoid that the
        scene object generator block has too much information about the inner workings
        of specific scene objects while keeping scene objects ignorant of the data
        sample.

        Args:
            **kwargs: Keyword argument dictionary describing the scene object to be generated,
                potentially containing extra keywords for passing on specific scene object
                templates to be processed.

        Returns:
            Updated keyword argument dictionary describing the scene object to be generated.
        """
        return kwargs

    @staticmethod
    def update_parameters_from_instances(**kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update parameters that will be used for initialization based on new information
        from other scene object instances that have been created for this scene.

        Sometimes, information required for the creation of a scene object is not
        available when its description is generated, e.g. references to other (instantiated)
        scene objects. This method can be used to update the description of the desired
        scene object with the new information. It is created to avoid that the
        scene object generator block has too much information about the inner workings
        of specific scene objects while keeping scene objects ignorant of the data
        sample.

        Args:
            **kwargs: Keyword argument dictionary describing the scene object to be generated,
                potentially containing extra keywords for passing on specific scene object
                instances to be processed.

        Returns:
            Updated keyword argument dictionary describing the scene object to be generated.
        """
        return kwargs

    def __str__(self):
        filename_without_ext = self.filename.split(".")[0]
        ret_str = f"Scene object {filename_without_ext} of type {self.__class__}"
        if hasattr(self, "tag"):
            ret_str += f", tagged {self.tag}"
        return ret_str

if __name__ == "__main__":
    
    for i in range(100):
        print(i, BaseObject.int_id_to_char( i ))


