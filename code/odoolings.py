#!/usr/bin/env python3
"""odoolings: auto-check your tutorial work against each chapter's goals.

Inspired by rustlings: after finishing a chapter's Hands-on section, run

    python odoolings.py check ch05

and it inspects your *actually running* Odoo over XML-RPC. Green means your
work matches the chapter checkpoint; red comes with a hint.

Stdlib only, nothing to install. Defaults match the tutorial's Docker env
(http://localhost:8069, database "tutorial", admin/admin).
"""
import argparse
import json
import sys
import xmlrpc.client


class Env:
    """Tiny XML-RPC wrapper. Checks call env.call(model, method, *args)."""

    def __init__(self, url, db, user, password):
        self.url, self.db, self.user, self.password = url, db, user, password
        self.common = xmlrpc.client.ServerProxy(url + "/xmlrpc/2/common")
        self.uid = None

    def login(self):
        self.uid = self.common.authenticate(self.db, self.user, self.password, {})
        assert self.uid, "authentication failed for %r on database %r" % (self.user, self.db)
        self.models = xmlrpc.client.ServerProxy(self.url + "/xmlrpc/2/object")

    def call(self, model, method, *args, **kw):
        if self.uid is None:
            self.login()
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, list(args), kw)


# ---------------------------------------------------------------- checks --
# One function per check; raise AssertionError (or anything) to fail.

def server_up(env):
    env.version_info = env.common.version()


def server_is_19(env):
    v = env.common.version()["server_version"]
    assert v.startswith("19"), "server reports version %s, tutorial targets 19.x" % v


def can_login(env):
    env.login()


def shell_partner_exists(env):
    ids = env.call("res.partner", "search", [("name", "=", "Ada Lovelace")])
    assert ids, "no res.partner named 'Ada Lovelace' in the database"


def _librefleet_module(env):
    mods = env.call("ir.module.module", "search_read",
                    [("name", "=", "librefleet")],
                    fields=["state", "latest_version", "application"])
    assert mods, "no module named 'librefleet' known to this database"
    return mods[0]


def librefleet_installed(env):
    state = _librefleet_module(env)["state"]
    assert state == "installed", "module state is %r, not 'installed'" % state


def librefleet_version_ok(env):
    v = _librefleet_module(env)["latest_version"] or ""
    assert v.startswith("19.0."), "installed version is %r, expected 19.0.x.y.z" % v


def librefleet_is_app(env):
    assert _librefleet_module(env)["application"], "'application' is not True in the manifest"


def vehicle_model_exists(env):
    ids = env.call("ir.model", "search", [("model", "=", "librefleet.vehicle")])
    assert ids, "no model 'librefleet.vehicle' registered in this database"


def _vehicle_fields(env):
    return {f["name"]: f for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.vehicle")],
        fields=["name", "ttype", "required"])}


def vehicle_fields_typed(env):
    expected = {"license_plate": "char", "vin": "char", "model_name": "char",
                "year": "integer", "mileage_km": "float", "notes": "text",
                "active": "boolean"}
    actual = _vehicle_fields(env)
    for name, ttype in expected.items():
        assert name in actual, "field %r is missing on librefleet.vehicle" % name
        assert actual[name]["ttype"] == ttype, (
            "field %r is %r, expected %r" % (name, actual[name]["ttype"], ttype))


def vehicle_plate_required(env):
    f = _vehicle_fields(env).get("license_plate")
    assert f and f["required"], "license_plate is not required=True"


def workshop_groups_exist(env):
    for xmlid in ("librefleet.group_librefleet_user", "librefleet.group_librefleet_manager"):
        res = env.call("ir.model.data", "check_object_reference",
                       xmlid.split(".")[0], xmlid.split(".")[1])
        assert res and res[0] == "res.groups", "%s does not resolve to a res.groups record" % xmlid


def vehicle_acls_exist(env):
    acls = env.call("ir.model.access", "search_count",
                    [("model_id.model", "=", "librefleet.vehicle")])
    assert acls >= 2, ("found %d access rules for librefleet.vehicle, expected one "
                       "per group (user + manager)" % acls)


def admin_reads_vehicles(env):
    ids = env.call("librefleet.vehicle", "search", [])
    assert ids, "admin got an empty vehicle list; are the ch09 vehicles still there?"


def service_type_fields_typed(env):
    fields = {f["name"]: f for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.service.type")],
        fields=["name", "ttype", "required"])}
    assert fields, "no model 'librefleet.service.type' registered in this database"
    for name, ttype in {"name": "char", "flat_fee": "float", "default_duration_h": "float"}.items():
        assert name in fields, "field %r is missing on librefleet.service.type" % name
        assert fields[name]["ttype"] == ttype, (
            "field %r is %r, expected %r" % (name, fields[name]["ttype"], ttype))
    assert fields["name"]["required"], "service type 'name' is not required=True"


def service_type_acls_exist(env):
    acls = env.call("ir.model.access", "search_count",
                    [("model_id.model", "=", "librefleet.service.type")])
    assert acls >= 2, ("found %d access rules for librefleet.service.type, "
                       "expected one per group" % acls)


def vehicle_action_exists(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "action_librefleet_vehicle")
    assert res[0] == "ir.actions.act_window", "librefleet.action_librefleet_vehicle is not a window action"
    act = env.call("ir.actions.act_window", "read", [res[1]], ["res_model", "view_mode"])[0]
    assert act["res_model"] == "librefleet.vehicle", "the action's res_model is %r" % act["res_model"]
    assert act["view_mode"] == "list,form", "view_mode is %r, expected 'list,form'" % act["view_mode"]


def root_menu_exists(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "menu_librefleet_root")
    assert res[0] == "ir.ui.menu", "librefleet.menu_librefleet_root is not a menu"


def vehicle_views_exist(env):
    views = env.call("ir.ui.view", "search_read",
                     [("model", "=", "librefleet.vehicle")], fields=["type"])
    types = {v["type"] for v in views}
    assert "list" in types, "no list view defined for librefleet.vehicle (remember: <list>, not <tree>)"
    assert "form" in types, "no form view defined for librefleet.vehicle"


def config_menu_manager_only(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "menu_librefleet_config")
    menu = env.call("ir.ui.menu", "read", [res[1]], ["group_ids"])[0]
    mgr = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "group_librefleet_manager")[1]
    assert mgr in menu["group_ids"], "the Configuration menu is not restricted to Workshop / Manager"


def technician_exists_in_group(env):
    users = env.call("res.users", "search_read",
                     [("login", "=", "tina")], fields=["group_ids"])
    assert users, "no user with login 'tina'"
    gid = env.call("ir.model.data", "check_object_reference", "librefleet", "group_librefleet_user")[1]
    assert gid in users[0]["group_ids"], "'tina' is not in the Workshop / User group"


def _model_fields(env, model):
    fields = {f["name"]: f for f in env.call(
        "ir.model.fields", "search_read", [("model", "=", model)],
        fields=["name", "ttype", "required", "relation", "relation_field"])}
    assert fields, "no model %r registered in this database" % model
    return fields


def _expect_field(fields, model, name, ttype, relation=None, required=None):
    assert name in fields, "field %r is missing on %s" % (name, model)
    f = fields[name]
    assert f["ttype"] == ttype, "%s.%s is %r, expected %r" % (model, name, f["ttype"], ttype)
    if relation:
        assert f["relation"] == relation, (
            "%s.%s points at %r, expected %r" % (model, name, f["relation"], relation))
    if required is not None:
        assert f["required"] == required, (
            "%s.%s required is %r, expected %r" % (model, name, f["required"], required))


def vehicle_relations(env):
    f = _model_fields(env, "librefleet.vehicle")
    _expect_field(f, "librefleet.vehicle", "owner_id", "many2one", "res.partner")
    _expect_field(f, "librefleet.vehicle", "service_order_ids", "one2many", "librefleet.service.order")
    assert f["service_order_ids"]["relation_field"] == "vehicle_id", (
        "service_order_ids must be the inverse of librefleet.service.order.vehicle_id")


def order_model_shape(env):
    m = "librefleet.service.order"
    f = _model_fields(env, m)
    _expect_field(f, m, "vehicle_id", "many2one", "librefleet.vehicle", required=True)
    _expect_field(f, m, "service_type_id", "many2one", "librefleet.service.type")
    _expect_field(f, m, "technician_ids", "many2many", "res.users")
    _expect_field(f, m, "line_ids", "one2many", "librefleet.service.order.line")
    _expect_field(f, m, "stage", "selection")
    _expect_field(f, m, "scheduled_start", "datetime")
    _expect_field(f, m, "scheduled_end", "datetime")


def part_and_line_shape(env):
    f = _model_fields(env, "librefleet.part")
    for name, ttype in [("name", "char"), ("code", "char"),
                        ("standard_cost", "float"), ("list_price", "float")]:
        _expect_field(f, "librefleet.part", name, ttype)
    m = "librefleet.service.order.line"
    f = _model_fields(env, m)
    _expect_field(f, m, "order_id", "many2one", "librefleet.service.order", required=True)
    _expect_field(f, m, "part_id", "many2one", "librefleet.part")
    _expect_field(f, m, "qty", "float")
    _expect_field(f, m, "price_unit", "float")


def new_models_have_acls(env):
    for model in ("librefleet.service.order", "librefleet.service.order.line", "librefleet.part"):
        n = env.call("ir.model.access", "search_count", [("model_id.model", "=", model)])
        assert n >= 2, "found %d access rules for %s, expected one per group" % (n, model)


def order_record_rules(env):
    rules = env.call("ir.rule", "search_count",
                     [("model_id.model", "=", "librefleet.service.order")])
    assert rules >= 2, ("found %d record rules on service orders, expected the "
                        "technician rule AND the manager all-access rule" % rules)


def technician_rule_enforced(env):
    tina_env = Env(env.url, env.db, "tina", "technician")
    tina_env.login()
    uid = tina_env.uid
    mine = tina_env.call("librefleet.service.order", "search",
                         [("technician_ids", "in", [uid])])
    others = tina_env.call("librefleet.service.order", "search",
                           [("technician_ids", "not in", [uid])])
    assert mine, "no service order assigned to tina; create the ch12 demo orders"
    assert others, "no service order WITHOUT tina; create the ch12 demo orders"
    tina_env.call("librefleet.service.order", "write", mine[:1], {"stage": "confirmed"})
    tina_env.call("librefleet.service.order", "write", mine[:1], {"stage": "draft"})
    try:
        tina_env.call("librefleet.service.order", "write", others[:1], {"stage": "confirmed"})
    except xmlrpc.client.Fault:
        return
    raise AssertionError("tina could write a service order she is not assigned to; "
                         "is the technician record rule active?")


def _close(a, b):
    return abs(a - b) < 0.005


