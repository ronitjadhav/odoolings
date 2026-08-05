from . import part
from . import service_order
from . import service_type
from . import vehicle

# loaner.py extends librefleet.vehicle and prototypes librefleet.part, so both
# must already be registered: within a module, import order matters.
from . import loaner
