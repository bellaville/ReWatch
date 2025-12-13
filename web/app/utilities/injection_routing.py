from flask import abort
from functools import wraps
import inspect
from typing import Any, get_type_hints
import re

from flask import Blueprint
from db import db


URL_PATTERN = r"<([a-z])_id>"

def identify_possible_endpoint_objects(endpoint: str) -> list[str]:
    return re.findall(URL_PATTERN, endpoint)

def get_injection_type(type_hints: dict[str, Any], class_name: str) -> Any:
    return type_hints.get(class_name)

def get_class_from_string(class_name: str):
    """Return class reference mapped to table.

    :param tablename: String with name of table.
    :return: Class reference or None.
    """
    for mapper in db.Model.registry.mappers:
        cls = mapper.class_
        if hasattr(cls, '__tablename__') and cls.__tablename__ == class_name:
            return cls

def injection_route(blueprint: Blueprint, endpoint: str, *args, **kwargs):

    def decorator(fn: callable):
        endpoint_function = inspect.unwrap(fn)
        type_hints = get_type_hints(endpoint_function)
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            
            injection_kwargs = {}
            
            for injection in identify_possible_endpoint_objects(endpoint):
                injection_type = get_injection_type(type_hints, injection)
                
                if not injection_type:
                    # Type not found, continue
                    continue
                
                injection_kwargs[injection] = injection_type.query.get(int(kwargs[injection + "_id"]))
                
                if not injection_kwargs[injection]:
                    return abort(404, "The requested object was not found")
                    
            injection_kwargs = {**injection_kwargs, **kwargs}
            return fn(*args, **injection_kwargs)
        
        blueprint.route(endpoint, *args, **kwargs)(wrapper)
        return wrapper
    
    return decorator
    