def line_subtotal_computed(env):
    f = _model_fields(env, "librefleet.service.order.line")
    _expect_field(f, "librefleet.service.order.line", "subtotal", "float")
    lines = env.call("librefleet.service.order.line", "search_read", [],
                     fields=["qty", "price_unit", "subtotal"])
    assert lines, "no order lines in the database; keep the ch12 demo data around"
    for l in lines:
        assert _close(l["subtotal"], l["qty"] * l["price_unit"]), (
            "line %d: subtotal %s != qty %s * price_unit %s"
            % (l["id"], l["subtotal"], l["qty"], l["price_unit"]))


def order_totals_computed(env):
    orders = env.call("librefleet.service.order", "search_read", [],
                      fields=["parts_total", "labor_total", "margin",
                              "service_type_id", "line_ids"])
    assert orders, "no service orders in the database"
    for o in orders:
        lines = env.call("librefleet.service.order.line", "search_read",
                         [("order_id", "=", o["id"])],
                         fields=["subtotal", "qty", "part_id"])
        parts = sum(l["subtotal"] for l in lines)
        assert _close(o["parts_total"], parts), (
            "order %d: parts_total %s, expected %s (sum of line subtotals)"
            % (o["id"], o["parts_total"], parts))
        fee = 0.0
        if o["service_type_id"]:
            fee = env.call("librefleet.service.type", "read",
                           [o["service_type_id"][0]], ["flat_fee"])[0]["flat_fee"]
        assert _close(o["labor_total"], fee), (
            "order %d: labor_total %s, expected the service type's flat fee %s"
            % (o["id"], o["labor_total"], fee))
        cost = 0.0
        for l in lines:
            if l["part_id"]:
                std = env.call("librefleet.part", "read",
                               [l["part_id"][0]], ["standard_cost"])[0]["standard_cost"]
                cost += l["qty"] * std
        assert _close(o["margin"], parts + fee - cost), (
            "order %d: margin %s, expected parts+labor-cost = %s"
            % (o["id"], o["margin"], parts + fee - cost))


def customer_follows_owner(env):
    f = _model_fields(env, "librefleet.service.order")
    _expect_field(f, "librefleet.service.order", "customer_id", "many2one", "res.partner")
    stored = env.call("ir.model.fields", "search_read",
                      [("model", "=", "librefleet.service.order"), ("name", "=", "customer_id")],
                      fields=["store", "related"])[0]
    assert stored["related"] == "vehicle_id.owner_id", (
        "customer_id related is %r, expected 'vehicle_id.owner_id'" % stored["related"])
    assert stored["store"], "customer_id must be stored (store=True) per the blueprint"
    orders = env.call("librefleet.service.order", "search_read", [],
                      fields=["customer_id", "vehicle_id"])
    for o in orders:
        owner = env.call("librefleet.vehicle", "read",
                         [o["vehicle_id"][0]], ["owner_id"])[0]["owner_id"]
        assert (o["customer_id"] or False) == (owner or False) or \
               (o["customer_id"] and owner and o["customer_id"][0] == owner[0]), (
            "order %d: customer_id %s but the vehicle's owner is %s"
            % (o["id"], o["customer_id"], owner))


def totals_not_stored(env):
    rows = {r["name"]: r for r in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.service.order"),
         ("name", "in", ["parts_total", "labor_total", "margin"])],
        fields=["name", "store"])}
    for name in ("parts_total", "labor_total", "margin"):
        assert name in rows, "%s must exist on librefleet.service.order" % name
    # Only these two are asserted non-stored. margin's store flag is deliberately
    # NOT checked here: ch19 turns it into a stored field so it can be used as a
    # kanban/graph measure, and this check must keep passing after that.
    for name in ("parts_total", "labor_total"):
        assert not rows[name]["store"], (
            "%s is stored; the chapter keeps these totals non-stored (compare "
            "with line subtotal)" % name)


def vehicle_service_count(env):
    vehicles = env.call("librefleet.vehicle", "search_read", [],
                        fields=["service_count"])
    assert vehicles, "no vehicles in the database"
    for v in vehicles:
        n = env.call("librefleet.service.order", "search_count",
                     [("vehicle_id", "=", v["id"])])
        assert v["service_count"] == n, (
            "vehicle %d: service_count is %s but it has %d orders"
            % (v["id"], v["service_count"], n))


def _expect_fault(fn, msg):
    """Assert that an RPC call is refused by the server (constraint fired)."""
    try:
        fn()
    except xmlrpc.client.Fault:
        return
    raise AssertionError(msg)


def vehicle_plate_unique(env):
    cons = env.call("ir.model.constraint", "search_read",
                    [("model.model", "=", "librefleet.vehicle"), ("type", "=", "u")],
                    fields=["definition"])
    assert any("license_plate" in (c.get("definition") or "") for c in cons), (
        "no UNIQUE database constraint covering license_plate on librefleet.vehicle")


def vehicle_year_constrained(env):
    _expect_fault(
        lambda: env.call("librefleet.vehicle", "create",
                         {"license_plate": "ODOOLINGS-YR", "year": 1850}),
        "a vehicle with model year 1850 was accepted; the @api.constrains on year is "
        "missing or too loose")


def order_reference_from_sequence(env):
    assert env.call("ir.sequence", "search_count",
                    [("code", "=", "librefleet.service.order")]), \
        "no ir.sequence with code 'librefleet.service.order' (check data/ir_sequence.xml)"
    orders = env.call("librefleet.service.order", "search_read", [],
                      fields=["reference"])
    assert orders, "no service orders in the database"
    for o in orders:
        ref = o["reference"]
        assert ref and ref != "New", (
            "order %d still has reference %r; backfill legacy orders from the sequence"
            % (o["id"], ref))


def order_no_overlap(env):
    booked = env.call("librefleet.service.order", "search_read",
                      [("scheduled_start", "!=", False),
                       ("scheduled_end", "!=", False),
                       ("stage", "!=", "cancelled")],
                      fields=["vehicle_id", "scheduled_start", "scheduled_end"],
                      limit=1)
    assert booked, "need one scheduled, non-cancelled order to test overlap; keep the demo data"
    b = booked[0]
    _expect_fault(
        lambda: env.call("librefleet.service.order", "create",
                         {"vehicle_id": b["vehicle_id"][0],
                          "scheduled_start": b["scheduled_start"],
                          "scheduled_end": b["scheduled_end"]}),
        "a booking overlapping an existing one on the same vehicle was accepted; "
        "the @api.constrains overlap check is missing")


def reference_drawn_at_save(env):
    d = env.call("librefleet.service.order", "default_get", ["reference"])
    assert d.get("reference") == "New", (
        "default_get returns %r; the field default should be the plain string "
        "'New', with next_by_code moved into create()" % d.get("reference"))


def batch_create_draws_numbers(env):
    vehicles = env.call("librefleet.vehicle", "search", [], limit=2)
    assert len(vehicles) >= 2, "need at least two vehicles in the database"
    ids = env.call("librefleet.service.order", "create", [
        {"vehicle_id": vehicles[0], "scheduled_start": "2030-01-01 08:00:00",
         "scheduled_end": "2030-01-01 09:00:00"},
        {"vehicle_id": vehicles[1], "scheduled_start": "2030-01-01 08:00:00",
         "scheduled_end": "2030-01-01 09:00:00"},
    ])
    try:
        refs = [o["reference"] for o in env.call(
            "librefleet.service.order", "read", ids, fields=["reference"])]
        assert all(r.startswith("SO/") for r in refs), (
            "batch-created orders got references %r; each vals dict should get "
            "its own sequence number in create()" % refs)
        assert len(set(refs)) == len(refs), (
            "batch-created orders share a reference (%r); draw one number per "
            "entry of vals_list" % refs)
    finally:
        env.call("librefleet.service.order", "unlink", ids)


def shell_batch_vehicle_state(env):
    v = env.call("librefleet.vehicle", "search_read",
                 [("license_plate", "=", "SHELL-001")], fields=["notes", "active"])
    assert v, ("no vehicle SHELL-001; run the batch create from the hands-on, "
               "and env.cr.commit() before leaving the shell")
    assert v[0]["notes"] == "Checked in bulk from the shell", (
        "SHELL-001 notes is %r; the single multi-record write() should have set it"
        % v[0]["notes"])


def shell_archived_vehicle(env):
    visible = env.call("librefleet.vehicle", "search_count",
                       [("license_plate", "=", "SHELL-002")])
    assert not visible, ("SHELL-002 shows up in a normal search; it should be "
                         "archived (active = False), which hides it by default")
    hidden = env.call("librefleet.vehicle", "search_count",
                      [("license_plate", "=", "SHELL-002")],
                      context={"active_test": False})
    assert hidden == 1, ("SHELL-002 not found even with active_test=False; was it "
                         "unlinked instead of archived?")


def shell_unlinked_vehicle(env):
    n = env.call("librefleet.vehicle", "search_count",
                 [("license_plate", "=", "SHELL-003")],
                 context={"active_test": False})
    assert n == 0, "SHELL-003 still exists; archiving is not deleting, unlink() it"

# ------------------------------------------------------------ boss2 checks --

def garage_installed(env):
    mods = env.call("ir.module.module", "search_read",
                    [("name", "=", "garage_inventory")],
                    fields=["state", "latest_version", "application"])
    assert mods, "no module named 'garage_inventory' known to this database"
    m = mods[0]
    assert m["state"] == "installed", "module state is %r, not 'installed'" % m["state"]
    assert m["application"], "'application' is not True in the manifest"
    assert (m["latest_version"] or "").startswith("19.0."), (
        "version is %r, expected 19.0.x.y.z" % m["latest_version"])


def garage_item_fields(env):
    fields_ = {f["name"]: f for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "garage.inventory.item")],
        fields=["name", "ttype", "required", "store"])}
    assert fields_, "no model 'garage.inventory.item' registered in this database"
    for name, ttype in {"name": "char", "code": "char", "qty_on_hand": "float",
                        "unit_cost": "float", "total_value": "float"}.items():
        assert name in fields_, "field %r is missing on garage.inventory.item" % name
        assert fields_[name]["ttype"] == ttype, (
            "field %r is %r, expected %r" % (name, fields_[name]["ttype"], ttype))
    for name in ("name", "code"):
        assert fields_[name]["required"], "%r is not required=True" % name
    assert fields_["total_value"]["store"], (
        "total_value is not stored; the spec asks for store=True so it can be "
        "summed and searched")


def garage_total_value_computes(env):
    ids = env.call("garage.inventory.item", "create",
                   [{"name": "Boss check pad", "code": "BOSS-CHK",
                     "qty_on_hand": 4, "unit_cost": 2.5}])
    try:
        val = env.call("garage.inventory.item", "read", ids, fields=["total_value"])[0]["total_value"]
        assert val == 10.0, "total_value is %s for qty 4 x cost 2.5, expected 10.0" % val
        env.call("garage.inventory.item", "write", ids, {"qty_on_hand": 6})
        val = env.call("garage.inventory.item", "read", ids, fields=["total_value"])[0]["total_value"]
        assert val == 15.0, ("total_value is %s after changing qty to 6, expected "
                             "15.0; check the @api.depends list" % val)
    finally:
        env.call("garage.inventory.item", "unlink", ids)


