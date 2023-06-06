import pickle
import os
from collections.abc import Mapping, Set

def sort_object(obj):
    if isinstance(obj, dict) or isinstance(obj, Mapping):
        return {k: sort_object(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, set) or isinstance(obj, Set):
        return {sort_object(x) for x in sorted(obj)}
    elif isinstance(obj, list):
        return [sort_object(x) for x in obj]
    else:
        return obj

def save_to_pickle_object(object_to_be_saved, filename, files_generation_folder):
    sorted_object = sort_object(object_to_be_saved)
    with open(os.path.join(files_generation_folder, filename), 'wb') as fileout:
        pickle.dump(sorted_object, fileout, protocol=pickle.HIGHEST_PROTOCOL)

def pickle_load_file(file_name , input_folder):
    """ Load an object from a file"""
    with open(os.path.join(input_folder, file_name), 'rb') as f:
        return pickle.load(f)