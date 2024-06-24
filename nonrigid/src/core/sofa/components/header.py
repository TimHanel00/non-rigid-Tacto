from typing import Optional
import Sofa.Core

from core.log import Log

def add_scene_header(
    root_node: Sofa.Core.Node,
    gravity: list = [0, -9.81, 0],
    dt: float = 0.01,
    alarm_distance: Optional[float] = 0.002,
    contact_distance: Optional[float] = 0.001,
    friction: Optional[float] = 0.0,
    background_color: list = [1,1,1,1],
    visual_flags: list = ["showForceFields"],
    light_direction: list = [],
    visual_text: Optional[str] = None,
    visual_text_position: list = [0,0,0],
    visual_text_color: list = [0,0,0,1]
):
    """  
    Adds the scene header to the SOFA scene depending on the specified parameters.

    Args:
        root_node: root node of the simulation.
        gravity: gravivty force.
        dt: simulation time step.
        alarm_distance: alarm distance for the collision pipeline. Setting it to None disables collision pipeline.
        contact_distance: contact distance for the collision pipeline. Setting it to None disables collision pipeline.
        friction: Friction coefficient. It is used only in case the collision pipeline is active.
        background_color: RGBA defining background color.
        visual_flags: list of strings that control what should be visualized in the SOFA GUI.
        light_direction: list with direction/s of the simulation lights.
        visual_text: Text that can be visualized in the simulation scene in the SOFA GUI.
        visual_text_position: Position of the text in the SOFA GUI.
        visual_text_color: RGBA of the text in the SOFA GUI.
    
    """
    root_node.dt = dt
    root_node.gravity = gravity
    root_node.addObject('DefaultVisualManagerLoop')
    root_node.addObject('VisualStyle', displayFlags=visual_flags)
    root_node.addObject('BackgroundSetting', color=background_color)

    root_node.addObject('DefaultAnimationLoop')
    # root_node.addObject('FreeMotionAnimationLoop')
    # root_node.addObject('GenericConstraintSolver', 
    #                 maxIterations=1000, 
    #                 tolerance=1e-6, 
    #                 printLog=0, 
    #                 allVerified=0
    #                 )

    # root_node.addObject('LCPConstraintSolver',
    #                 tolerance=1e-6, 
    #                 mu=0.0001,
    #                 printLog=0, 
    #                 )

    if (alarm_distance is None) or (contact_distance is None):
        Log.log(module="Sofa", severity="WARN", msg="Collision pipeline is not created!")
    else:
        root_node.addObject('DefaultPipeline')
        root_node.addObject('BruteForceBroadPhase')
        root_node.addObject('BVHNarrowPhase')
        root_node.addObject('MinProximityIntersection',
                        alarmDistance = alarm_distance, 
                        contactDistance = contact_distance, 
                        )
        root_node.addObject('DefaultContactManager', 
                        name = "ContactResponse", 
                        response = "FrictionContactConstraint", 
                        responseParams = f"mu={friction}"
                        )

    if not visual_text is None:
        root_node.addObject('Visual3DText', 
                                text=visual_text, 
                                position=visual_text_position, 
                                scale=0.02, 
                                color=visual_text_color
                                )

    if len(light_direction):
        root_node.addObject('LightManager')
        for i, d in enumerate(light_direction): 
            root_node.addObject('DirectionalLight', 
                                    name="light"+str(i), 
                                    color=[1, 1, 1, 1], 
                                    direction=d
                                    ) 
