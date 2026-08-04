from . import part
from . import service_order
from . import service_type
from . import vehicle

# loaner.py extends librefleet.vehicle and prototypes librefleet.part, so both
# must already be registered: within a module, import order matters.
from . import loaner

# ch22: extensions of CORE models. These resolve against the registry built from
# our manifest's depends, not against this package, so their position here is
# free. Grouped last only to keep "ours" and "theirs" visually separate.
from . import product_template
from . import res_partner
