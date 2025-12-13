from flask import abort
from functools import wraps
import inspect
from typing import Any, Optional, get_type_hints
import re

from flask import Blueprint
from app.db import db


URL_PATTERN = r"<([a-z]+)_id>"

def identify_possible_endpoint_objects(endpoint: str) -> list[str]:
    """
    Identifies all instances of <*_id> notation in a given URL
    
    
    :param endpoint: Description
    :type endpoint: str
    :return: List of extracted parameters from URL
    :rtype: list[str]
    """
    return re.findall(URL_PATTERN, endpoint)

def get_injection_type(type_hints: dict[str, Any], class_name: str) -> Optional[Any]:
    """
    Gets the injection type for a corresponding extracted ID
    
    :param type_hints: Type hints that are provided for bottom-level function
    :type type_hints: dict[str, Any]
    :param class_name: Name of parameter extracted from URL
    :type class_name: str
    :return: Class for the injected type
    :rtype: Any
    """
    return type_hints.get(class_name)

def injection_route(blueprint: Blueprint, endpoint: str, *args, **kwargs):
    """
    Allows for context injection into a given endpoint that follows the format:
    
    Endpoint: "../<class_id>/.."
    Function call: def function(class: ClassName...)
    
    From class_id, maps to the parameter in the function, retrieves the type, then
    calls a query on the id from the class object.
    
    :param blueprint: Blueprint to add injection endpoint to
    :type blueprint: Blueprint
    :param endpoint: Endpoint pattern for blueprint
    :type endpoint: str
    :param args: Arguments for blueprint addition
    :param kwargs: Keyword arguments for blueprint addition
    """

    def decorator(fn: callable):
        """
        Decorator to be placed on top of the bottom-level calling function
        
        :param fn: Function to be decorated on
        :type fn: callable
        """
        bottom_level_function = inspect.unwrap(fn)
        type_hints = get_type_hints(bottom_level_function)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            """
            Wraps the function and actievly injects matching parameters.
            Aborts if no instance is found for the given user
            
            :param args: Argument for bottom level class
            :param kwargs: Keyword arguments for bottom level class
            """
            
            injection_kwargs = {}
            possible_endpoint_objs = identify_possible_endpoint_objects(endpoint)
            
            # For each possible injectable object
            for injection in possible_endpoint_objs:
                
                # Get type
                injection_type = get_injection_type(type_hints, injection)
                
                if not injection_type:
                    # Type not found, continue
                    continue
                
                # Search for object
                injection_kwargs[injection] = db.session.get(
                    injection_type, 
                    int(kwargs[injection + "_id"])
                )
                
                # Return if object not found
                if not injection_kwargs[injection]:
                    return abort(404, "The requested object was not found")
                
                del kwargs[injection + "_id"]
                    
            # Add injections to KWs
            injection_kwargs = {**injection_kwargs, **kwargs}
            return fn(*args, **injection_kwargs)
        
        # Route blueprint using endpoint through the wrapper
        blueprint.route(endpoint, *args, **kwargs)(wrapper)
        return wrapper
    
    return decorator
    