def garage_code_unique(env):
    ids = env.call("garage.inventory.item", "create",
                   [{"name": "Boss unique probe", "code": "BOSS-UNIQ"}])
    try:
        _expect_fault(
            lambda: env.call("garage.inventory.item", "create",
                             {"name": "Duplicate", "code": "BOSS-UNIQ"}),
            "two items with the same code were accepted; the spec requires a "
            "UNIQUE constraint on code")
    finally:
        env.call("garage.inventory.item", "unlink", ids)


def garage_qty_never_negative(env):
    _expect_fault(
        lambda: env.call("garage.inventory.item", "create",
                         {"name": "Anti-matter", "code": "BOSS-NEG",
                          "qty_on_hand": -1}),
        "an item with qty_on_hand = -1 was accepted; the spec requires a Python "
        "constraint refusing negative quantities")


def garage_group_and_acls(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "garage_inventory", "group_garage_stockkeeper")
    assert res and res[0] == "res.groups", (
        "garage_inventory.group_garage_stockkeeper does not resolve to a res.groups record")
    acls = env.call("ir.model.access", "search_read",
                    [("model_id.model", "=", "garage.inventory.item")],
                    fields=["group_id", "perm_read", "perm_write"])
    assert len(acls) >= 2, ("found %d access rules for garage.inventory.item, "
                            "expected at least 2 (stockkeeper + read-only internal users)" % len(acls))
    assert any(a["perm_read"] and not a["perm_write"] for a in acls), (
        "no read-only ACL found; internal users should read items but not change them")


def garage_menu_and_action(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "garage_inventory", "menu_garage_root")
    assert res[0] == "ir.ui.menu", "garage_inventory.menu_garage_root is not a menu"
    res = env.call("ir.model.data", "check_object_reference",
                   "garage_inventory", "action_garage_inventory_item")
    assert res[0] == "ir.actions.act_window", (
        "garage_inventory.action_garage_inventory_item is not a window action")
    act = env.call("ir.actions.act_window", "read", [res[1]],
                   ["res_model", "view_mode"])[0]
    assert act["res_model"] == "garage.inventory.item", (
        "the action opens %r, not garage.inventory.item" % act["res_model"])
    assert act["view_mode"] == "list,form", (
        "view_mode is %r, expected 'list,form'" % act["view_mode"])
    views = env.call("ir.ui.view", "search_read",
                     [("model", "=", "garage.inventory.item")], fields=["type"])
    types = {v["type"] for v in views}
    assert {"list", "form"} <= types, (
        "expected both a list and a form view for garage.inventory.item, found %s"
        % (sorted(types) or "none"))

def vehicle_form_extension_exists(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "view_librefleet_vehicle_form_reception")
    assert res[0] == "ir.ui.view", (
        "librefleet.view_librefleet_vehicle_form_reception is not an ir.ui.view")
    view = env.call("ir.ui.view", "read", [res[1]], ["inherit_id", "mode"])[0]
    assert view["inherit_id"], "the view has no inherit_id; it must extend the base form"
    assert view["mode"] == "extension", (
        "view mode is %r, expected 'extension' (set inherit_id and leave mode alone)"
        % view["mode"])


def vehicle_form_combined_arch(env):
    arch = env.call("librefleet.vehicle", "get_view", view_type="form")["arch"]
    assert 'name="active"' in arch, (
        "the combined form arch has no active field; is the xpath adding it "
        "after service_count?")
    assert "Odometer (km)" in arch, (
        "mileage_km is not relabeled to 'Odometer (km)'; use position=\"attributes\" "
        "with an <attribute name=\"string\"> node")


def reception_list_priority(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "view_librefleet_vehicle_list_reception")
    assert res[0] == "ir.ui.view", (
        "librefleet.view_librefleet_vehicle_list_reception is not an ir.ui.view")
    view = env.call("ir.ui.view", "read", [res[1]], ["priority", "inherit_id"])[0]
    assert not view["inherit_id"], (
        "the reception list must be a second standalone list view (no inherit_id), "
        "not an extension")
    assert view["priority"] == 99, (
        "priority is %s; the chapter ends with 99 so the original list stays the "
        "default" % view["priority"])


def default_list_unchanged(env):
    arch = env.call("librefleet.vehicle", "get_view", view_type="list")["arch"]
    assert "service_count" not in arch, (
        "the default list shows service_count, so the reception view won the "
        "priority contest; its priority must be higher (99) than the original's")
    assert "model_name" in arch, "the default list lost its model_name column"

def order_form_statusbar(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="form")["arch"]
    assert "<header>" in arch, "the order form has no <header>; the statusbar lives there"
    assert 'widget="statusbar"' in arch, "stage is not rendered with widget=\"statusbar\""
    assert "statusbar_visible" in arch, (
        "add statusbar_visible so cancelled stays hidden from the main path")


def order_form_notebook(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="form")["arch"]
    assert "<notebook>" in arch, "the order form has no <notebook>"
    assert '<page string="Parts"' in arch, "no Parts page in the notebook"
    parts_i = arch.index('<page string="Parts"')
    lines_i = arch.find('name="line_ids"')
    assert lines_i > parts_i, "line_ids should live inside the Parts page"


def order_list_polish(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="list")["arch"]
    assert "decoration-" in arch, (
        "the order list has no decoration-* attribute; grey out cancelled at least")
    assert 'widget="badge"' in arch, "stage is not shown as a badge in the list"
    assert "optional=" in arch, "make at least one column optional (optional=\"hide\")"


def vehicle_smart_button(env):
    arch = env.call("librefleet.vehicle", "get_view", view_type="form")["arch"]
    assert "oe_stat_button" in arch, "no smart button on the vehicle form"
    assert 'widget="statinfo"' in arch, "the button should show service_count via widget=\"statinfo\""
    assert 'name="web_ribbon"' in arch, "no Archived ribbon widget on the vehicle form"


def vehicle_button_action(env):
    vehicle = env.call("librefleet.vehicle", "search", [], limit=1)
    assert vehicle, "need at least one vehicle"
    act = env.call("librefleet.vehicle", "action_view_service_orders", vehicle)
    assert act.get("res_model") == "librefleet.service.order", (
        "the button method must return an act_window on librefleet.service.order")
    assert any("vehicle_id" in str(term) for term in act.get("domain", [])), (
        "the returned action's domain does not filter on vehicle_id")


def reception_anchor_moved(env):
    res = env.call("ir.model.data", "check_object_reference",
                   "librefleet", "view_librefleet_vehicle_form_reception")
    view = env.call("ir.ui.view", "read", [res[1]], ["arch_db"])[0]
    assert "service_count" not in view["arch_db"], (
        "the ch16 extension still anchors on service_count, which now lives inside "
        "the smart button; re-anchor the xpath (mileage_km works)")

def order_search_view_exists(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="search")["arch"]
    for name in ("my_services", "not_cancelled", "group_vehicle", "group_stage"):
        assert f'name="{name}"' in arch, (
            "the search view is missing a filter named %r" % name)


def order_my_services_filter_correct(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="search")["arch"]
    assert "[('technician_ids', 'in', [uid])]" in arch.replace('&quot;', "'"), (
        "the 'My Services' filter domain should be [('technician_ids', 'in', [uid])]; "
        "uid is the magic current-user variable the client evaluates")


def order_default_context_matches_filter(env):
    action_id = env.call("ir.model.data", "check_object_reference",
                         "librefleet", "action_librefleet_service_order")[1]
    ctx = env.call("ir.actions.act_window", "read", [action_id], ["context"])[0]["context"]
    import ast
    import re
    ctx_dict = ast.literal_eval(ctx)
    search_default_keys = [k for k in ctx_dict if k.startswith("search_default_")]
    assert search_default_keys, "the action has no search_default_* context key"
    # Read the filter names out of the view itself rather than hardcoding them, so
    # that filters the reader adds (the exercises do exactly that) still pass, and
    # so group-by filters count too: they are <filter> elements like any other.
    arch = env.call("librefleet.service.order", "get_view", view_type="search")["arch"]
    filter_names = set(re.findall(r'<filter[^>]*\bname="([^"]+)"', arch))
    assert filter_names, (
        "no <filter name=...> found in the search view arch; the default cannot "
        "match anything")
    for key in search_default_keys:
        name = key[len("search_default_"):]
        assert name in filter_names, (
            "action context key %r has no matching filter in the search view. "
            "Filters actually present: %s. The search_default_<name> suffix must be "
            "exact, or the default silently does nothing"
            % (key, ", ".join(sorted(filter_names))))


def order_group_by_vehicle_works(env):
    groups = env.call("librefleet.service.order", "read_group",
                      [], ["id"], ["vehicle_id"])
    assert len(groups) >= 2, "grouping by vehicle_id should produce at least 2 groups"

def order_kanban_calendar_pivot_graph_exist(env):
    for vtype in ("kanban", "calendar", "pivot", "graph"):
        arch = env.call("librefleet.service.order", "get_view", view_type=vtype)["arch"]
        assert arch, "no %s view found for librefleet.service.order" % vtype


def order_kanban_grouped_by_stage(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="kanban")["arch"]
    assert 'default_group_by="stage"' in arch, (
        "the kanban view should default_group_by=\"stage\" to give the pipeline")


def order_margin_is_stored_and_aggregatable(env):
    fields_ = env.call("ir.model.fields", "search_read",
                       [("model", "=", "librefleet.service.order"), ("name", "=", "margin")],
                       fields=["store"])
    assert fields_ and fields_[0]["store"], (
        "margin is not stored; a pivot/graph measure needs a real column to "
        "aggregate in SQL")
    groups = env.call("librefleet.service.order", "read_group", [], ["margin:sum"], ["vehicle_id"])
    assert groups, "read_group on margin:sum returned nothing"


def order_parts_labor_stay_non_stored(env):
    fields_ = {f["name"]: f for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.service.order"),
         ("name", "in", ["parts_total", "labor_total"])],
        fields=["name", "store"])}
    assert not fields_["parts_total"]["store"], (
        "parts_total got stored too; the chapter only promotes margin, to show "
        "storing is a deliberate per-field choice, not an all-or-nothing switch")
    assert not fields_["labor_total"]["store"]

def approve_wizard_is_transient(env):
    model = env.call("ir.model", "search_read",
                     [("model", "=", "librefleet.service.order.approve.wizard")],
                     fields=["transient"])
    assert model, "no model librefleet.service.order.approve.wizard registered"
    assert model[0]["transient"], (
        "the wizard model is not transient; inherit models.TransientModel, not "
        "models.Model")


