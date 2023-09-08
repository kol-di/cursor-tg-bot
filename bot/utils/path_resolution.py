from pathlib import Path
import os


def check_can_create_dir(path, dir):
    """
    Checks if directory can be crated. 
    If so, creates it
    """
    try:
        if dir:
            path.mkdir(exist_ok=True)
        else:
            path.touch(exist_ok=True)
        os.chmod(path, 0o777)
    except OSError:
        return False
    return True


def resolve(input_path, caller_path, dir=True):
    import __main__
    path = next(
        cand_path for cand_path in [
            # absolute path provided
            Path(input_path),   
            # path relative to current file, when program ran as script
            Path(caller_path).parent / input_path,     
            # path relative to executable
            Path(__main__.__file__).parent / input_path     
        ] if check_can_create_dir(cand_path, dir=dir))
    return path