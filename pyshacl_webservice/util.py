# -*- coding: utf-8 -*-
import sys
try:
    # v39.0 and above.
    try:
        from setuptools.extern import packaging
    except ImportError:
        # Before v39.0
        from pkg_resources.extern import packaging
    version = packaging.version
except ImportError:
    raise RuntimeError("The 'packaging' library is missing.")

if sys.version_info[0:3] >= (3, 5, 0):
    async def add_success_callback(fut, callback):
        result = await fut
        await callback(result)
        return result

__all__ = ['version']