def approve_wizard_button_returns_correct_action(env):
    order_id = env.call("librefleet.service.order", "search", [], limit=1)[0]
    act = env.call("librefleet.service.order", "action_open_approve_wizard", order_id)
    assert act.get("res_model") == "librefleet.service.order.approve.wizard", (
        "action_open_approve_wizard must open the approve wizard")
    assert act.get("target") == "new", (
        "the wizard action needs target=\"new\" to open as a popup, not a full page")
    assert act.get("context", {}).get("default_order_id") == order_id, (
        "the action's context must set default_order_id so the wizard's "
        "order_id field defaults to the order the button was clicked from")


def approve_wizard_blocks_wrong_stage(env):
    vehicle_id = env.call("librefleet.vehicle", "search", [], limit=1)[0]
    order_id = env.call("librefleet.service.order", "create", {
        "vehicle_id": vehicle_id, "stage": "draft",
        "scheduled_start": "2031-06-01 08:00:00", "scheduled_end": "2031-06-01 09:00:00"})
    try:
        wiz_id = env.call("librefleet.service.order.approve.wizard", "create",
                          {"order_id": order_id})
        _expect_fault(
            lambda: env.call("librefleet.service.order.approve.wizard", "action_confirm",
                             [wiz_id]),
            "the wizard let a draft order be marked done; check the stage guard "
            "in action_confirm")
    finally:
        env.call("librefleet.service.order", "unlink", [order_id])


def approve_wizard_blocks_negative_margin_without_override(env):
    vehicle_id = env.call("librefleet.vehicle", "search", [], limit=1)[0]
    part_id = env.call("librefleet.part", "search", [], limit=1)[0]
    order_id = env.call("librefleet.service.order", "create", {
        "vehicle_id": vehicle_id, "stage": "in_progress",
        "scheduled_start": "2031-06-02 08:00:00", "scheduled_end": "2031-06-02 09:00:00"})
    try:
        env.call("librefleet.service.order.line", "create", {
            "order_id": order_id, "part_id": part_id, "qty": 100, "price_unit": 0.0})
        margin = env.call("librefleet.service.order", "read",
                          [order_id], ["margin"])[0]["margin"]
        assert margin < 0, "fixture order should have a negative margin, got %s" % margin
        wiz_id = env.call("librefleet.service.order.approve.wizard", "create",
                          {"order_id": order_id})
        _expect_fault(
            lambda: env.call("librefleet.service.order.approve.wizard", "action_confirm",
                             [wiz_id]),
            "a negative-margin order was completed without the override; check "
            "the margin guard in action_confirm")
    finally:
        env.call("librefleet.service.order", "unlink", [order_id])

def vehicle_extended_in_place(env):
    """Classic _inherit adds to the SAME model and table, no new model."""
    fields_ = env.call("ir.model.fields", "search_count",
                       [("model", "=", "librefleet.vehicle"), ("name", "=", "is_loanable")])
    assert fields_, ("librefleet.vehicle has no is_loanable field; a classic "
                     "_inherit (no _name) adds fields to the existing model")
    assert not env.call("ir.model", "search_count",
                        [("model", "=", "librefleet.vehicle.loanable")]), (
        "a separate model was created; classic extension must not introduce a "
        "new _name")


def consumable_is_a_prototype_copy(env):
    assert env.call("ir.model", "search_count",
                    [("model", "=", "librefleet.consumable")]), (
        "no librefleet.consumable model; use _inherit plus a new _name")
    names = {f["name"] for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.consumable")], fields=["name"])}
    for copied in ("name", "code", "standard_cost", "list_price"):
        assert copied in names, (
            "librefleet.consumable is missing %r, which prototype inheritance "
            "should have copied from librefleet.part" % copied)
    assert "unit" in names, "librefleet.consumable should add its own unit field"
    part_names = {f["name"] for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.part")], fields=["name"])}
    assert "unit" not in part_names, (
        "librefleet.part gained a unit field; a prototype copies FROM the "
        "parent and must not add anything back to it")


def loaner_delegates_to_vehicle(env):
    models_ = env.call("ir.model", "search_read",
                       [("model", "=", "librefleet.loaner")], fields=["id"])
    assert models_, "no librefleet.loaner model"
    names = {f["name"] for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.loaner")], fields=["name"])}
    assert "vehicle_id" in names, "librefleet.loaner needs the delegation many2one"
    # _inherits registers the parent's fields on the child as NON-STORED related
    # fields pointing through the delegate; the column stays on the parent table.
    plate = env.call("ir.model.fields", "search_read",
                     [("model", "=", "librefleet.loaner"),
                      ("name", "=", "license_plate")],
                     fields=["related", "store"])
    assert plate, ("license_plate is not reachable from librefleet.loaner; "
                   "_inherits should expose the parent's fields")
    assert plate[0]["related"] == "vehicle_id.license_plate", (
        "license_plate on the loaner is related to %r, expected "
        "'vehicle_id.license_plate'" % plate[0]["related"])
    assert not plate[0]["store"], (
        "license_plate is stored on librefleet.loaner; with _inherits it must "
        "stay on the parent table and be reached through the delegate")


def loaner_creates_and_reads_through(env):
    """A loaner IS a vehicle: creating one creates the vehicle row too."""
    before = env.call("librefleet.vehicle", "search_count", [])
    loaner_id = env.call("librefleet.loaner", "create",
                         {"license_plate": "ODOOLINGS-LOAN", "daily_rate": 12.0})
    try:
        after = env.call("librefleet.vehicle", "search_count", [])
        assert after == before + 1, (
            "creating a loaner did not create a backing vehicle row (%d -> %d)"
            % (before, after))
        rec = env.call("librefleet.loaner", "read", [loaner_id],
                       fields=["license_plate", "vehicle_id"])[0]
        assert rec["license_plate"] == "ODOOLINGS-LOAN", (
            "the parent's license_plate is not readable through the loaner")
    finally:
        # deleting the loaner leaves its vehicle behind (the cascade only runs
        # parent -> child), so remove the backing vehicle explicitly
        vehicle = env.call("librefleet.loaner", "read", [loaner_id],
                           fields=["vehicle_id"])[0]["vehicle_id"]
        env.call("librefleet.loaner", "unlink", [loaner_id])
        if vehicle:
            env.call("librefleet.vehicle", "unlink", [vehicle[0]])


# --- ch32: extending core apps ----------------------------------------------

def product_dependency_declared(env):
    """Extending product.template requires "product" in the manifest depends."""
    installed = env.call("ir.module.module", "search_count",
                         [("name", "=", "product"), ("state", "=", "installed")])
    assert installed, (
        "the product module is not installed; add it to librefleet's depends, "
        "which is what pulls it in")


def partner_extended_in_place(env):
    """res.partner gains our fields without a new model appearing."""
    fields_ = {f["name"]: f for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "res.partner"), ("name", "like", "librefleet%")],
        fields=["name", "ttype"])}
    assert "librefleet_vehicle_ids" in fields_, (
        "res.partner has no librefleet_vehicle_ids; add it with a class using "
        "_inherit = \"res.partner\" and no _name")
    assert fields_["librefleet_vehicle_ids"]["ttype"] == "one2many", (
        "librefleet_vehicle_ids should be a One2many back to librefleet.vehicle "
        "through its owner_id field")
    assert "librefleet_vehicle_count" in fields_, (
        "res.partner has no librefleet_vehicle_count; add a computed Integer")
    assert not env.call("ir.model", "search_count",
                        [("model", "=", "res.partner.librefleet")]), (
        "a separate model appeared; extending core means _inherit with NO _name")


def partner_fields_are_namespaced(env):
    """Fields added to core models must be prefixed to avoid collisions."""
    bare = env.call("ir.model.fields", "search_read",
                    [("model", "=", "res.partner"), ("name", "in",
                     ["vehicle_ids", "vehicle_count"])], fields=["name"])
    assert not bare, (
        "found un-prefixed %s on res.partner; name fields you add to core "
        "models librefleet_* so they cannot collide with core or another module"
        % ", ".join(f["name"] for f in bare))


def partner_form_extended_not_replaced(env):
    """Our view must be an extension of base's form, never a replacement."""
    views = env.call("ir.ui.view", "search_read",
                     [("model", "=", "res.partner"), ("mode", "=", "extension"),
                      ("arch_db", "like", "action_librefleet_vehicles")],
                     fields=["name", "mode"])
    assert views, (
        "no extension view on res.partner adds the vehicles smart button; set "
        "inherit_id to base.view_partner_form and add nodes, do not copy the form")


def partner_vehicle_count_computes(env):
    """The computed count reflects vehicles actually owned by the partner."""
    partner_id = env.call("res.partner", "create", {"name": "ODOOLINGS-OWNER"})
    vehicle_ids = []
    try:
        for plate in ("ODOOLINGS-P1", "ODOOLINGS-P2"):
            vehicle_ids.append(env.call("librefleet.vehicle", "create",
                                        {"license_plate": plate,
                                         "owner_id": partner_id}))
        count = env.call("res.partner", "read", [partner_id],
                         fields=["librefleet_vehicle_count"])[0][
                             "librefleet_vehicle_count"]
        assert count == 2, (
            "librefleet_vehicle_count read %r for a partner owning 2 vehicles; "
            "@api.depends should track librefleet_vehicle_ids" % count)
    finally:
        if vehicle_ids:
            env.call("librefleet.vehicle", "unlink", vehicle_ids)
        env.call("res.partner", "unlink", [partner_id])


def part_bridges_to_product(env):
    """librefleet.part can point at a real catalogue product."""
    field = env.call("ir.model.fields", "search_read",
                     [("model", "=", "librefleet.part"), ("name", "=", "product_id")],
                     fields=["ttype", "relation"])
    assert field, (
        "librefleet.part has no product_id; add a Many2one to product.product "
        "so a shelved part can be linked to the catalogue")
    assert field[0]["ttype"] == "many2one", "product_id should be a Many2one"
    assert field[0]["relation"] == "product.product", (
        "product_id points at %r; it should relate to product.product"
        % field[0]["relation"])


def product_template_flag_reaches_variants(env):
    """A field added to product.template is readable on product.product.

    Not because we declared it twice: product.product uses delegation
    (_inherits) on product.template, so ch31's mechanism hands it over as a
    non-stored related field. The column exists only on the template.
    """
    tmpl = env.call("ir.model.fields", "search_read",
                    [("model", "=", "product.template"),
                     ("name", "=", "librefleet_is_part")], fields=["store"])
    assert tmpl, (
        "product.template has no librefleet_is_part; extend it with "
        "_inherit = \"product.template\"")
    assert tmpl[0]["store"], (
        "librefleet_is_part should be a real stored column on product.template")
    variant = env.call("ir.model.fields", "search_read",
                       [("model", "=", "product.product"),
                        ("name", "=", "librefleet_is_part")], fields=["store"])
    assert variant, (
        "librefleet_is_part is not visible on product.product; if it is missing "
        "you declared it somewhere other than product.template")
    assert not variant[0]["store"], (
        "librefleet_is_part is STORED on product.product, so it was declared "
        "there directly; let delegation expose the template's field instead")



