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
    
    Args:
        endpoint (str): Endpoint URL pattern to analyze
        
    Returns:
        list[str]: List of extracted parameter names
    """
    return re.findall(URL_PATTERN, endpoint)

def get_injection_type(type_hints: dict[str, Any], class_name: str) -> Optional[Any]:
    """
    Gets the injection type for a corresponding extracted ID
    
    Args:
        type_hints (dict[str, Any]): Type hints from the function
        class_name (str): Class name to extract type for
        
    Returns:
        Optional[Any]: Extracted type or None if not found
    """
    return type_hints.get(class_name)

def injection_route(blueprint: Blueprint, endpoint: str, *args, **kwargs):
    """
    Allows for context injection into a given endpoint that follows the format:
    
    Endpoint: "../<class_id>/.."
    Function call: def function(class: ClassName...)
    
    From class_id, maps to the parameter in the function, retrieves the type, then
    calls a query on the id from the class object.
    
    Args:
        blueprint (Blueprint): Blueprint to add injection endpoint to
        endpoint (str): Endpoint pattern for blueprint
        *args: Arguments for blueprint addition
        **kwargs: Keyword arguments for blueprint addition
        
    Returns:
        callable: Decorated function with injection capabilities
    """

    def decorator(fn: callable) -> callable:
        """
        Decorator to be placed on top of the bottom-level calling function
        
        Args:
            fn (callable): Bottom-level function to decorate
            
        Returns:
            callable: Wrapped function with injection capabilities
        """
        bottom_level_function = inspect.unwrap(fn)
        type_hints = get_type_hints(bottom_level_function)
        
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            """
            Wraps the function and actievly injects matching parameters.
            Aborts if no instance is found for the given user
            
            Args:
                args: Argument for bottom level class
                kwargs: Keyword arguments for bottom level class
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
    