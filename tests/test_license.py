import re
from dependencywatcher.license import License

test_licenses = [
    ["Apache License, Version 2.0", "Apache v2.0"],
    ["The Apache Software License, Version 2.0", "Apache v2.0"],
    ["MIT License", "MIT"],
    ["CC-BY-NC-3.0", "CC-BY-NC v3.0"],
    ["BSD license (see license.txt for details), Copyright (c) 2000-2015, ReportLab Inc.", "BSD"],
    ["Eclipse Public License 1.0", "EPL v1.0"],
    ["BSD 3-Clause", "BSD New v3"],
    ["the Apache License, ASL Version 2.0", "Apache v2.0"],
    ["GNU Lesser General Public License (LGPL), Version 2.1", "LGPL v2.1"]
]

def check_normalized(a, b):
    n = License(a).normalized
    assert b == n, "Expected: %s, actual: %s ('%s')" % (b, n, a)

def test_generator():
    for t in test_licenses:
        yield check_normalized, t[0], t[1]