# --- ch33: mail & chatter -----------------------------------------------------

def order_has_mail_mixins(env):
    """mail.thread and mail.activity.mixin bring their own fields with them."""
    names = {f["name"] for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.service.order")], fields=["name"])}
    for field, mixin in (("message_ids", "mail.thread"),
                         ("message_follower_ids", "mail.thread"),
                         ("activity_ids", "mail.activity.mixin")):
        assert field in names, (
            "librefleet.service.order has no %s, so %s is not inherited. Add both "
            "mixins with the LIST form: _inherit = [\"mail.thread\", "
            "\"mail.activity.mixin\"], keeping _name." % (field, mixin))


def order_tracks_the_right_fields(env):
    """tracking=True is what fills the chatter with an audit trail."""
    tracked = {f["name"] for f in env.call(
        "ir.model.fields", "search_read",
        [("model", "=", "librefleet.service.order"), ("tracking", "!=", False)],
        fields=["name"])}
    for field in ("stage", "customer_id"):
        assert field in tracked, (
            "%s is not tracked; add tracking=True so a change posts a message with "
            "before/after values in the chatter" % field)


def order_form_has_chatter(env):
    arch = env.call("librefleet.service.order", "get_view", view_type="form")["arch"]
    assert "<chatter" in arch, (
        "the order form has no <chatter/>. In Odoo 19 that single tag renders the "
        "thread, the followers and the activity scheduler; put it after </sheet>.")


def service_done_mail_template_exists(env):
    tmpl = env.call("mail.template", "search_read",
                    [("model", "=", "librefleet.service.order")],
                    fields=["name", "subject", "partner_to"])
    assert tmpl, (
        "no mail.template targets librefleet.service.order; add one in "
        "data/mail_template.xml and register it in the manifest")
    t = tmpl[0]
    assert "{{" in (t["subject"] or ""), (
        "the template subject has no {{ }} placeholder, so every customer gets an "
        "identical subject line")
    assert "{{" in (t["partner_to"] or ""), (
        "partner_to should resolve the recipient dynamically, e.g. "
        "{{ object.customer_id.id }}")


def order_tracking_actually_posts(env):
    """A tracked change posts a message, but only once the transaction commits."""
    order_id = env.call("librefleet.service.order", "search", [], limit=1)[0]
    before = env.call("librefleet.service.order", "read", [order_id],
                      fields=["stage", "message_ids"])[0]
    original = before["stage"]
    new_stage = "confirmed" if original != "confirmed" else "draft"
    try:
        env.call("librefleet.service.order", "write", [order_id], {"stage": new_stage})
        after = env.call("librefleet.service.order", "read", [order_id],
                         fields=["message_ids"])[0]["message_ids"]
        assert len(after) > len(before["message_ids"]), (
            "changing a tracked field posted no message. Over RPC each call is its "
            "own transaction, so tracking should have been finalized already")
        msg = env.call("mail.message", "read", [after[0]],
                       fields=["tracking_value_ids"])[0]
        assert msg["tracking_value_ids"], (
            "the message carries no tracking values, so the field change was not "
            "recorded as before/after")
    finally:
        env.call("librefleet.service.order", "write", [order_id], {"stage": original})
        msgs = env.call("librefleet.service.order", "read", [order_id],
                        fields=["message_ids"])[0]["message_ids"]
        if msgs:
            env.call("mail.message", "unlink", msgs)


# --- ch34: data files -------------------------------------------------------

def service_type_master_data_shipped(env):
    """Tire Rotation ships as noupdate master data, not a manual UI entry."""
    rows = env.call("librefleet.service.type", "search_read",
                    [("name", "=", "Tire Rotation")],
                    fields=["flat_fee", "default_duration_h"])
    assert rows, ("no Tire Rotation service type found; add "
                  "data/service_type_master.xml and register it in the manifest")
    assert rows[0]["flat_fee"] == 59.0, (
        "Tire Rotation's flat_fee is %s, not 59.0. If you tried bumping it to test "
        "noupdate, that is expected right after the edit and BEFORE upgrading, "
        "but the shipped, upgraded value should read 59.0 again" % rows[0]["flat_fee"])


def service_type_second_noupdate_record_was_added(env):
    """A record with no existing xml id is still created on a later upgrade."""
    rows = env.call("librefleet.service.type", "search_read",
                    [("name", "=", "Wheel Alignment")], fields=["flat_fee"])
    assert rows, (
        "no Wheel Alignment service type found. noupdate protects records that "
        "already exist, it does not block new ones: add a second <record> to the "
        "same noupdate block and upgrade again, it will be created normally")
    assert rows[0]["flat_fee"] == 45.0, (
        "Wheel Alignment's flat_fee is %s, not 45.0" % rows[0]["flat_fee"])


def demo_partner_exists(env):
    rows = env.call("res.partner", "search_read",
                    [("name", "=", "Nora Baumann")], fields=["id"])
    assert rows, (
        "no partner named Nora Baumann. Remember demo data only loads with "
        "--with-demo on a database that does not have librefleet installed yet, "
        "your real tutorial database will not show this")


def demo_vehicle_owned_by_demo_partner(env):
    v = env.call("librefleet.vehicle", "search_read",
                [("license_plate", "=", "AG 12 345")],
                fields=["model_name", "year", "owner_id"])
    assert v, "no vehicle AG 12 345 found (see data/librefleet.vehicle-demo.csv)"
    assert v[0]["owner_id"], "AG 12 345 has no owner_id; check the CSV's owner_id:id column"
    owner = env.call("res.partner", "read", [v[0]["owner_id"][0]], fields=["name"])[0]
    assert owner["name"] == "Nora Baumann", (
        "AG 12 345's owner is %r, not Nora Baumann; owner_id:id must reference "
        "the same xml id res.partner-demo.csv gives her" % owner["name"])


def demo_service_order_links_vehicle_and_master_data(env):
    """The demo order's XML ref() reaches a CSV row AND a master-data record."""
    so = env.call("librefleet.service.order", "search_read",
                  [("reference", "!=", False)],
                  fields=["vehicle_id", "service_type_id"], limit=1)
    assert so, "no service order found; check data/service_order_demo.xml"
    vehicle = env.call("librefleet.vehicle", "read", [so[0]["vehicle_id"][0]],
                       fields=["license_plate"])[0]
    assert vehicle["license_plate"] == "AG 12 345", (
        "the demo order's vehicle_id ref does not resolve to AG 12 345")
    stype = env.call("librefleet.service.type", "read", [so[0]["service_type_id"][0]],
                     fields=["name"])[0]
    assert stype["name"] == "Tire Rotation", (
        "the demo order's service_type_id ref does not resolve to Tire Rotation, "
        "the master-data record from earlier in this chapter")


# --- ch21: the business spine -------------------------------------------------
# Parts 4-5 run against a separate demo database, so every check here takes
# --db. They verify business state the reader produced, not module structure.

FUNCTIONAL_APPS = ("sale_management", "purchase", "stock", "mrp", "crm", "account")


def functional_db_has_the_apps(env):
    rows = env.call("ir.module.module", "search_read",
                    [("name", "in", list(FUNCTIONAL_APPS)), ("state", "=", "installed")],
                    fields=["name"])
    have = {r["name"] for r in rows}
    missing = set(FUNCTIONAL_APPS) - have
    assert not missing, (
        "these apps are not installed here: %s. This chapter runs in its own demo "
        "database, not your tutorial one. Create it with: odoo -d functional -i "
        "sale_management,purchase,stock,mrp,crm --with-demo --stop-after-init, then "
        "pass --db functional to odoolings." % ", ".join(sorted(missing)))


def functional_db_has_demo_data(env):
    assert env.call("res.partner", "search_count", [("is_company", "=", True)]) > 3, (
        "almost no companies here, so the database was built without demo data. "
        "Parts 4-5 need it (a chart of accounts, products, partners). Drop the "
        "database and recreate it with --with-demo.")


def brake_pad_template_exists(env):
    rows = env.call("product.template", "search_read",
                    [("name", "=", "Brake Pad Set")],
                    fields=["type", "list_price", "product_variant_count"])
    assert rows, ("no product template named exactly 'Brake Pad Set'. The hands-on "
                  "creates it in the Sales app under Products.")
    t = rows[0]
    assert t["type"] == "consu", (
        "'Brake Pad Set' has type %r; in Odoo 19 a physical part is 'consu' "
        "(labelled Goods). 'product' is not a type any more." % t["type"])


def brake_pad_generated_variants(env):
    tmpl = env.call("product.template", "search", [("name", "=", "Brake Pad Set")])
    variants = env.call("product.product", "search_read",
                        [("product_tmpl_id", "in", tmpl)],
                        fields=["display_name", "product_tmpl_id"])
    assert len(variants) >= 2, (
        "'Brake Pad Set' has %d variant(s). Add an attribute (Axle) with at least two "
        "values (Front, Rear) whose 'Variant Creation' mode is 'Instantly', and Odoo "
        "generates one product.product per combination." % len(variants))
    parents = {v["product_tmpl_id"][0] for v in variants}
    assert len(parents) == 1, (
        "those variants belong to %d different templates; they should all point back "
        "to the one 'Brake Pad Set' template" % len(parents))


def brake_pad_tracks_inventory(env):
    rows = env.call("product.template", "search_read",
                    [("name", "=", "Brake Pad Set")], fields=["is_storable"])
    assert rows[0]["is_storable"], (
        "'Brake Pad Set' does not track inventory. In Odoo 19 that is the separate "
        "'Track Inventory' boolean (is_storable, added by the Inventory app), not a "
        "product type. Tick it so chapter 25 can move these parts through stock.")


# --- ch22: sales, lead to confirmed order -------------------------------------
# Order numbers differ per reader (the sequence keeps counting), so nothing here
# matches on a name. Checks describe business state instead.

def _brake_pad_variants(env):
    return env.call("product.product", "search",
                    [("product_tmpl_id.name", "=", "Brake Pad Set")])


def crm_opportunity_exists(env):
    n = env.call("crm.lead", "search_count", [("type", "=", "opportunity")])
    assert n, ("no crm.lead has type 'opportunity'. Create a lead in the CRM app and "
               "convert it: lead and opportunity are the same model, and conversion "
               "just flips the 'type' field on the record you already had.")


def confirmed_order_for_the_brake_pads(env):
    variants = _brake_pad_variants(env)
    assert variants, ("no 'Brake Pad Set' variants exist. Chapter 21 created that "
                      "product; this chapter sells it.")
    lines = env.call("sale.order.line", "search_read",
                     [("product_id", "in", variants), ("product_uom_qty", "=", 4)],
                     fields=["order_id", "price_unit"])
    assert lines, ("no sales order line has 4 of a Brake Pad Set variant. The hands-on "
                   "quotes 4 of the Front variant.")
    states = env.call("sale.order", "search_read",
                      [("id", "in", [l["order_id"][0] for l in lines])],
                      fields=["name", "state", "invoice_status"])
    confirmed = [o for o in states if o["state"] == "sale"]
    assert confirmed, (
        "the order exists but its state is %r, not 'sale'. Press Confirm: that is the "
        "transition that turns a quotation into a sales order."
        % states[0]["state"])
    env._ch22_order = confirmed[0]


def confirming_created_a_delivery(env):
    order = getattr(env, "_ch22_order", None)
    assert order, "run the previous check first"
    oid = env.call("sale.order", "search", [("name", "=", order["name"])])
    picks = env.call("stock.picking", "search_read", [("sale_id", "in", oid)],
                     fields=["name", "state", "picking_type_code"])
    assert picks, (
        "the order is confirmed but has no delivery order. That picking is created by "
        "sale_stock's override of _action_confirm, so if it is missing, check that the "
        "line's product actually tracks inventory (chapter 21's is_storable).")
    assert any(p["picking_type_code"] == "outgoing" for p in picks), (
        "found pickings %s but none is outgoing; a customer delivery should be"
        % [p["name"] for p in picks])


def order_is_invoiceable_on_confirmation(env):
    order = getattr(env, "_ch22_order", None)
    assert order, "run the previous check first"
    assert order["invoice_status"] == "to invoice", (
        "invoice_status is %r. The Brake Pad Set keeps the default 'Ordered quantities' "
        "invoice policy, so confirming alone makes it invoiceable. A product set to "
        "'Delivered quantities' would read 'no' until the delivery is validated."
        % order["invoice_status"])


# Each chapter: list of (description, check_fn, hint shown on failure).
CHAPTERS = {
    "ch05": [
        ("Odoo server is reachable", server_up,
         "Is the dev environment running? In your workspace: docker compose up"),
        ("server version is 19.x", server_is_19,
         "The tutorial targets Odoo 19. Check the image tag in docker-compose.yml (image: odoo:19)."),
        ("can log in as admin", can_login,
         "Create a database (default name: tutorial) at http://localhost:8069 with admin/admin, "
         "or pass --db/--user/--password for yours."),
    ],
    "ch06": [
        ("can log in as admin", can_login,
         "Is the dev environment running with the tutorial database? See ch05."),
        ("the partner created from odoo shell exists", shell_partner_exists,
         "In the ch06 hands-on you create a contact named 'Ada Lovelace' from "
         "odoo shell. Did you run env.cr.commit() before quitting? Without it, "
         "shell writes are rolled back."),
    ],
    "ch08": [
        ("module librefleet is installed", librefleet_installed,
         "Is addons/librefleet in place with __manifest__.py and __init__.py? "
         "Install it: docker compose exec odoo odoo -c /etc/odoo/odoo.conf "
         "-d tutorial -i librefleet --stop-after-init"),
        ("manifest version is 19.0.x.y.z", librefleet_version_ok,
         "Set \"version\": \"19.0.1.0.0\" in __manifest__.py (Odoo major first, "
         "then your module's own version), then upgrade with -u librefleet."),
        ("LibreFleet is an app", librefleet_is_app,
         "Set \"application\": True in __manifest__.py and upgrade, so LibreFleet "
         "appears on the Apps home screen."),
    ],
    "ch09": [
        ("model librefleet.vehicle is registered", vehicle_model_exists,
         "Did you create models/vehicle.py with _name = 'librefleet.vehicle', "
         "import it from models/__init__.py AND the top-level __init__.py, then "
         "upgrade? New Python code needs -u librefleet --stop-after-init."),
        ("vehicle fields have the right types", vehicle_fields_typed,
         "Compare your field definitions with the chapter: license_plate/vin/"
         "model_name are Char, year is Integer, mileage_km is Float, notes is "
         "Text, active is Boolean. Upgrade after every change."),
        ("license_plate is required", vehicle_plate_required,
         "Add required=True to the license_plate field and upgrade."),
    ],
    "ch10": [
        ("Workshop User and Manager groups exist", workshop_groups_exist,
         "Define both res.groups records in security/librefleet_security.xml with "
         "ids group_librefleet_user and group_librefleet_manager, list the file in "
         "the manifest's data, and upgrade."),
        ("librefleet.vehicle has access rules", vehicle_acls_exist,
         "Add security/ir.model.access.csv with one line per group and list it in "
         "the manifest AFTER the security XML (the CSV references the groups)."),
        ("admin can read vehicles over XML-RPC", admin_reads_vehicles,
         "This failed in ch09 by design. It passes once the ACLs exist and admin "
         "is in the Workshop / Manager group (the users field on the group record)."),
        ("technician user 'tina' exists in Workshop / User", technician_exists_in_group,
         "Create the user from odoo shell as in the hands-on (login 'tina', "
         "group_ids includes librefleet.group_librefleet_user) and env.cr.commit()."),
    ],
    "ch11": [
        ("librefleet.service.type model with the right fields", service_type_fields_typed,
         "Create models/service_type.py (name Char required, flat_fee Float, "
         "default_duration_h Float), import it in models/__init__.py, upgrade."),
        ("service types have access rules", service_type_acls_exist,
         "Every new model needs its own lines in security/ir.model.access.csv "
         "(user read-only, manager full), or it stays invisible like ch09's vehicle."),
        ("vehicle window action exists with view_mode list,form", vehicle_action_exists,
         "Define ir.actions.act_window with id action_librefleet_vehicle, "
         "res_model librefleet.vehicle and view_mode list,form in views/vehicle_views.xml."),
        ("LibreFleet root menu exists", root_menu_exists,
         "Add <menuitem id=\"menu_librefleet_root\" .../> in views/librefleet_menus.xml "
         "and list the file in the manifest (after the views it references)."),
        ("vehicle list and form views defined", vehicle_views_exist,
         "Add both <list> and <form> views for librefleet.vehicle in "
         "views/vehicle_views.xml. On Odoo 19 the list tag is <list>, not <tree>."),
        ("Configuration menu is manager-only", config_menu_manager_only,
         "Put groups=\"group_librefleet_manager\" on the Configuration <menuitem> "
         "(id menu_librefleet_config) so technicians don't see it."),
    ],
    "ch12": [
        ("vehicle has owner_id and service_order_ids", vehicle_relations,
         "owner_id is Many2one('res.partner'); service_order_ids is "
         "One2many('librefleet.service.order', 'vehicle_id'), the inverse of the "
         "order's vehicle_id."),
        ("service order model has the right shape", order_model_shape,
         "Check models/service_order.py against the chapter: vehicle_id required "
         "Many2one, service_type_id Many2one, technician_ids Many2many to "
         "res.users, line_ids One2many, stage Selection, scheduled_start/end "
         "Datetime. Upgrade after each change."),
        ("part and order line models have the right shape", part_and_line_shape,
         "librefleet.part: name/code Char, standard_cost/list_price Float. "
         "Order line: order_id required Many2one, part_id Many2one, qty and "
         "price_unit Float."),
        ("the three new models have access rules", new_models_have_acls,
         "Every model needs its lines in security/ir.model.access.csv, one per "
         "group, or it is invisible (chapter 9 taught you how that looks)."),
        ("service orders have record rules", order_record_rules,
         "Two ir.rule records in security/librefleet_security.xml: the technician "
         "write-own-orders rule for Workshop / User AND the [(1,'=',1)] rule for "
         "Workshop / Manager (without it, managers get caught by the user rule)."),
        ("technicians can only write their own orders", technician_rule_enforced,
         "Log tina's work: she must be in technician_ids of at least one demo "
         "order and absent from another. Writing hers succeeds, writing the other "
         "must raise AccessError. Check the rule's domain and perm_write."),
    ],
    "ch13": [
        ("line subtotals are computed and stored", line_subtotal_computed,
         "subtotal = fields.Float(compute='_compute_subtotal', store=True) with "
         "@api.depends('qty', 'price_unit'). Did you upgrade after adding it?"),
        ("order totals add up (parts, labor, margin)", order_totals_computed,
         "parts_total sums line subtotals, labor_total mirrors the service type's "
         "flat_fee, margin = parts + labor - what the parts cost you. Check your "
         "@api.depends paths: dotted ones like 'line_ids.subtotal' are allowed "
         "and required."),
        ("order totals are NOT stored", totals_not_stored,
         "Leave store off the three order totals: they are cheap to compute and "
         "this chapter wants you to see the difference in psql."),
        ("customer_id is a stored related field that follows the owner",
         customer_follows_owner,
         "customer_id = fields.Many2one(related='vehicle_id.owner_id', "
         "store=True). Stored related fields update automatically when the "
         "source changes; if yours lags, check the related= path."),
        ("vehicle.service_count matches reality", vehicle_service_count,
         "service_count is a non-stored computed Integer: for each record, "
         "len(rec.service_order_ids). Remember to loop over self in the compute."),
    ],
    "ch14": [
        ("license_plate has a UNIQUE database constraint", vehicle_plate_unique,
         "Add _license_plate_unique = models.Constraint('unique(license_plate)', "
         "'...') on librefleet.vehicle (Odoo 19 replaced _sql_constraints with "
         "models.Constraint). Upgrade after adding it."),
        ("vehicle rejects an out-of-range model year", vehicle_year_constrained,
         "Add an @api.constrains('year') method that raises ValidationError when "
         "year is outside a sane range (e.g. 1900..next year). Constrains run in "
         "Python on create/write, so they fire over RPC too."),
        ("service orders get a reference from the sequence", order_reference_from_sequence,
         "Define the ir.sequence (data/ir_sequence.xml, code "
         "'librefleet.service.order') and give reference a default that calls "
         "next_by_code. Backfill any legacy orders still reading 'New'."),
        ("overlapping bookings on the same vehicle are refused", order_no_overlap,
         "Add an @api.constrains('scheduled_start','scheduled_end','vehicle_id') "
         "that searches for another non-cancelled order on the same vehicle whose "
         "window overlaps (start < other_end AND end > other_start)."),
    ],
    "ch15": [
        ("the order number is drawn at save time, not in the default", reference_drawn_at_save,
         "Set default=\"New\" on the reference field and move next_by_code into an "
         "@api.model_create_multi create() override. Upgrade AND restart: new "
         "Python only loads on restart."),
        ("a batch create draws one distinct number per order", batch_create_draws_numbers,
         "Under @api.model_create_multi, create() receives a LIST of vals dicts. "
         "Loop over vals_list and draw a number for each before calling super()."),
        ("SHELL-001 exists with the bulk-write note", shell_batch_vehicle_state,
         "Create the three SHELL vehicles in one create([...]) call, set the note "
         "on all three with one write(), and env.cr.commit() before quitting."),
        ("SHELL-002 is archived, not deleted", shell_archived_vehicle,
         "Set active = False on SHELL-002. A plain search must not find it; "
         "with_context(active_test=False) must."),
        ("SHELL-003 is gone for good", shell_unlinked_vehicle,
         "unlink() SHELL-003 and commit. If it still turns up under "
         "active_test=False, you archived instead of deleting."),
    ],
    "ch16": [
        ("the reception form extension exists and is an extension view", vehicle_form_extension_exists,
         "Create views/vehicle_views_inherit.xml with a record whose inherit_id "
         "refs view_librefleet_vehicle_form, list the file in the manifest, upgrade."),
        ("the combined form arch contains your changes", vehicle_form_combined_arch,
         "Two edits: xpath after service_count adding <field name=\"active\"/>, and "
         "position=\"attributes\" on mileage_km setting string to 'Odometer (km)'."),
        ("the reception list exists, standalone, priority 99", reception_list_priority,
         "A second <list> view for the same model with <field name=\"priority\" "
         "eval=\"99\"/>, no inherit_id."),
        ("the original list is still the default", default_list_unchanged,
         "Lowest priority wins the default slot. The original has priority 16; "
         "keep the reception list at 99 after the experiment."),
    ],
    "ch17": [
        ("the order form has a clickable statusbar in a header", order_form_statusbar,
         "Add <header> before <sheet> with stage as widget=\"statusbar\", "
         "options clickable, statusbar_visible=\"draft,confirmed,in_progress,done\"."),
        ("parts and notes moved into a notebook", order_form_notebook,
         "Wrap the lines and notes in <notebook><page string=\"Parts\">... with "
         "line_ids inside the Parts page."),
        ("the order list is decorated", order_list_polish,
         "decoration-muted for cancelled (and friends), stage as widget=\"badge\", "
         "and at least one optional column."),
        ("the vehicle form has the services smart button + ribbon", vehicle_smart_button,
         "A button_box div with an oe_stat_button showing service_count "
         "(widget=\"statinfo\"), plus the web_ribbon widget for archived vehicles."),
        ("the smart button opens this vehicle's orders", vehicle_button_action,
         "action_view_service_orders on the vehicle model: ensure_one, then return "
         "an act_window dict with a domain on vehicle_id."),
        ("the ch16 extension was re-anchored", reception_anchor_moved,
         "Moving service_count into the button changed what the old xpath matches. "
         "Anchor the active field on mileage_km instead, and upgrade."),
    ],
    "ch18": [
        ("the search view has the expected filters", order_search_view_exists,
         "Add <filter> elements named my_services, not_cancelled, group_vehicle, "
         "group_stage to a new search view for librefleet.service.order."),
        ("the My Services filter domain is correct", order_my_services_filter_correct,
         "domain=\"[('technician_ids', 'in', [uid])]\"; uid is evaluated client-side "
         "as the logged-in user's id."),
        ("the action's default filter matches a real filter name", order_default_context_matches_filter,
         "Every search_default_<name> key in the action's context must match a "
         "filter's name= exactly, or nothing happens, silently, forever."),
        ("grouping by vehicle_id works", order_group_by_vehicle_works,
         "read_group with groupby=['vehicle_id'] should return one group per vehicle "
         "that has orders."),
    ],
    "ch19": [
        ("kanban, calendar, pivot and graph views exist", order_kanban_calendar_pivot_graph_exist,
         "Add one ir.ui.view record per type (kanban/calendar/pivot/graph) for "
         "librefleet.service.order and list them all in the action's view_mode."),
        ("the kanban is grouped into the pipeline by default", order_kanban_grouped_by_stage,
         "Set default_group_by=\"stage\" on the <kanban> root element."),
        ("margin is stored and aggregatable", order_margin_is_stored_and_aggregatable,
         "Add store=True to the margin field and upgrade; read_group cannot "
         "aggregate a non-stored computed field, it has no SQL column to sum."),
        ("parts_total and labor_total stay non-stored", order_parts_labor_stay_non_stored,
         "Only margin needed to become a pivot/graph measure; leave the other "
         "two computed fields as chapter 13 built them."),
    ],
    "ch20": [
        ("the approve wizard is a TransientModel", approve_wizard_is_transient,
         "class ServiceOrderApproveWizard(models.TransientModel), not models.Model."),
        ("the Mark Done button opens the wizard correctly", approve_wizard_button_returns_correct_action,
         "action_open_approve_wizard should return an act_window dict with "
         "target=\"new\" and context={\"default_order_id\": self.id}."),
        ("the wizard refuses to complete a non in_progress order", approve_wizard_blocks_wrong_stage,
         "raise UserError in action_confirm when order.stage != \"in_progress\"."),
        ("the wizard refuses a negative-margin order without the override", approve_wizard_blocks_negative_margin_without_override,
         "raise UserError when order.margin < 0 and not "
         "self.override_negative_margin."),
    ],
    "ch21": [
        ("the functional database has the Part 4-5 apps", functional_db_has_the_apps,
         "Build it once: odoo -d functional -i sale_management,purchase,stock,mrp,crm "
         "--with-demo --stop-after-init. Then: odoolings.py check ch21 --db functional"),
        ("it was built with demo data", functional_db_has_demo_data,
         "Odoo 19 installs WITHOUT demo unless you pass --with-demo, and that flag only "
         "works on a fresh database. Chapter 34 explains why an upgrade cannot add it."),
        ("a 'Brake Pad Set' template exists, typed as Goods", brake_pad_template_exists,
         "Sales > Products > New. Odoo 19's product types are Goods, Service and Combo."),
        ("it generated at least two variants from one template", brake_pad_generated_variants,
         "Add an Axle attribute with Front and Rear. One template, one product.product "
         "per attribute combination: that is the whole template/variant split."),
        ("it tracks inventory", brake_pad_tracks_inventory,
         "Tick 'Track Inventory' (is_storable). It is a boolean the Inventory app adds, "
         "separate from the product type."),
    ],
    "ch22": [
        ("a lead was converted to an opportunity", crm_opportunity_exists,
         "CRM > New, then use Convert to Opportunity. Same record, same model: only "
         "the 'type' field changes."),
        ("a quotation for 4 brake pads was confirmed", confirmed_order_for_the_brake_pads,
         "Sales > Orders > Quotations > New, add 4 of Brake Pad Set (Front), then Confirm."),
        ("confirming created an outgoing delivery", confirming_created_a_delivery,
         "The delivery is a side effect of confirmation, added by sale_stock, not by "
         "sale itself. Read its two-line _action_confirm override."),
        ("the order became invoiceable", order_is_invoiceable_on_confirmation,
         "invoice_status is driven by the product's invoice policy, not by the order."),
    ],
    "ch31": [
        ("classic _inherit extended the vehicle in place", vehicle_extended_in_place,
         "Add is_loanable via a class with _inherit = \"librefleet.vehicle\" and "
         "NO _name, so it lands on the existing model and table."),
        ("librefleet.consumable is a prototype copy of the part", consumable_is_a_prototype_copy,
         "_inherit = \"librefleet.part\" plus _name = \"librefleet.consumable\" "
         "copies the parent's fields into a brand new model; add unit on top."),
        ("librefleet.loaner delegates to the vehicle", loaner_delegates_to_vehicle,
         "_inherits = {\"librefleet.vehicle\": \"vehicle_id\"} plus a required "
         "vehicle_id many2one with ondelete=\"cascade\"."),
        ("creating a loaner creates its vehicle and reads through", loaner_creates_and_reads_through,
         "With _inherits, create() on the child writes the parent row too, and "
         "the parent's fields are readable straight off the child."),
    ],
    "ch32": [
        ("the product dependency is declared and installed", product_dependency_declared,
         "Add \"product\" to depends in __manifest__.py, then upgrade. Extending a "
         "model you did not declare fails with \"does not exist in registry\"."),
        ("res.partner is extended in place", partner_extended_in_place,
         "_inherit = \"res.partner\" with NO _name, adding librefleet_vehicle_ids "
         "(One2many on owner_id) and a computed librefleet_vehicle_count."),
        ("fields added to core are namespaced", partner_fields_are_namespaced,
         "Prefix everything you add to a core model, librefleet_*, so it cannot "
         "collide with core or with another module extending the same model."),
        ("the core partner form is extended, not replaced", partner_form_extended_not_replaced,
         "inherit_id ref=\"base.view_partner_form\", then add the smart button "
         "inside <div name=\"button_box\"> with position=\"inside\"."),
        ("the vehicle count computes for a partner", partner_vehicle_count_computes,
         "@api.depends(\"librefleet_vehicle_ids\") and set the field with len() "
         "over the recordset."),
        ("librefleet.part bridges to a catalogue product", part_bridges_to_product,
         "Add product_id = fields.Many2one(\"product.product\") to librefleet.part."),
        ("the template flag reaches variants via delegation", product_template_flag_reaches_variants,
         "Declare librefleet_is_part on product.template ONLY. product.product "
         "_inherits the template, so ch31's delegation exposes it unstored."),
    ],
    "ch33": [
        ("the order inherits mail.thread and mail.activity.mixin", order_has_mail_mixins,
         "_inherit = [\"mail.thread\", \"mail.activity.mixin\"] alongside _name: the "
         "list form of _inherit pulls in mixins without renaming your model."),
        ("stage and customer are tracked", order_tracks_the_right_fields,
         "Add tracking=True to the fields worth an audit trail. Not every field: a "
         "chatter full of noise is a chatter nobody reads."),
        ("the order form renders a chatter", order_form_has_chatter,
         "Add <chatter/> after </sheet> in the form arch."),
        ("a mail template targets service orders", service_done_mail_template_exists,
         "data/mail_template.xml with a mail.template record, subject and partner_to "
         "using {{ }} placeholders, registered in the manifest data list."),
        ("a tracked change posts a message with before/after values", order_tracking_actually_posts,
         "tracking=True plus mail.thread does this for you. If it posts nothing, check "
         "the field really has tracking=True and that mail.thread is in _inherit."),
    ],
    "ch34": [
        ("Tire Rotation shipped as noupdate master data", service_type_master_data_shipped,
         "Add data/service_type_master.xml with a noupdate=\"1\" <record>, register "
         "it in the manifest's \"data\" list, then upgrade."),
        ("a second noupdate record was added on a later upgrade", service_type_second_noupdate_record_was_added,
         "Add a Wheel Alignment <record> to the same noupdate block as Tire Rotation "
         "and upgrade again: noupdate blocks re-writing existing records, not "
         "creating new ones."),
    ],
    "ch34-demo": [
        ("the demo partner exists", demo_partner_exists,
         "Run this against a SCRATCH database installed with --with-demo, e.g. "
         "python3 odoolings.py check ch34-demo --db tutorial_demo_check. Your real "
         "tutorial database never loads demo data, by design."),
        ("the demo vehicle is owned by the demo partner", demo_vehicle_owned_by_demo_partner,
         "In data/librefleet.vehicle-demo.csv, the owner_id:id column's value must "
         "be the exact xml id res.partner-demo.csv gives Nora Baumann."),
        ("the demo order's refs resolve to the vehicle and the master data", demo_service_order_links_vehicle_and_master_data,
         "data/service_order_demo.xml's vehicle_id and service_type_id use ref=, "
         "pointing at xml ids defined in other files of this same module."),
    ],
    "boss2": [
        ("garage_inventory is installed, an app, versioned 19.0.x", garage_installed,
         "Scaffold the module in addons/garage_inventory with the manifest keys "
         "from the spec, then install with -i garage_inventory."),
        ("garage.inventory.item has the spec's fields", garage_item_fields,
         "Check names, types, required flags, and store=True on total_value. "
         "Upgrade after every change."),
        ("total_value computes and recomputes", garage_total_value_computes,
         "total_value = qty_on_hand * unit_cost, computed with @api.depends on both "
         "fields and store=True. Chapter 13 has the pattern."),
        ("item codes are unique", garage_code_unique,
         "The spec wants a database-level guarantee. models.Constraint with "
         "unique(code), chapter 14 style."),
        ("negative stock is refused", garage_qty_never_negative,
         "@api.constrains('qty_on_hand') raising ValidationError. Remember to loop "
         "over self."),
        ("Stockkeeper group + ACLs are in place", garage_group_and_acls,
         "Group with XML id group_garage_stockkeeper, one full-CRUD ACL for it, one "
         "read-only ACL for base.group_user. Chapter 10 has the shape."),
        ("menu, action and both views exist", garage_menu_and_action,
         "XML ids menu_garage_root and action_garage_inventory_item, view_mode "
         "'list,form', plus a <list> and a <form> view. Chapter 11 has the shape."),
    ],
}


# ------------------------------------------------- snapshot / diff (ch21+) --
# "What did that button actually do?" You snapshot, click something in the UI,
# then diff. Built for Parts 4-5, where every chapter's job is to run a business
# flow and then read what it did to the database.
#
# Two deliberate limits, both stated rather than silent:
#   * Only the models below are watched. Odoo has ~900; watching all of them
#     would be slow and would bury the signal. Add a model here when a chapter
#     needs it.
#   * At most SNAPSHOT_LIMIT records per model are compared field by field.
#     Beyond that only the count is tracked, and the diff says so out loud.
#
# This is the one part of odoolings that touches the filesystem (a single JSON
# dotfile in the current directory). It still never reads the reader's module,
# so §4.5's "location-independent" contract holds: the tool works against any
# --url/--db from any directory.

SNAPSHOT_FILE = ".odoolings-snapshot.json"
SNAPSHOT_LIMIT = 800

# model -> fields worth showing when a record is created or changes.
WATCHED = {
    "crm.lead":          ["name", "stage_id", "probability"],
    "sale.order":        ["name", "state", "amount_untaxed", "amount_total", "invoice_status"],
    "sale.order.line":   ["product_id", "product_uom_qty", "price_unit", "discount"],
    "purchase.order":    ["name", "state", "amount_total"],
    "stock.picking":     ["name", "state", "picking_type_id"],
    "stock.move":        ["reference", "product_id", "product_uom_qty", "state"],
    "stock.quant":       ["product_id", "location_id", "quantity"],
    "mrp.production":    ["name", "state", "product_qty"],
    "account.move":      ["name", "move_type", "state", "amount_total", "payment_state"],
    "account.move.line": ["name", "account_id", "debit", "credit", "reconciled"],
    "account.payment":   ["state", "amount"],
    "product.template":  ["name", "list_price", "type"],
    # product.product matters as much as the template: generating variants is the
    # one thing a template does that you cannot see by watching templates alone.
    "product.product":   ["display_name", "default_code", "lst_price"],
    "product.pricelist": ["name"],
    "res.partner":       ["name"],
}


def _flatten(value):
    """XML-RPC gives many2one as [id, "Display Name"]. Keep the name only."""
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], int):
        value = value[1]
    if value is False:
        return None
    if isinstance(value, str):
        # Invoice-line names carry the whole product description, newlines and
        # all, which would wreck the one-record-per-line output.
        value = " ".join(value.split())
    return value


