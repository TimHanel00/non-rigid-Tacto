from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException


from utils.utils import trunc_norm

class SceneObjectGeneratorBlock(PipelineBlock):
    """ Block used to generate scene objects for every DataSample.

    This block should be added to the beginning of your pipeline.
    Then call the add_object_template() method with all the objects
    you would want to create for the scenes.

    When the block runs, its "run" function is called on every DataSample
    and it will create the scene objects. At this point, it will sample
    the parameters for the scene objects from the given parameter
    ranges (that were previously passed to add_object_template()), allowing
    the objects to differ in parameters from DataSample to DataSample.

    Note: After this block has run, generated scene object will end up in 
    `sample.scene_objects`. Downstream pipeline blocks will be able to access
    the objects through this parameter.

    See the sample run_*.py scripts for usage examples.
    """

    def __init__(
            self,
    ):
        self.templates = []
        # save tags separately for easier uniqueness check when adding a new object template
        self.template_tags = []

        super().__init__([], [])

    def add_object_template( self,
            obj_class: type,
            params: dict = {}
    ):
        """ Add a new object to be generated

        The objects class given here will be instantiated for each scene object.
        If the creation of an object should be optional, then `params` should contain
        a key "ex_likelyhood" which is lower than 1. This value is interpreted as the
        existance likelyhood for the object (0 -> never created, 1 -> created for every
        scene object). For example, params["ex_likelyhood"] = 0.5 would mean that roughly
        half of the DataSamples will end up having this object, for the other half it
        will not be created.

        Other values passed to params may be single values (in which case the value is
        given to the object's constructor when it is created) or tuples with two entries
        (in which case the passed value is first sampled uniformly from the range given
        by the tuple). For example, params["stiffness"] = (0.5, 1.5) would mean that the
        generated object would be constructed with a "stiffness" parameter set to be 
        a value drawn uniformly from the range 0.5 to 1.5.

        Args:
            obj_class: The type of object to be generated. Should be a class derived
                from :class:`~core.objects.baseobject.BaseObject`.
            params: The key, value pairs of all the parameters which will be given
                to the object. Note: These must have the same names as the parameters of
                the `obj_class`'s initializer, i.e. if you pass
                :class:`~core.objects.sceneobjects.Ligament` as obj_class then `params`
                should contain a key "stiffness" with an appropriate value.
                Note: The values given for the parameters may optionally be tuples instead
                of single values. If the tuple contains two values, the first will be
                interpreted as the minimum and the second as the maximum of a uniform
                distribution to sample the value from. If the tuple contains four values,
                it will be interpreted as (mean, standard deviation, minimum value,
                maximum value) of a truncated normal distribution to sample the value from.
        """
        if not "ex_likelyhood" in params:
            params["ex_likelyhood"] = 1

        if "tag" in params:
            tag = params["tag"]
            if tag in self.template_tags:
                msg = f"Tag '{tag}' is already in use! Scene object tags must be unique. " \
                      "Check other uses of SceneObjectGeneratorBlock.add_object_template. " \
                      "Continuing without this tag."
                Log.log(severity="WARN", module="SceneObjectGeneratorBlock", msg=msg)
                params.pop("tag")
            else:
                self.template_tags.append(tag)

        # perform object type-specific sanity check of parametrization
        # the object class does it -> the generator block remains blissfully ignorant of
        # scene object specifics
        obj_class.check_parameters(**params)

        self.templates.append( { "obj_class":obj_class, "params":params } )

    def run(self, sample):
        """ Construct scene objects for the given sample.

        Note: After this function has run, generated scene object will end up in 
        `sample.scene_objects`. Downstream pipeline blocks will be able to access
        the objects through this parameter.
        """

        for obj in self.templates:
            obj_class = obj["obj_class"]
            params = obj["params"].copy()

            # To determine the object's ID, we count how many objects of this type are
            # already stored for this sample:
            obj_id = len([o for o in sample.scene_objects if isinstance(o, obj_class)])

            # Depending on the 'existence likelihood', determine whether this
            # object should exist for the given sample, or not
            if params["ex_likelyhood"] < 1:
                l = sample.random.random()
                if l > params["ex_likelyhood"]:
                    continue

            # for cross references between scene objects:
            # update scene object construction parameters based on other
            # scene object TEMPLATES
            params["scene_object_templates"] = self.templates
            params = obj_class.update_parameters_from_templates(**params)
            params.pop("scene_object_templates")

            # for cross references between scene objects:
            # update scene object construction parameters based on other
            # scene object INSTANCES
            # more specifically: retrieve the specific
            # scene object of the target structure from the DataSample
            # e.g.: Vasculature scene objects retrieve their containing organ's
            # filename
            if "structure_tag" in params:
                tag = params["structure_tag"]
                # this search function returns a list for the case that someone queries
                # by scene object type
                organ_scene_objects = sample.find_scene_object(tag=tag)
                print("ORGAN FOUND:", organ_scene_objects)
                if organ_scene_objects is not None:
                    try:
                        # pass found filenames to requesting scene object
                        # and process further there
                        params["referenced_structure"] = organ_scene_objects
                        params = obj_class.update_parameters_from_instances(**params)
                        params.pop("referenced_structure")
                    except AssertionError as e:
                        raise SampleProcessingException(self, sample, e.args[0])
                else:
                    msg = (f"No target structure with the tag {tag} could be found in "
                           f"DataSample {sample.id}. Does the 'structure_tag' given to the "
                           f"{obj_class} scene object with ID {obj_id} match the 'tag' "
                           f" given to the target structure in the calls to "
                           f"SceneObjectGeneratorBlock.add_object_template?")
                    raise SampleProcessingException(self, sample, msg)

            # sample values for parameters with value ranges
            sampled_params = {}
            for k, p in params.items():
                if k != "ex_likelyhood":
                    if type(p) == tuple:
                        if len(p) == 2:
                            val = sample.random.uniform(p[0], p[1])
                        elif len(p) == 4:
                            val = trunc_norm(sample.random,
                                             mu=p[0],
                                             sigma=p[1],
                                             min=p[2],
                                             max=p[3])
                        else:
                            val = sample.random.uniform(p[0], p[1])
                    else:
                        val = p
                    sampled_params[k] = val

            print("sampled_params:", sampled_params)

            # instantiate scene object
            o = obj_class(obj_id = obj_id, **sampled_params)
            #Log.log(f"Created object {o.filename} of class {obj_class}")
            # save the whole configuration for each object, including default values
            all_params = o.get_config_parameters()
            class_attrs = dir(o.__class__)
            for key in all_params:
                # file_basename and file_extensions are saved in class attributes
                # saving them is not necessary since we have the filename
                if key not in class_attrs and key != 'filename':
                    sample.set_config_value(self,
                                            key,
                                            all_params[key],
                                            category_key=o.filename)

            # store the finished scene object in the sample
            sample.scene_objects.append( o )

