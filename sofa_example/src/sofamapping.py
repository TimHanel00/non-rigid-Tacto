from Sofa.Core import ObjectFactory
registry = ObjectFactory.Registry()

print("Available Mappings:")
for key, obj in registry.items():
    if 'Mapping' in obj.componentType:
        print(obj.name)