# Which field names the record best. Defaults to the first hit in _LABEL_ORDER,
# overridden where a different field is the actual point of the record (a stock
# move is about its product, not the picking reference it inherits).
_LABEL_ORDER = ("name", "reference", "product_id", "account_id")
_LABEL_OVERRIDE = {
    # A generated variant has no internal reference yet, so its display_name
    # ("Brake Pad Set (Rear)") is the only thing that identifies it usefully.
    "product.product": "display_name",
    "stock.move": "product_id",
    "stock.quant": "product_id",
    "sale.order.line": "product_id",
    "account.move.line": "name",
}


def _label(model, vals):
    """The most human thing we know about a record, on one line, bounded."""
    key = _LABEL_OVERRIDE.get(model)
    candidates = ([key] if key else []) + list(_LABEL_ORDER)
    for key in candidates:
        value = vals.get(key)
        # A draft invoice has no number yet, and Odoo stores that as "/".
        if value and str(value) != "/":
            text = str(value)
            return text if len(text) <= 40 else text[:37] + "..."
    return "id=%s" % vals.get("id")


def _detail(model, vals):
    """The remaining watched fields, so a new record shows what it was born with."""
    shown = _label(model, vals)
    bits = []
    for field in WATCHED.get(model, []):
        value = vals.get(field)
        if value in (None, "", 0, 0.0) or str(value) == shown:
            continue
        bits.append("%s=%s" % (field, value))
    return "  ".join(bits)


def take_snapshot(env):
    """Read every watched model's current state. Returns a plain dict."""
    installed = set(env.call("ir.model", "search_read", [], fields=["model"]) and
                    [m["model"] for m in env.call("ir.model", "search_read", [], fields=["model"])])
    state, skipped = {}, []
    for model, fields in sorted(WATCHED.items()):
        if model not in installed:
            continue  # app not installed in this database; not an error
        count = env.call(model, "search_count", [])
        entry = {"count": count, "records": {}, "truncated": count > SNAPSHOT_LIMIT}
        if entry["truncated"]:
            skipped.append("%s (%d records)" % (model, count))
        rows = env.call(model, "search_read", [], fields=fields + ["id"],
                        limit=SNAPSHOT_LIMIT, order="id desc")
        for row in rows:
            entry["records"][str(row["id"])] = {k: _flatten(v) for k, v in row.items()}
        state[model] = entry
    return state, skipped


def cmd_snapshot(env):
    state, skipped = take_snapshot(env)
    with open(SNAPSHOT_FILE, "w") as fh:
        json.dump({"db": env.db, "state": state}, fh)
    watched = len(state)
    total = sum(e["count"] for e in state.values())
    print("snapshot: %d models, %d records (database %r)" % (watched, total, env.db))
    if skipped:
        print("  count-only beyond %d records: %s" % (SNAPSHOT_LIMIT, ", ".join(skipped)))
    print("\nNow do something in the interface, then: odoolings.py diff"
          + ("" if env.db == "tutorial" else " --db %s" % env.db))
    return 0


def cmd_diff(env):
    try:
        with open(SNAPSHOT_FILE) as fh:
            saved = json.load(fh)
    except FileNotFoundError:
        print("No snapshot found. Run: odoolings.py snapshot"
              + ("" if env.db == "tutorial" else " --db %s" % env.db))
        return 2
    if saved.get("db") != env.db:
        print("Snapshot was taken against database %r, but you are pointing at %r."
              % (saved.get("db"), env.db))
        return 2

    before = saved["state"]
    after, _ = take_snapshot(env)
    any_change = False

    for model in sorted(set(before) | set(after)):
        old = before.get(model, {"count": 0, "records": {}, "truncated": False})
        new = after.get(model, {"count": 0, "records": {}, "truncated": False})
        delta = new["count"] - old["count"]
        added = [i for i in new["records"] if i not in old["records"]]
        removed = [i for i in old["records"] if i not in new["records"]]
        changed = []
        for rid, vals in new["records"].items():
            if rid in old["records"]:
                for field, value in vals.items():
                    if field == "id":
                        continue
                    was = old["records"][rid].get(field)
                    if was != value:
                        changed.append((rid, vals, field, was, value))
        if not (delta or added or removed or changed):
            continue

        any_change = True
        sign = "+%d" % delta if delta > 0 else str(delta) if delta else "~"
        note = "" if not new["truncated"] else "   (count-only: over %d records)" % SNAPSHOT_LIMIT
        print("%-19s %s%s" % (model, sign, note))
        for rid in sorted(added, key=int):
            vals = new["records"][rid]
            print("      new   %-24s %s" % (_label(model, vals), _detail(model, vals)))
        for rid in sorted(removed, key=int):
            print("      gone  %s" % _label(model, old["records"][rid]))
        for rid, vals, field, was, value in changed:
            print("      chg   %-24s %s: %s -> %s"
                  % (_label(model, vals), field, was, value))

    if not any_change:
        print("Nothing changed in the watched models.")
        print("If you expected a change, the model may not be in WATCHED "
              "(see the list at the top of this section).")
    return 0


def cmd_check(env, chapter):
    checks = CHAPTERS.get(chapter)
    if checks is None:
        print("Unknown chapter %r. Chapters with checks: %s" % (chapter, ", ".join(sorted(CHAPTERS))))
        return 2
    for desc, fn, hint in checks:
        try:
            fn(env)
        except Exception as e:
            # server Faults carry a full traceback; the last line is the point
            msg = e.faultString.strip().splitlines()[-1] if isinstance(e, xmlrpc.client.Fault) else e
            print("✘ %s" % desc)
            print("    %s" % msg)
            print("    hint: %s" % hint)
            return 1
        print("✔ %s" % desc)
    print("\n%s complete! On to the next chapter 🔧" % chapter)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="odoolings", description=__doc__.split("\n")[0])
    p.add_argument("command", choices=["check", "list", "snapshot", "diff"])
    p.add_argument("chapter", nargs="?", help="e.g. ch05 (not needed by snapshot/diff)")
    p.add_argument("--url", default="http://localhost:8069")
    p.add_argument("--db", default="tutorial")
    p.add_argument("--user", default="admin")
    p.add_argument("--password", default="admin")
    a = p.parse_args(argv)

    if a.command == "list":
        for ch in sorted(CHAPTERS):
            print("%s  (%d checks)" % (ch, len(CHAPTERS[ch])))
        return 0
    env = Env(a.url, a.db, a.user, a.password)
    if a.command == "snapshot":
        return cmd_snapshot(env)
    if a.command == "diff":
        return cmd_diff(env)
    if not a.chapter:
        p.error("check needs a chapter, e.g.: odoolings.py check ch05")
    return cmd_check(env, a.chapter)


if __name__ == "__main__":
    sys.exit(main())
