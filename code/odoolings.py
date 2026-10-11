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
import ast
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
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
    # Round-trips through a real write to prove tina has it, restoring the
    # original stage afterward: this check must never leave a side effect on
    # state later chapters (ch35 on) depend on being in a specific stage.
    target = mine[:1]
    original_stage = tina_env.call(
        "librefleet.service.order", "read", target, fields=["stage"])[0]["stage"]
    probe_stage = "draft" if original_stage != "draft" else "confirmed"
    try:
        tina_env.call("librefleet.service.order", "write", target, {"stage": probe_stage})
    finally:
        tina_env.call("librefleet.service.order", "write", target, {"stage": original_stage})
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
        # only what this check posted: the reader's own chatter history stays
        ours = [m for m in msgs if m not in before["message_ids"]]
        if ours:
            env.call("mail.message", "unlink", ours)


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


def service_type_name_is_translatable(env):
    """translate=True on the field, which is what turns its column into jsonb."""
    rows = env.call("ir.model.fields", "search_read",
                    [("model", "=", "librefleet.service.type"), ("name", "=", "name")],
                    fields=["translate"])
    assert rows, "no 'name' field found on librefleet.service.type"
    assert rows[0]["translate"], (
        "librefleet.service.type.name is not translatable. Add translate=True to the "
        "field and upgrade; Odoo migrates the varchar column to jsonb for you")


def french_is_installed(env):
    """A second language has to be loaded before anything can be translated into it."""
    rows = env.call("res.lang", "search_read", [("code", "=", "fr_FR")],
                    fields=["active"])
    assert rows and rows[0]["active"], (
        "French is not installed. Run: odoo i18n loadlang -c /etc/odoo/odoo.conf "
        "-d tutorial -l fr  (pass the iso_code 'fr', not 'fr_FR', to avoid a "
        "spurious 'not found languages' warning)")


def tire_rotation_reads_in_french(env):
    """The imported .po actually landed: same record, two languages, one jsonb column."""
    en = env.call("librefleet.service.type", "search_read",
                  [("name", "=", "Tire Rotation")], fields=["name"],
                  context={"lang": "en_US"})
    assert en, "no Tire Rotation service type found (chapter 34, step 1)"
    fr = env.call("librefleet.service.type", "read", [en[0]["id"]],
                  fields=["name"], context={"lang": "fr_FR"})
    assert fr[0]["name"] == "Rotation des pneus", (
        "Tire Rotation reads as %r in French, expected 'Rotation des pneus'. Write "
        "i18n/fr.po with that msgstr and import it with odoo i18n import -l fr"
        % fr[0]["name"])


def base_automation_is_installed(env):
    """Automated Actions live in their own module, not in base."""
    mod = env.call("ir.module.module", "search_read",
                    [("name", "=", "base_automation")], fields=["state"])
    assert mod and mod[0]["state"] == "installed", (
        "base_automation is not installed. Add it to librefleet's depends and "
        "upgrade: Automated Actions are their own module, base does not carry them.")


def maintenance_reminder_cron_exists(env):
    """A cron is an ir.actions.server with a schedule bolted on: ir.cron inherits it."""
    rows = env.call("ir.cron", "search_read",
                     [("code", "like", "action_send_maintenance_reminders")],
                     fields=["active", "interval_number", "interval_type"])
    assert rows, (
        "no ir.cron calls action_send_maintenance_reminders(). ir.cron inherits "
        "ir.actions.server through ir_actions_server_id, so point a cron's "
        "ir_actions_server_id at that action rather than duplicating its code.")
    cron = rows[0]
    assert cron["active"], "the cron exists but is inactive"
    assert cron["interval_type"] == "days" and cron["interval_number"] == 1, (
        "expected a daily cron (interval_number=1, interval_type='days'), got %s %s"
        % (cron["interval_number"], cron["interval_type"]))


def reminder_action_is_bound_to_the_vehicle_list(env):
    """binding_model_id + binding_view_types is what puts an action in the list's Action menu."""
    rows = env.call("ir.actions.server", "search_read",
                     [("name", "=", "LibreFleet: maintenance reminders")],
                     fields=["binding_model_id", "binding_view_types", "state"])
    assert rows, "no server action named 'LibreFleet: maintenance reminders' found"
    action = rows[0]
    assert action["binding_model_id"], (
        "the action has no binding_model_id, so it never appears in the "
        "Vehicles list's Action menu, only under Settings > Technical > "
        "Server Actions")
    assert "list" in (action["binding_view_types"] or ""), (
        "binding_view_types does not include 'list'")
    assert action["state"] == "code", "the action's state should be 'code'"


def running_it_reminded_an_overdue_vehicle(env):
    """Proves the method actually ran, not just that the XML parsed cleanly."""
    rows = env.call("mail.activity", "search_read",
                     [("res_model", "=", "librefleet.vehicle"),
                      ("summary", "=", "Schedule maintenance")],
                     fields=["res_id", "user_id"])
    assert rows, (
        "no 'Schedule maintenance' activity exists on any vehicle. Run the cron "
        "by hand once: Settings > Technical > Scheduled Actions > 'LibreFleet: "
        "maintenance reminders' > Run Manually.")
    assert all(r["user_id"] for r in rows), (
        "a reminder activity has no user_id (Assigned to). activity_schedule() "
        "leaves that field empty unless you pass user_id explicitly, it does "
        "not default to whoever ran it.")


def finishing_an_order_cleared_its_vehicle_reminder(env):
    """The automated action's whole point: a finished service should retire its own reminder."""
    done_orders = env.call("librefleet.service.order", "search_read",
                            [("stage", "=", "done")], fields=["vehicle_id"])
    assert done_orders, (
        "no service order is stage='done' yet. Take one through the approve "
        "wizard (chapter 20's flow) so there is something for the automated "
        "action to react to.")
    vehicle_ids = [o["vehicle_id"][0] for o in done_orders]
    leftover = env.call("mail.activity", "search_count",
                         [("res_model", "=", "librefleet.vehicle"),
                          ("res_id", "in", vehicle_ids),
                          ("summary", "=", "Schedule maintenance")])
    assert leftover == 0, (
        "a vehicle with a done service order still has an open 'Schedule "
        "maintenance' activity. Check the base.automation's trigger: it should "
        "fire on_create_or_write with filter_pre_domain stage != 'done' and "
        "filter_domain stage = 'done', calling _clear_maintenance_reminder() "
        "on records.mapped('vehicle_id')")


def _service_report_action(env):
    res = env.call("ir.model.data", "check_object_reference",
                    "librefleet", "action_report_service_order")
    assert res and res[0] == "ir.actions.report", (
        "librefleet.action_report_service_order does not resolve to an "
        "ir.actions.report record")
    return env.call("ir.actions.report", "read", [res[1]],
                     fields=["model", "report_name", "report_type",
                             "binding_model_id", "binding_type"])[0]


def service_report_action_is_registered(env):
    """A report is a stored ir.actions.report record, same family as chapter 35's server actions."""
    action = _service_report_action(env)
    assert action["model"] == "librefleet.service.order", (
        "the report action's model is %r, expected librefleet.service.order"
        % action["model"])
    assert action["report_type"] == "qweb-pdf", (
        "report_type is %r, expected 'qweb-pdf'" % action["report_type"])
    assert action["report_name"] == "librefleet.report_service_order", (
        "report_name is %r, expected 'librefleet.report_service_order' (module."
        "template_id, not just the template id)" % action["report_name"])


def service_report_is_bound_to_the_print_menu(env):
    """binding_type='report' is what puts it in the form's Print dropdown, no button XML needed."""
    action = _service_report_action(env)
    assert action["binding_model_id"], (
        "the action has no binding_model_id, so it will never appear in a "
        "service order's Print menu")
    assert action["binding_type"] == "report", (
        "binding_type is %r, expected 'report' (chapter 35's server action "
        "used binding_type 'action', a report uses 'report')" % action["binding_type"])


def service_report_templates_exist(env):
    """Two templates, same shape as core's account.report_invoice: a wrapper and a document."""
    for name in ("report_service_order", "report_service_order_document"):
        res = env.call("ir.model.data", "check_object_reference", "librefleet", name)
        assert res and res[0] == "ir.ui.view", (
            "librefleet.%s does not resolve to an ir.ui.view (QWeb templates "
            "load as views)" % name)


def service_report_never_prints_the_margin(env):
    """margin is what the workshop earns; a document handed to the customer should never carry it."""
    res = env.call("ir.model.data", "check_object_reference",
                    "librefleet", "report_service_order_document")
    view = env.call("ir.ui.view", "read", [res[1]], fields=["arch_db"])[0]
    assert "o.margin" not in view["arch_db"], (
        "the service report template renders o.margin somewhere. That field is "
        "the workshop's profit, not something a customer-facing document should show")


def _http_get(env, path):
    req = urllib.request.Request(env.url + path, headers={"X-Odoo-Database": env.db})
    return urllib.request.urlopen(req, timeout=10)


def services_page_renders(env):
    """type='http', auth='public': no login, no XML-RPC, a plain unauthenticated GET."""
    try:
        resp = _http_get(env, "/librefleet/services")
    except urllib.error.HTTPError as exc:
        raise AssertionError(
            "GET /librefleet/services returned %s, expected 200. Check the route's "
            "auth level is \"public\" and the module is upgraded" % exc.code)
    body = resp.read().decode()
    assert "What we service" in body, (
        "the page loaded (200) but its content is missing; check the template "
        "librefleet.services_page")


def vehicle_lookup_endpoint_works(env):
    """type='jsonrpc': the envelope differs from type='http', not the auth story."""
    vehicles = env.call("librefleet.vehicle", "search_read", [], fields=["license_plate"], limit=1)
    assert vehicles, "no vehicle to look up; earlier chapters should have created one"
    payload = json.dumps({
        "jsonrpc": "2.0", "method": "call",
        "params": {"license_plate": vehicles[0]["license_plate"]},
    }).encode()
    req = urllib.request.Request(
        env.url + "/librefleet/vehicles/lookup", data=payload,
        headers={"Content-Type": "application/json", "X-Odoo-Database": env.db})
    try:
        body = json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as exc:
        raise AssertionError(
            "POST /librefleet/vehicles/lookup returned %s. Check the route uses "
            "type=\"jsonrpc\" (not the deprecated type=\"json\") and auth=\"public\"" % exc.code)
    assert body.get("result", {}).get("found") is True, (
        "the endpoint did not find a vehicle that definitely exists: %r" % body)


def service_order_has_portal_mixin(env):
    """portal.mixin's own default access_url is the literal string '#'; this model must override it."""
    orders = env.call("librefleet.service.order", "search_read", [], fields=["access_url"], limit=1)
    assert orders, "no service order to check"
    url = orders[0]["access_url"]
    assert url and url.startswith("/my/service-orders/"), (
        "access_url is %r. Add portal.mixin to the model's _inherit list and override "
        "_compute_access_url to point at /my/service-orders/<id>" % url)


def _portal_group_id(env):
    return env.call("ir.model.data", "check_object_reference", "base", "group_portal")[1]


def portal_access_is_read_only(env):
    """The ACL only grants read; the record rule (checked separately) is what scopes it to one customer."""
    rows = env.call("ir.model.access", "search_read",
                     [("model_id.model", "=", "librefleet.service.order"),
                      ("group_id", "=", _portal_group_id(env))],
                     fields=["perm_read", "perm_write", "perm_create", "perm_unlink"])
    assert rows, "no ir.model.access row grants base.group_portal access to librefleet.service.order"
    acl = rows[0]
    assert acl["perm_read"], "the portal ACL exists but does not grant read"
    assert not (acl["perm_write"] or acl["perm_create"] or acl["perm_unlink"]), (
        "the portal ACL grants more than read (%r); a customer should never be able "
        "to write, create or delete a service order over the portal" % acl)


def portal_record_rule_scopes_to_customer(env):
    """The ACL alone would let every portal user read every order; this is what stops that."""
    rules = env.call("ir.rule", "search_read",
                      [("model_id.model", "=", "librefleet.service.order"),
                       ("groups", "in", [_portal_group_id(env)])],
                      fields=["domain_force"])
    assert rules, ("no ir.rule scopes librefleet.service.order for base.group_portal; "
                    "without one, any portal user could read any customer's orders")
    assert "customer_id" in rules[0]["domain_force"], (
        "the portal record rule's domain is %r, expected it to filter on customer_id"
        % rules[0]["domain_force"])


_BUNDLE_CACHE = {}


def _backend_bundle(env):
    """Fetch the backend JS bundle once per run, always freshly built.

    OWL runs in the browser, so odoolings cannot execute a component. What it
    CAN do is read the bundle the browser would download and prove the code
    got compiled into it, which is what the manifest's "assets" key is for.

    The URL matters. Odoo caches each built bundle as an ir.attachment named
    after a content hash, and rebuilds ONLY when the web client asks for a
    hash it has not stored yet. Read that attachment and you may be grading a
    stale build (or, if the browser still has the good one cached, a build
    nobody is actually running). The 'debug' unique token skips the attachment
    lookup entirely and rebuilds from the manifest every time, which is the
    only reliably current answer. Note it serves the non-minified bundle, so
    the filename drops '.min'.
    """
    if env.db in _BUNDLE_CACHE:
        return _BUNDLE_CACHE[env.db]
    url = env.url + "/web/assets/debug/web.assets_web.js"
    last = None
    # Odoo watches the addons path and restarts itself when a file changes,
    # which kills whatever request was in flight. Editing a component then
    # immediately running this check reliably hits that, so retry once.
    for attempt in range(3):
        req = urllib.request.Request(url, headers={"X-Odoo-Database": env.db})
        try:
            body = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
            _BUNDLE_CACHE[env.db] = body
            return body
        except urllib.error.HTTPError as exc:
            raise AssertionError(
                "could not fetch the backend asset bundle (HTTP %s). Is the "
                "server running on %s?" % (exc.code, env.url))
        except Exception as exc:  # connection reset by the auto-reload restart
            last = exc
            time.sleep(2)
    raise AssertionError(
        "could not fetch the backend asset bundle after 3 tries (%s). If you "
        "just edited a file, Odoo's auto-reload may still be restarting; wait "
        "a moment and re-run" % last)


def workshop_clock_is_in_the_backend_bundle(env):
    """Proves the manifest's assets key is right: no entry, no code in the bundle."""
    bundle = _backend_bundle(env)
    assert "class WorkshopClock extends Component" in bundle, (
        "the WorkshopClock component is not in the backend bundle. Check the "
        "manifest has an \"assets\" key (a sibling of \"data\", NOT inside it) "
        "listing librefleet/static/src/**/*.js under \"web.assets_backend\", "
        "then upgrade the module")


def workshop_clock_template_is_registered(env):
    """The .xml has to be listed in the bundle too; JS alone renders nothing."""
    bundle = _backend_bundle(env)
    assert 'registerTemplate("librefleet.WorkshopClock"' in bundle, (
        "no template registered as \"librefleet.WorkshopClock\". Either the "
        "*.xml line is missing from the manifest's assets list, or the "
        "<t t-name=\"...\"> in workshop_clock.xml does not exactly match the "
        "static template = \"...\" in workshop_clock.js. A mismatch throws "
        "OwlError: Cannot find template, visible only in the browser console")


def workshop_clock_reads_open_orders_over_rpc(env):
    """The component's own domain, run here, so a wrong domain fails loudly."""
    bundle = _backend_bundle(env)
    assert "searchCount" in bundle and "librefleet.service.order" in bundle, (
        "the component does not call orm.searchCount on librefleet.service.order. "
        "useService(\"orm\") is how an OWL component reaches the ORM; a plain "
        "fetch() would bypass the session and the ORM's access rules")
    n = env.call("librefleet.service.order", "search_count",
                  [("stage", "not in", ["done", "cancelled"])])
    assert isinstance(n, int), "search_count did not return a number"


def _margin_field_descriptor(bundle):
    """Slice out just our own field descriptor.

    Bare substring checks are useless against a 9 MB bundle that contains all
    of core: "supportedTypes" alone appears ~67 times, once per built-in
    widget, so a check for it would pass even if OUR descriptor lacked it.
    """
    start = bundle.find("marginField = {")
    if start == -1:
        start = bundle.find("marginField =")
    assert start != -1, (
        "no marginField descriptor found in the bundle. A field widget needs "
        "an exported descriptor object, { component, supportedTypes, ... }, "
        "next to its component class")
    end = bundle.find("};", start)
    return bundle[start:end]


def margin_widget_is_registered(env):
    """A widget only exists once it is added to the "fields" registry under a name."""
    bundle = _backend_bundle(env)
    assert "class MarginField extends Component" in bundle, (
        "the MarginField component class is not in the bundle. Check the "
        "manifest's assets list includes librefleet/static/src/**/*.js")
    assert 'registry.category("fields").add("librefleet_margin"' in bundle, (
        "librefleet_margin is not registered in the fields registry. A widget "
        "class on its own is inert: it needs "
        'registry.category("fields").add("librefleet_margin", marginField). '
        "The string you register under is the same one the view's "
        'widget="..." attribute asks for')


def margin_widget_declares_supported_types(env):
    """supportedTypes is what makes Odoo refuse the widget on a Char field."""
    descriptor = _margin_field_descriptor(_backend_bundle(env))
    assert "supportedTypes" in descriptor, (
        "the marginField descriptor has no supportedTypes. Without it nothing "
        "stops someone putting widget=\"librefleet_margin\" on a Char field "
        "and getting nonsense; declare [\"float\", \"monetary\"]")
    assert "float" in descriptor, (
        "supportedTypes does not include \"float\", which is what "
        "librefleet.service.order.margin actually is")


def margin_widget_is_used_on_the_form(env):
    """The registry entry is half of it; the view has to ask for the widget by name."""
    res = env.call("ir.model.data", "check_object_reference",
                    "librefleet", "view_librefleet_service_order_form")
    view = env.call("ir.ui.view", "read", [res[1]], fields=["arch_db"])[0]
    assert 'widget="librefleet_margin"' in view["arch_db"], (
        "the service order form does not use the widget. Add "
        'widget="librefleet_margin" to the <field name="margin"/> in '
        "views/service_order_views.xml, then upgrade")


def form_controller_patch_is_scoped(env):
    """A patch is global: the resModel guard is the only thing keeping it off other apps."""
    bundle = _backend_bundle(env)
    assert "patch(FormController.prototype" in bundle, (
        "FormController.prototype is not patched. Import patch from "
        '"@web/core/utils/patch" and FormController from '
        '"@web/views/form/form_controller", then patch its prototype')
    assert "onWillSaveRecord" in bundle, (
        "the patch does not override onWillSaveRecord, the hook that runs "
        "before a form saves")
    assert 'record.resModel === "librefleet.service.order"' in bundle, (
        "the patch has no resModel guard. patch() applies to EVERY form view "
        "in the web client, for every model in every app, so the method body "
        "must check which model it is looking at before doing anything")


def _dashboard_component_source(bundle):
    """Slice out just the dashboard module's own source.

    Same lesson as chapter 40's descriptor slice: the bundle carries all of
    core, so a bare substring check proves nothing about the reader's file.
    """
    start = bundle.find("class LibreFleetDashboard")
    assert start != -1, (
        "no LibreFleetDashboard component found in the backend bundle. Check "
        "static/src/dashboard/dashboard.js exists and the manifest's assets "
        "glob picks it up")
    end = bundle.find('registry.category("actions")', start)
    return bundle[start:end if end != -1 else start + 4000]


def dashboard_client_action_exists(env):
    """ir.actions.client is the database half; its tag names the JS half."""
    res = env.call("ir.model.data", "check_object_reference",
                    "librefleet", "action_librefleet_dashboard")
    assert res and res[0] == "ir.actions.client", (
        "librefleet.action_librefleet_dashboard does not resolve to an "
        "ir.actions.client record")
    action = env.call("ir.actions.client", "read", [res[1]], fields=["tag", "name"])[0]
    assert action["tag"] == "librefleet_dashboard", (
        "the action's tag is %r, expected 'librefleet_dashboard'. The tag is "
        "the only link to the JavaScript: it is looked up in the \"actions\" "
        "registry" % action["tag"])


def dashboard_component_is_registered(env):
    """The tag has to exist on the JS side too, or the menu opens a blank screen."""
    bundle = _backend_bundle(env)
    assert 'registry.category("actions").add("librefleet_dashboard"' in bundle, (
        "no component registered in the \"actions\" registry under "
        "\"librefleet_dashboard\". The string here must match the tag on the "
        "ir.actions.client record exactly; a mismatch renders nothing and says "
        "nothing, in the server log or the browser console")


def dashboard_aggregates_server_side(env):
    """The point of the chapter: group in Postgres, not by fetching every record."""
    source = _dashboard_component_source(_backend_bundle(env))
    assert "formattedReadGroup" in source, (
        "the dashboard does not call orm.formattedReadGroup. Fetching every "
        "order with searchRead and counting them in JavaScript works on your "
        "two demo orders and falls over on a real fleet; grouping belongs in "
        "the database. (Odoo 19 renamed read_group to formatted_read_group, "
        "so there is no orm.readGroup to reach for.)")
    assert "technician_ids" in source, (
        "the dashboard does not group by technician_ids, which is what makes "
        "it a jobs-per-technician dashboard")


def dashboard_reuses_the_group_domain(env):
    """__domain comes back with each group; rebuilding it by hand is how counts drift."""
    source = _dashboard_component_source(_backend_bundle(env))
    assert "__domain" in source, (
        "the dashboard does not use each group's __domain. formattedReadGroup "
        "returns the exact domain that produced every group, so a drill-down "
        "can reuse it instead of rebuilding a domain by hand and risking a "
        "list that disagrees with the number the user just clicked")


def dashboard_open_orders_group_correctly(env):
    """Runs the component's own query here, so a wrong domain or groupby fails loudly."""
    domain = [("stage", "in", ["draft", "confirmed", "in_progress"])]
    groups = env.call("librefleet.service.order", "formatted_read_group",
                       domain=domain, groupby=["technician_ids"],
                       aggregates=["__count", "margin:sum"])
    assert groups, (
        "grouping open service orders by technician returned nothing. Assign "
        "at least one technician to an open order so the dashboard has "
        "something to show")
    named = [g for g in groups if g["technician_ids"]]
    assert named, (
        "every open order is unassigned, so the dashboard has no technician "
        "rows. Put a technician on at least one open order")


def point_of_sale_is_installed(env):
    mod = env.call("ir.module.module", "search_read",
                    [("name", "=", "point_of_sale")], fields=["state"])
    assert mod and mod[0]["state"] == "installed", (
        "point_of_sale is not installed. Settings > Apps > Point of Sale, "
        "or -i point_of_sale from the CLI.")


def website_sale_is_installed(env):
    mod = env.call("ir.module.module", "search_read",
                    [("name", "=", "website_sale")], fields=["state"])
    assert mod and mod[0]["state"] == "installed", (
        "website_sale is not installed. Settings > Apps > eCommerce, "
        "or -i website_sale from the CLI.")


def a_website_order_was_placed(env):
    """The functional proof for the eCommerce half: a real order, placed
    through the actual storefront, not created directly on the backend."""
    orders = env.call("sale.order", "search_read",
                       [("website_id", "!=", False)],
                       fields=["name", "amount_total"], limit=1, order="id desc")
    assert orders, (
        "no sale.order with a website_id found. Place a real order through "
        "http://localhost:8069/shop (Wire Transfer needs no external "
        "account; enable it first via payment.provider).")


def a_pos_session_was_closed(env):
    """The functional proof this chapter is really about: a real till, opened and closed."""
    sessions = env.call("pos.session", "search_read",
                         [("state", "=", "closed")],
                         fields=["name", "order_ids"], limit=1, order="id desc")
    assert sessions, (
        "no closed pos.session found. Open a register (Point of Sale > New "
        "Session), ring up at least one order, then close the register.")
    assert sessions[0]["order_ids"], (
        "the closed session has no orders. A session with nothing sold has "
        "nothing for the next check to verify.")


def session_move_is_posted_and_balanced(env):
    """Closing a session posts one consolidated journal entry, not one per order."""
    sessions = env.call("pos.session", "search_read",
                         [("state", "=", "closed"), ("move_id", "!=", False)],
                         fields=["move_id"], limit=1, order="id desc")
    assert sessions, (
        "no closed session has a move_id. Closing the register is what "
        "posts the session's consolidated journal entry; a session stuck at "
        "'closing control' has not finished that step.")
    move_id = sessions[0]["move_id"][0]
    move = env.call("account.move", "read", [move_id], fields=["state"])[0]
    assert move["state"] == "posted", (
        "the session's journal entry is %r, expected 'posted'" % move["state"])
    lines = env.call("account.move.line", "search_read",
                      [("move_id", "=", move_id)], fields=["debit", "credit"])
    debit = sum(l["debit"] for l in lines)
    credit = sum(l["credit"] for l in lines)
    assert abs(debit - credit) < 0.01, (
        "the session's journal entry does not balance: debit %.2f, credit "
        "%.2f" % (debit, credit))


def cash_count_matches_reality(env):
    """The gotcha: leaving Cash Count at its 0 default reports a fake shortfall."""
    sessions = env.call("pos.session", "search_read",
                         [("state", "=", "closed")],
                         fields=["cash_register_difference"], limit=1, order="id desc")
    assert sessions, "no closed session to check"
    diff = sessions[0]["cash_register_difference"]
    assert abs(diff) < 0.01, (
        "the most recently closed session has a cash difference of %.2f. "
        "The Closing Register screen's Cash Count field defaults to 0, not "
        "to what the drawer should hold, so leaving it untouched reports a "
        "fake shortfall for the entire opening float plus every cash sale. "
        "Count the drawer (or type the expected total) before closing." % diff)


def maintenance_reminder_module_is_installed(env):
    mod = env.call("ir.module.module", "search_read",
                    [("name", "=", "librefleet_maintenance_reminder")],
                    fields=["state"])
    assert mod and mod[0]["state"] == "installed", (
        "librefleet_maintenance_reminder is not installed. -i "
        "librefleet_maintenance_reminder from the CLI, after moving the code "
        "and data files out of librefleet.")


def librefleet_no_longer_depends_on_base_automation(env):
    mod = env.call("ir.module.module", "search_read",
                    [("name", "=", "librefleet")], fields=["dependencies_id"])
    assert mod, "librefleet is not installed"
    deps = env.call("ir.module.module.dependency", "read",
                     mod[0]["dependencies_id"], ["name"])
    dep_names = {d["name"] for d in deps}
    assert "base_automation" not in dep_names, (
        "librefleet's manifest still lists base_automation as a dependency. "
        "Nothing in librefleet's own code uses it anymore once the reminder "
        "logic moves to librefleet_maintenance_reminder, remove it from depends.")


# --- chapter 49: install and run an OCA module (functional db) ----------------

def _module_state(env, name):
    rows = env.call("ir.module.module", "search_read",
                     [("name", "=", name)], fields=["state", "latest_version"])
    return rows[0] if rows else None


def sale_fixed_discount_is_installed(env):
    mod = _module_state(env, "sale_fixed_discount")
    assert mod, (
        "Odoo has never even heard of sale_fixed_discount. That means the "
        "addons path does not reach it: check the `addons paths` line in "
        "`docker compose logs odoo` and remember the entry is the repository "
        "directory (/mnt/oca/sale-workflow), not its parent.")
    assert mod["state"] == "installed", (
        "sale_fixed_discount is on the addons path but its state is %r. "
        "Install it with -i sale_fixed_discount against the functional "
        "database." % mod["state"])


def fixed_discount_dependency_came_along(env):
    mod = _module_state(env, "account_invoice_fixed_discount")
    assert mod and mod["state"] == "installed", (
        "account_invoice_fixed_discount is not installed. It is "
        "sale_fixed_discount's dependency and it lives in a DIFFERENT "
        "repository, OCA/account-invoicing, so it needs its own clone and its "
        "own addons_path entry. You cannot install the first module without it.")


def sale_order_line_has_discount_fixed(env):
    fields = env.call("sale.order.line", "fields_get", [], ["type"])
    assert "discount_fixed" in fields, (
        "sale.order.line has no discount_fixed field, so the module's Python "
        "never loaded even though the module reports installed. Try -u "
        "sale_fixed_discount and read the log for an import error.")
    ttype = fields["discount_fixed"]["type"]
    assert ttype == "float", (
        "discount_fixed is a %s, expected float. If this fails you are "
        "probably looking at account.move.line's version of the field, which "
        "is monetary and comes from the other module." % ttype)


# --- chapter 50: five modules, five ways in (functional db) -------------------

CH50_MODULES = ("crm_lead_code", "product_secondary_unit", "auditlog",
                "web_responsive")


def ch50_modules_are_installed(env):
    rows = env.call("ir.module.module", "search_read",
                     [("name", "in", list(CH50_MODULES))], fields=["name", "state"])
    states = {r["name"]: r["state"] for r in rows}
    missing = [m for m in CH50_MODULES if states.get(m) != "installed"]
    assert not missing, (
        "not installed: %s. Each one needs its repository cloned into oca/ AND "
        "an addons_path entry of its own: crm_lead_code is in OCA/crm, "
        "product_secondary_unit in OCA/product-attribute, auditlog in "
        "OCA/server-tools, web_responsive in OCA/web."
        % ", ".join(missing))


def auto_install_bridge_arrived(env):
    rows = env.call("ir.module.module", "search_read",
                     [("name", "=", "sale_order_secondary_unit")],
                     fields=["state", "auto_install"])
    assert rows, (
        "sale_order_secondary_unit is not in the module list at all, so "
        "OCA/sale-workflow is not on your addons path. It is chapter 49's "
        "clone, keep it there.")
    assert rows[0]["state"] == "installed", (
        "sale_order_secondary_unit is %r, but it declares auto_install and "
        "both of its dependencies (sale, product_secondary_unit) should be "
        "installed by now. Install product_secondary_unit and it arrives on "
        "its own; you never name it." % rows[0]["state"])


def every_old_lead_got_a_code(env):
    total = env.call("crm.lead", "search_count", [])
    assert total, (
        "no leads at all in this database. Run this check against the "
        "functional database, the one Parts 4 and 5 built.")
    without = env.call("crm.lead", "search_count", [("code", "=", False)])
    assert without == 0, (
        "%d of %d leads have no code. The post_init_hook assigns codes to "
        "leads that already existed, so it only runs on install: if you "
        "upgraded (-u) rather than installed (-i), the hook never fired."
        % (without, total))


def product_secondary_unit_model_exists(env):
    rows = env.call("ir.model", "search_read",
                     [("model", "=", "product.secondary.unit")], fields=["name"])
    assert rows, (
        "product.secondary.unit does not exist. Unlike the other modules in "
        "this chapter, this one defines a brand new model with _name, so its "
        "absence means the module's Python never loaded.")


# --- chapter 51: changing an OCA module without forking it (functional db) ----

def _a_draft_sale_line(env):
    lines = env.call("sale.order.line", "search_read",
                      [("state", "=", "draft"), ("price_unit", ">", 0)],
                      fields=["price_unit", "discount_fixed"], limit=1)
    assert lines, (
        "no draft sale order line with a price in this database, so there is "
        "nothing to test the constraint against. Run this against the "
        "functional database.")
    return lines[0]


def discount_limit_module_installed(env):
    rows = env.call("ir.module.module", "search_read",
                     [("name", "=", "sale_fixed_discount_limit")],
                     fields=["state", "dependencies_id"])
    assert rows, (
        "sale_fixed_discount_limit is not in the module list, so Odoo cannot "
        "see addons/sale_fixed_discount_limit. Check the directory name and "
        "that it holds a __manifest__.py.")
    assert rows[0]["state"] == "installed", (
        "sale_fixed_discount_limit is %r. Install it with "
        "-i sale_fixed_discount_limit." % rows[0]["state"])
    deps = env.call("ir.module.module.dependency", "read",
                     rows[0]["dependencies_id"], ["name"])
    names = {d["name"] for d in deps}
    assert "sale_fixed_discount" in names, (
        "the manifest depends on %s, but not on sale_fixed_discount. That "
        "dependency is what guarantees discount_fixed exists before your "
        "constraint mentions it: depending on sale instead leaves load order "
        "to chance." % sorted(names))


def discount_above_unit_price_refused(env):
    line = _a_draft_sale_line(env)
    try:
        env.call("sale.order.line", "write", [line["id"]],
                 {"discount_fixed": line["price_unit"] * 2})
    except xmlrpc.client.Fault:
        return
    # The write went through, so put the line back before reporting: a failing
    # check should not leave the reader's data worse than it found it.
    env.call("sale.order.line", "write", [line["id"]],
             {"discount_fixed": line["discount_fixed"]})
    raise AssertionError(
        "a fixed discount of twice the unit price was accepted on line %d. "
        "Your @api.constrains is missing, or it compares the wrong two "
        "fields, or the module was not upgraded after you wrote it."
        % line["id"])


def refused_write_left_the_line_alone(env):
    line = env.call("sale.order.line", "read", [_a_draft_sale_line(env)["id"]],
                     ["discount_fixed"])[0]
    assert not line["discount_fixed"], (
        "line %d now carries discount_fixed = %s, so the refused write was "
        "applied in part before the constraint fired. A ValidationError has "
        "to abort the whole write, which it does when it is raised from "
        "@api.constrains rather than from an override that writes first."
        % (line["id"], line["discount_fixed"]))


def exactly_one_maintenance_automation(env):
    automations = env.call("base.automation", "search_read", [],
                            fields=["name"])
    reminder_automations = [a for a in automations
                             if a["name"] == "Clear the maintenance reminder "
                                              "when a service order is done"]
    assert len(reminder_automations) == 1, (
        "expected exactly one 'Clear the maintenance reminder...' automation, "
        "found %d. A leftover record from librefleet (before its data file was "
        "removed) alongside the new one in librefleet_maintenance_reminder "
        "would double-fire the automation; see this chapter's cleanup SQL." %
        len(reminder_automations))


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
    # Not pinned to 'to invoice': a reader who has since done chapter 28 will have
    # actually invoiced this same order, moving it to 'invoiced'. Either value
    # proves the point this check exists for, that confirming alone made it
    # invoiceable; only 'no' means confirmation never did.
    assert order["invoice_status"] in ("to invoice", "invoiced"), (
        "invoice_status is %r. The Brake Pad Set keeps the default 'Ordered quantities' "
        "invoice policy, so confirming alone makes it invoiceable. A product set to "
        "'Delivered quantities' would read 'no' until the delivery is validated."
        % order["invoice_status"])


# --- ch27: accounting foundations ---------------------------------------------
# The reader's work is one hand-written, balanced journal entry. Entry numbers
# come from a sequence, so nothing here matches on a name.

def _ch27_entry(env):
    """The reader's manual entry: a posted 'entry' move worth 250 in a general journal."""
    return env.call("account.move", "search",
                    [("move_type", "=", "entry"), ("state", "=", "posted"),
                     ("amount_total", "=", 250.0)])


def manual_journal_entry_posted(env):
    assert _ch27_entry(env), (
        "no posted journal entry of 250.00 found. The hands-on writes one by hand in the "
        "Miscellaneous journal: 250.00 debit to an equipment account, 250.00 credit to "
        "the bank account, then Post. A draft entry does not count, which is what the "
        "next checks are about.")


def manual_entry_is_balanced(env):
    # Check one move, not the set: a reader may well have written more than one
    # entry, and summing across moves would compare apples to several apples.
    ids = _ch27_entry(env)[:1]
    lines = env.call("account.move.line", "search_read", [("move_id", "in", ids)],
                     fields=["debit", "credit"])
    debit = round(sum(l["debit"] for l in lines), 2)
    credit = round(sum(l["credit"] for l in lines), 2)
    assert debit == credit == 250.0, (
        "the entry's debits total %.2f and its credits %.2f. Odoo refuses to post an "
        "unbalanced entry at all ('The entry is not balanced.'), so if you are reading "
        "this they balance but are not 250.00 each." % (debit, credit))


def manual_entry_got_its_number_on_posting(env):
    move = env.call("account.move", "read", _ch27_entry(env)[:1],
                    fields=["name"])[0]
    assert move["name"] and move["name"] != "/", (
        "the entry has no name, so it was never really posted. The sequence assigns the "
        "number at posting time, not at creation: a draft entry's name is False.")
    assert "/" in move["name"], (
        "the entry is named %r, which does not look like a journal sequence "
        "(MISC/2026/08/0001). Was it posted from the Miscellaneous journal?"
        % move["name"])


def an_invoice_is_the_same_model(env):
    """The chapter's whole point: invoices are account.move too."""
    kinds = {mt: env.call("account.move", "search_count", [("move_type", "=", mt)])
             for mt in ("entry", "out_invoice")}
    assert kinds["entry"] and kinds["out_invoice"], (
        "expected both plain journal entries and customer invoices here, found %r. Demo "
        "data ships the invoices; your hands-on adds the entry." % kinds)
    inv = env.call("account.move", "search_read",
                   [("move_type", "=", "out_invoice"), ("state", "=", "posted")],
                   fields=["name"], limit=1)
    assert inv, "no posted customer invoice found in the demo data"
    lines = env.call("account.move.line", "search_read",
                     [("move_id", "=", inv[0]["id"])], fields=["debit", "credit"])
    d = round(sum(l["debit"] for l in lines), 2)
    c = round(sum(l["credit"] for l in lines), 2)
    assert d == c and d > 0, (
        "invoice %s has debits %.2f and credits %.2f. Every account.move balances, "
        "invoices included: that is what makes them journal entries."
        % (inv[0]["name"], d, c))


# --- ch28: invoicing, payments, reconciliation --------------------------------

def _ch28_invoice(env):
    """The reader's invoice: posted, out_invoice, carrying tax, for the brake pads."""
    variants = env.call("product.product", "search",
                        [("product_tmpl_id.name", "=", "Brake Pad Set")])
    lines = env.call("account.move.line", "search_read",
                     [("product_id", "in", variants),
                      ("move_id.move_type", "=", "out_invoice"),
                      ("move_id.state", "=", "posted")],
                     fields=["move_id"])
    return sorted({l["move_id"][0] for l in lines})


def brake_pad_invoice_posted(env):
    ids = _ch28_invoice(env)
    assert ids, (
        "no posted customer invoice contains a Brake Pad Set line. Open the confirmed "
        "order from chapter 22 and use Create Invoice, then Confirm. Remember the "
        "invoice is created in draft: creating is not posting.")


def invoice_carries_a_tax_line(env):
    mid = _ch28_invoice(env)[0]
    lines = env.call("account.move.line", "search_read", [("move_id", "=", mid)],
                     fields=["name", "debit", "credit", "tax_line_id"])
    assert any(l["tax_line_id"] for l in lines), (
        "this invoice has no tax line. The demo products carry a 15% tax, so a posted "
        "invoice should have three lines: the product, the tax, and the receivable. "
        "Chapter 29 takes the tax apart.")
    debit = round(sum(l["debit"] for l in lines), 2)
    credit = round(sum(l["credit"] for l in lines), 2)
    assert debit == credit, (
        "the invoice's debits (%.2f) and credits (%.2f) differ, which should be "
        "impossible for a posted move" % (debit, credit))


def invoice_is_fully_paid(env):
    mid = _ch28_invoice(env)[0]
    mv = env.call("account.move", "read", [mid],
                  fields=["name", "payment_state", "amount_total", "amount_residual"])[0]
    assert mv["payment_state"] == "paid", (
        "invoice %s reads payment_state %r with %.2f still outstanding. Use Register "
        "Payment until nothing remains. Paying part of it leaves 'partial', which is "
        "the state the hands-on visits on the way."
        % (mv["name"], mv["payment_state"], mv["amount_residual"]))
    assert round(mv["amount_residual"], 2) == 0.0, (
        "payment_state says paid but %.2f is still residual" % mv["amount_residual"])


def receivable_line_is_reconciled(env):
    """Paid is a summary; reconciled on the receivable line is the mechanism."""
    mid = _ch28_invoice(env)[0]
    lines = env.call("account.move.line", "search_read",
                     [("move_id", "=", mid), ("debit", ">", 0)],
                     fields=["name", "reconciled", "account_id"])
    assert lines, "the invoice has no debit line, which should be impossible"
    assert all(l["reconciled"] for l in lines), (
        "the receivable line is not reconciled, even though the invoice looks paid. "
        "payment_state is a computed summary; the truth is the 'reconciled' flag on the "
        "line and the account.partial.reconcile records linking it to the payment.")


# --- ch23: pricing, pricelists, promotions -------------------------------------

def _ch23_front(env):
    return env.call("product.product", "search",
                    [("product_tmpl_id.name", "=", "Brake Pad Set")], limit=1)


def pricelists_feature_is_on(env):
    n = env.call("product.pricelist", "search_count", [])
    assert n, (
        "no product.pricelist records exist at all, which means the feature is still off. "
        "Pricelists are optional in Odoo 19: tick Settings > Sales > Pricelists and Odoo "
        "creates a Default pricelist per company.")


def two_rules_compete_on_one_pricelist(env):
    pls = env.call("product.pricelist", "search", [])
    items = env.call("product.pricelist.item", "search_read", [("pricelist_id", "in", pls)],
                     fields=["applied_on", "compute_price"])
    assert len(items) >= 2, (
        "found %d pricelist rule(s); the hands-on adds two so they can compete: a global "
        "percentage and a variant-specific fixed price." % len(items))
    kinds = {i["applied_on"] for i in items}
    assert "3_global" in kinds and "0_product_variant" in kinds, (
        "the rules present are %s. You need one '3_global' and one '0_product_variant' to "
        "see resolution order, because those numeric prefixes ARE the specificity order."
        % sorted(kinds))


def specific_rule_beats_global(env):
    """The whole point: a 79.00 product is quoted at the 60.00 variant rule.

    Checks the rule AND its effect. product.pricelist._get_product_price is
    private and RPC refuses it (the boundary chapter 28 meets with
    _create_invoices), so there is no public way to ask the pricelist for a live
    price. Asserting only the saved order line would be a check that cannot fail:
    editing the rule afterwards does not reprice a line that is already stored.
    So the rule's own configuration is verified too.
    """
    front = _ch23_front(env)
    assert front, "no Brake Pad Set variant found (chapter 21 created it)"
    listed = env.call("product.product", "read", front, fields=["lst_price"])[0]["lst_price"]

    rules = env.call("product.pricelist.item", "search_read",
                     [("applied_on", "=", "0_product_variant"), ("product_id", "in", front)],
                     fields=["compute_price", "fixed_price"])
    assert rules, (
        "no '0_product_variant' rule points at the Brake Pad Set (Front). Without it there "
        "is nothing to beat the global rule, and nothing to demonstrate.")
    fixed = [r for r in rules if r["compute_price"] == "fixed"
             and round(r["fixed_price"], 2) == 60.0]
    assert fixed, (
        "the variant rule computes %r at %.2f. The hands-on uses a fixed 60.00 against a "
        "79.00 list price, so the discount is unmistakable."
        % (rules[0]["compute_price"], rules[0]["fixed_price"]))

    lines = env.call("sale.order.line", "search_read",
                     [("product_id", "in", front), ("order_id.pricelist_id", "!=", False)],
                     fields=["price_unit"])
    assert lines, (
        "the rule exists but nothing was quoted with it. Make a quotation whose Pricelist "
        "field is set, then add the Front variant to it.")
    assert any(round(l["price_unit"], 2) == 60.0 for l in lines), (
        "quoted prices are %s, none of them 60.00, though the product lists at %.2f. The "
        "line takes its price when it is created, so a line added before the rule existed "
        "keeps the old price: add a fresh line."
        % (sorted({round(l["price_unit"], 2) for l in lines}), listed))


def a_promotion_added_a_negative_line(env):
    """A reward is a NEW line with a negative price, not an edit to an existing one."""
    lines = env.call("sale.order.line", "search_read", [("price_unit", "<", 0)],
                     fields=["name", "price_unit", "order_id"])
    assert lines, (
        "no order line has a negative price_unit, so no promotion has been claimed. Apply "
        "the demo code '10pc' to your quotation. Note a reward arrives as its own line: it "
        "does not change the price of the product line, and it is not the discount field.")


# --- ch24: purchase, RFQ to vendor bill ----------------------------------------

def _ch24_po(env):
    variants = env.call("product.product", "search",
                        [("product_tmpl_id.name", "=", "Brake Pad Set")])
    lines = env.call("purchase.order.line", "search_read",
                     [("product_id", "in", variants)], fields=["order_id"])
    return sorted({l["order_id"][0] for l in lines})


def purchase_order_confirmed(env):
    ids = _ch24_po(env)
    assert ids, ("no purchase order contains a Brake Pad Set line. The hands-on raises an "
                 "RFQ for 10 of them from a vendor.")
    orders = env.call("purchase.order", "read", ids,
                      fields=["name", "state", "receipt_status", "invoice_status"])
    confirmed = [o for o in orders if o["state"] == "purchase"]
    assert confirmed, (
        "found the order but its state is %r. An RFQ becomes a purchase order when you "
        "Confirm it, which is also what creates the receipt." % orders[0]["state"])
    env._ch24 = confirmed[0]


def goods_were_received(env):
    o = getattr(env, "_ch24", None)
    assert o, "run the previous check first"
    assert o["receipt_status"] == "full", (
        "receipt_status is %r, not 'full'. Validate the incoming transfer the confirmation "
        "created, remembering to set the received quantities first."
        % o["receipt_status"])


def three_way_match_is_complete(env):
    """ordered == received == invoiced, the whole point of the chapter."""
    o = getattr(env, "_ch24", None)
    assert o, "run the previous check first"
    oid = env.call("purchase.order", "search", [("name", "=", o["name"])])
    lines = env.call("purchase.order.line", "search_read", [("order_id", "in", oid)],
                     fields=["product_qty", "qty_received", "qty_invoiced"])
    for l in lines:
        assert l["product_qty"] == l["qty_received"] == l["qty_invoiced"], (
            "this line reads ordered %.1f, received %.1f, billed %.1f. Odoo tracks all "
            "three separately on purpose: that is the three-way match, and a mismatch is "
            "exactly what it exists to surface."
            % (l["product_qty"], l["qty_received"], l["qty_invoiced"]))
    assert o["invoice_status"] == "invoiced", (
        "invoice_status is %r. Use Create Bill on the confirmed order, set an invoice "
        "date, and post it." % o["invoice_status"])


def receipt_moved_stock_both_ways(env):
    """A stock move debits one location and credits another, like an accounting entry."""
    variants = env.call("product.product", "search",
                        [("product_tmpl_id.name", "=", "Brake Pad Set")])
    quants = env.call("stock.quant", "search_read", [("product_id", "in", variants)],
                      fields=["location_id", "quantity"])
    assert quants, "no stock.quant rows exist for the brake pads at all"
    positive = [q for q in quants if q["quantity"] > 0]
    negative = [q for q in quants if q["quantity"] < 0]
    assert positive and negative, (
        "expected the receipt to leave both a positive quant in your warehouse and a "
        "negative one at the vendor location, since a move always has a source and a "
        "destination. Found quantities %s."
        % sorted(q["quantity"] for q in quants))


# --- ch25: inventory, moves, quants & warehouses -------------------------------

def a_multi_step_transfer_happened(env):
    """A reception under a 2-step route creates a lazy internal transfer."""
    n = env.call("stock.picking", "search_count",
                [("picking_type_id.code", "=", "internal"), ("state", "=", "done")])
    assert n, (
        "no completed internal transfer found. Switch the warehouse's Incoming "
        "Shipments to 'Receive goods in input, then stock (2 steps)', raise and "
        "receive a small purchase, then validate both the Receipt and the internal "
        "transfer it creates when the receipt is done.")


def a_reordering_rule_exists_for_brake_pads(env):
    variants = env.call("product.product", "search",
                        [("product_tmpl_id.name", "=", "Brake Pad Set")])
    rules = env.call("stock.warehouse.orderpoint", "search_read",
                     [("product_id", "in", variants)],
                     fields=["product_min_qty", "product_max_qty"])
    assert rules, (
        "no reordering rule exists for the Brake Pad Set. Inventory > Operations > "
        "Replenishment > New, and set a minimum and maximum. Chapter 35 covers the "
        "scheduled action that actually acts on it.")
    assert rules[0]["product_max_qty"] > rules[0]["product_min_qty"] >= 0, (
        "the rule's max (%s) should be greater than its min (%s)"
        % (rules[0]["product_max_qty"], rules[0]["product_min_qty"]))


def warehouse_reverted_to_one_step(env):
    """Leave the simple case for chapters that have not asked for routes yet."""
    wh = env.call("stock.warehouse", "search_read", [], fields=["reception_steps"], limit=1)
    assert wh and wh[0]["reception_steps"] == "one_step", (
        "the warehouse's reception route is %r, not the one-step default. Switch it "
        "back once you have seen the 2-step transfer: later chapters assume the "
        "simple case unless they say otherwise."
        % (wh[0]["reception_steps"] if wh else None))


# --- ch26: manufacturing, BoM & manufacturing orders ---------------------------

def brake_pad_bom_has_components_and_an_operation(env):
    boms = env.call("mrp.bom", "search_read",
                    [("product_tmpl_id.name", "=", "Brake Pad Set")],
                    fields=["id"])
    assert boms, (
        "no bill of materials exists for the Brake Pad Set. Manufacturing > Products "
        "> Bills of Materials > New, product Brake Pad Set.")
    bom_id = boms[0]["id"]
    lines = env.call("mrp.bom.line", "search_count", [("bom_id", "=", bom_id)])
    assert lines >= 2, (
        "the BoM has %d component line(s); add at least two so the recipe is a real "
        "bag of components, not a single substitute part." % lines)
    ops = env.call("mrp.routing.workcenter", "search_count", [("bom_id", "=", bom_id)])
    assert ops >= 1, (
        "the BoM has no operations. Add one against a work center (Assembly 1 exists "
        "in the demo data), since a real BoM usually names both what it consumes and "
        "where the work happens.")


def a_manufacturing_order_completed(env):
    variants = env.call("product.product", "search",
                        [("product_tmpl_id.name", "=", "Brake Pad Set")])
    mos = env.call("mrp.production", "search_read",
                  [("product_id", "in", variants), ("state", "=", "done")],
                  fields=["id", "product_qty"])
    assert mos, (
        "no completed manufacturing order for the Brake Pad Set. Manufacturing > "
        "Manufacturing Orders > New, set a quantity, Confirm, then Mark as Done.")
    env._ch26_mo = mos[0]


def components_were_consumed_by_bom_ratio(env):
    """The BoM says 0.5 Friction and 1.0 Plate per unit; consumption must match."""
    mo = getattr(env, "_ch26_mo", None)
    assert mo, "run the previous check first"
    moves = env.call("stock.move", "search_read",
                     [("raw_material_production_id", "=", mo["id"])],
                     fields=["product_id", "product_uom_qty", "quantity", "state"])
    assert moves, "the manufacturing order has no component moves at all"
    done = [m for m in moves if m["state"] == "done"]
    assert done, "no component move reached 'done', so nothing was actually consumed"
    by_name = {m["product_id"][1]: m["quantity"] for m in done}
    produced = mo["product_qty"]
    for name, expected_each in (("Friction Material", 0.5), ("Backing Plate", 1.0)):
        got = by_name.get(name)
        assert got is not None, "no consumed move found for %s" % name
        expected = expected_each * produced
        assert abs(got - expected) < 0.01, (
            "%s: consumed %.2f, expected %.2f (%.2f per unit x %.1f produced). "
            "Component consumption should scale exactly with the BoM ratio."
            % (name, got, expected, expected_each, produced))


# --- ch29: taxes & fiscal positions --------------------------------------------

def _ch29_split_tax(env):
    """The sales tax whose invoice distribution was split across two accounts."""
    taxes = env.call("account.tax", "search_read",
                     [("type_tax_use", "=", "sale"), ("amount", "=", 15.0)],
                     fields=["name", "amount", "price_include"])
    for tax in taxes:
        reps = env.call("account.tax.repartition.line", "search_read",
                        [("tax_id", "=", tax["id"]), ("document_type", "=", "invoice"),
                         ("repartition_type", "=", "tax")],
                        fields=["factor_percent", "account_id"])
        if len(reps) >= 2:
            tax["reps"] = reps
            return tax
    return None


def sales_tax_was_split_across_two_accounts(env):
    tax = _ch29_split_tax(env)
    assert tax, (
        "no 15% sales tax has more than one line in its invoice distribution. Duplicate "
        "the 15% sales tax and, on the Definition tab, replace the single 'of tax' line "
        "in Distribution for Invoices with two: 60% and 40%, each pointing at its own "
        "account.")
    total = round(sum(r["factor_percent"] for r in tax["reps"] if r["factor_percent"] > 0), 6)
    assert total == 100.0, (
        "the invoice distribution's positive 'of tax' lines add up to %g%%, not 100%%. "
        "account.tax constrains that itself, so the tax form would have refused this: "
        "reaching %g%% means the lines were written straight onto "
        "account.tax.repartition.line, which skips the check on the tax." % (total, total))
    accounts = {r["account_id"] and r["account_id"][0] for r in tax["reps"]}
    assert len(accounts) >= 2 and None not in accounts, (
        "the two distribution lines point at the same account (or one has none), so the "
        "split cannot be seen in the ledger. Give each line a different account; the "
        "hands-on adds 251100 City Tax Received next to 251000 Tax Received.")
    env._ch29_split = tax


def one_tax_posted_two_tax_lines(env):
    """The whole point of repartition lines: one tax, several journal lines."""
    tax = getattr(env, "_ch29_split", None)
    assert tax, "run the previous check first"
    lines = env.call("account.move.line", "search_read",
                     [("tax_line_id", "=", tax["id"]), ("parent_state", "=", "posted")],
                     fields=["move_id", "account_id", "credit", "tax_repartition_line_id"])
    assert lines, (
        "no posted invoice has a tax line from %r. Create a customer invoice, put that "
        "tax on the line, and Confirm it. A draft invoice has tax lines too, but the "
        "check looks for a posted one because only posting makes them real."
        % tax["name"])
    by_move = {}
    for line in lines:
        by_move.setdefault(line["move_id"][0], []).append(line)
    best = max(by_move.values(), key=len)
    assert len(best) >= 2, (
        "the posted invoice carries only one tax line from %r, so the split did not "
        "take effect. Check that both 'of tax' lines survived the save: the Definition "
        "tab is easy to leave with one line still at 100%%." % tax["name"])
    accounts = {l["account_id"][1] for l in best}
    assert len(accounts) >= 2, (
        "the %d tax lines all landed on the same account (%s). Each distribution line "
        "needs its own account for the split to mean anything."
        % (len(best), ", ".join(accounts)))
    total = round(sum(l["credit"] for l in best), 2)
    assert total > 0, "the tax lines credit %.2f in total, which cannot be right" % total
    # Each line's share of the tax should be its own distribution factor. This is the
    # sentence "one tax, several lines, split by factor" turned into arithmetic.
    factors = {r["id"]: r["factor_percent"] for r in tax["reps"]}
    for line in best:
        rep = line["tax_repartition_line_id"]
        share = round(100.0 * line["credit"] / total, 2)
        expected = factors.get(rep and rep[0])
        assert expected is not None, (
            "a tax line points at a distribution line that is not one of the two you "
            "configured, which usually means the invoice was posted before the split")
        assert abs(share - expected) < 0.05, (
            "the line on %s took %.2f of %.2f (%.2f%%), but its distribution line says "
            "%g%%. The amounts should follow the factors exactly."
            % (line["account_id"][1], line["credit"], total, share, expected))


def a_tax_included_tax_exists(env):
    taxes = env.call("account.tax", "search_read",
                     [("type_tax_use", "=", "sale"), ("price_include", "=", True)],
                     fields=["name", "amount", "price_include_override"])
    assert taxes, (
        "no sales tax reads price_include = True. Create one and set Included in Price "
        "to 'Tax Included' on its Advanced Options tab. The company-wide default is "
        "locked once a database has journal entries, so the per-tax override is the "
        "only way in from here.")
    env._ch29_incl = taxes[0]


def tax_included_tax_books_to_a_tax_account(env):
    """A brand new tax has no account on its distribution, and posts into income."""
    tax = getattr(env, "_ch29_incl", None)
    assert tax, "run the previous check first"
    reps = env.call("account.tax.repartition.line", "search_read",
                    [("tax_id", "=", tax["id"]), ("document_type", "=", "invoice"),
                     ("repartition_type", "=", "tax")],
                    fields=["factor_percent", "account_id"])
    assert reps, "tax %r has no 'of tax' line in its invoice distribution" % tax["name"]
    missing = [r for r in reps if not r["account_id"]]
    assert not missing, (
        "tax %r still has a distribution line with no account. Odoo does not complain: "
        "it books the tax to whatever account the base line used, so the tax quietly "
        "lands in income. Set the account on both the invoice and refund 'of tax' "
        "lines." % tax["name"])
    groups = env.call("account.account", "read", [r["account_id"][0] for r in reps],
                      fields=["code", "name", "internal_group"])
    wrong = [g for g in groups if g["internal_group"] in ("income", "expense")]
    assert not wrong, (
        "tax %r books to %s, which is an %s account. Tax you owe onward is a liability, "
        "not revenue: point the distribution at a tax account such as 251000."
        % (tax["name"], wrong[0]["name"], wrong[0]["internal_group"]))


def a_tax_included_line_was_invoiced(env):
    """100.00 tax-included must post 86.96 of revenue and 13.04 of tax."""
    tax = getattr(env, "_ch29_incl", None)
    assert tax, "run the previous check first"
    lines = env.call("account.move.line", "search_read",
                     [("tax_ids", "in", [tax["id"]]), ("parent_state", "=", "posted")],
                     fields=["move_id", "price_unit", "price_subtotal", "price_total"])
    assert lines, (
        "no posted invoice line carries tax %r. Create a customer invoice with that tax "
        "on the line and Confirm it." % tax["name"])
    hundred = [l for l in lines if abs(l["price_unit"] - 100.0) < 0.005]
    assert hundred, (
        "none of the %d posted lines with that tax has a price of 100.00. The hands-on "
        "uses 100.00 on purpose: it is the price that does not divide cleanly by 1.15, "
        "so it shows where the rounding goes." % len(lines))
    line = hundred[0]
    assert abs(line["price_subtotal"] - 86.96) < 0.005, (
        "the 100.00 line posted a subtotal of %.2f, expected 86.96. With the tax "
        "included, the price you type is the total: the base is 100 / 1.15."
        % line["price_subtotal"])
    assert abs(line["price_total"] - 100.0) < 0.005, (
        "the 100.00 line's total is %.2f, expected 100.00. A tax-included line's total "
        "is the price you typed; if it is 115.00 the tax is being added on top, so the "
        "override did not apply." % line["price_total"])


def an_export_order_dropped_the_domestic_tax(env):
    """Anchored on the Brake Pad Set: the demo already ships foreign orders, and a
    check that any of those exist would be green before the reader did anything."""
    company = env.call("res.users", "read", [env.uid], fields=["company_id"])[0]["company_id"][0]
    home = env.call("res.company", "read", [company], fields=["account_fiscal_country_id"])[0]
    home_country = home["account_fiscal_country_id"] and home["account_fiscal_country_id"][0]
    home_name = home["account_fiscal_country_id"][1] if home_country else "the company country"
    variants = env.call("product.product", "search",
                        [("product_tmpl_id.name", "=", "Brake Pad Set")])
    orders = env.call("sale.order", "search_read",
                      [("order_line.product_id", "in", variants),
                       ("partner_id.country_id", "!=", home_country),
                       ("partner_id.country_id", "!=", False)],
                      fields=["name", "partner_id", "fiscal_position_id", "amount_tax"])
    assert orders, (
        "no order for the Brake Pad Set exists for a customer outside %s. Create a "
        "contact with a foreign country set, then quote them the brake pads: the demo's "
        "Foreign Trade fiscal position auto-applies on country alone." % home_name)
    mapped = [o for o in orders if o["fiscal_position_id"]]
    assert mapped, (
        "order %s is for a customer outside %s but has no fiscal position. Odoo resolves "
        "it from the customer's country as the order is created, and a contact with no "
        "country gets no fiscal position at all, so setting the country afterwards does "
        "not fix an existing quotation: make a fresh one."
        % (orders[0]["name"], home_name))
    order = mapped[0]
    assert round(order["amount_tax"], 2) == 0.0, (
        "order %s has a fiscal position (%s) but still carries %.2f of tax. Foreign "
        "Trade swaps the 15%% for 0%% Exports; if tax remains, the line's tax was set by "
        "hand after the mapping ran, and a manual tax wins."
        % (order["name"], order["fiscal_position_id"][1], order["amount_tax"]))
    # Zero tax alone would also be true of a line with no tax at all. What proves the
    # mapping ran is that the line's tax declares which domestic tax it replaces.
    lines = env.call("sale.order.line", "search_read", [("order_id", "=", order["id"])],
                     fields=["tax_ids"])
    tax_ids = [t for line in lines for t in line["tax_ids"]]
    assert tax_ids, (
        "order %s has no tax on its lines at all. That is not the same thing as a mapped "
        "0%% tax: an export still gets taxed, at zero, so the sale is reported rather "
        "than invisible." % order["name"])
    taxes = env.call("account.tax", "read", tax_ids, fields=["name", "amount", "original_tax_ids"])
    replacements = [t for t in taxes if t["original_tax_ids"]]
    assert replacements, (
        "the tax on order %s is %s, which does not replace anything. In Odoo 19 the "
        "mapping lives on the tax: the replacement carries the domestic tax in its "
        "'Replaces' field (original_tax_ids), and the fiscal position just lists it."
        % (order["name"], ", ".join(t["name"] for t in taxes)))
    env._ch29_order = order


def _brake_pad_variant(env):
    """The Brake Pad Set variant chapter 21 created, used by the ch30 checks."""
    rows = env.call("product.product", "search_read",
                    [("product_tmpl_id.name", "=", "Brake Pad Set")],
                    fields=["categ_id", "standard_price", "qty_available"], limit=1)
    assert rows, "no Brake Pad Set product found; chapter 21 creates it"
    return rows[0]


def brake_pads_have_a_category(env):
    """A product with no category falls back to periodic/standard and a zero cost."""
    prod = _brake_pad_variant(env)
    assert prod["categ_id"], (
        "the Brake Pad Set has no product category. A category is what supplies the "
        "costing method, the valuation mode and the stock account, so without one the "
        "product silently values at 0.00 no matter what you paid")


def goods_category_is_avco_and_real_time(env):
    """Cost method and valuation mode are two separate switches; this sets both."""
    prod = _brake_pad_variant(env)
    rows = env.call("product.category", "read", [prod["categ_id"][0]],
                    fields=["property_cost_method", "property_valuation"])[0]
    assert rows["property_cost_method"] == "average", (
        "the category's costing method is %r, expected 'average'. Standard Price keeps "
        "whatever cost you typed; AVCO derives it from what actually moved."
        % rows["property_cost_method"])
    assert rows["property_valuation"] == "real_time", (
        "the category's valuation is %r, expected 'real_time' (labelled Perpetual). "
        "Under 'periodic' Odoo still values every move, it just never posts a journal "
        "entry for one." % rows["property_valuation"])


def avco_derived_the_unit_cost(env):
    """630.00 of receipts over 19 units is 33.1579, and AVCO works that out itself."""
    prod = _brake_pad_variant(env)
    cost = prod["standard_price"]
    assert abs(cost - 33.1578947368421) < 0.01, (
        "the Brake Pad Set's cost is %s, expected about 33.16. Switching the category "
        "to AVCO makes Odoo recompute the cost from the movements that already exist "
        "(630.00 received over 19 units), so a wrong number here usually means the "
        "receipts from chapters 24 and 25 are missing" % cost)


def customers_location_routes_to_cogs(env):
    """In Odoo 19 the counterpart account lives on the location, not the category."""
    rows = env.call("stock.location", "search_read", [("usage", "=", "customer")],
                    fields=["valuation_account_id"], limit=1)
    assert rows, "no customer location found"
    acc = rows[0]["valuation_account_id"]
    assert acc, (
        "the Customers location has no Stock Valuation Account. Odoo 19 asks each "
        "location outside the company what value becomes when it arrives there, and "
        "without it a delivery posts no journal entry at all")
    acc_type = env.call("account.account", "read", [acc[0]], fields=["account_type"])[0]
    assert acc_type["account_type"].startswith("expense"), (
        "the Customers location points at %r, whose type is %r. Stock leaving for a "
        "customer becomes cost of goods sold, so it wants an expense account."
        % (acc[1], acc_type["account_type"]))


def the_waiting_delivery_posted_cogs(env):
    """Validating chapter 22's delivery is what finally moves value into the P&L."""
    picks = env.call("stock.picking", "search_read", [("name", "=", "WH/OUT/00044")],
                     fields=["state"])
    assert picks, ("WH/OUT/00044 not found; it is the delivery chapter 22 created and "
                   "chapter 24 made reservable")
    assert picks[0]["state"] == "done", (
        "WH/OUT/00044 is %r, not 'done'. Validate it: that transfer has been waiting "
        "since chapter 22 and it is what posts the first stock journal entry."
        % picks[0]["state"])
    moves = env.call("stock.move", "search_read",
                     [("picking_id.name", "=", "WH/OUT/00044")],
                     fields=["value", "account_move_id"])
    assert moves and moves[0]["account_move_id"], (
        "the delivery move has no account_move_id, so no journal entry was posted. "
        "Check that the category is real_time and the Customers location has an account")
    val = moves[0]["value"]
    assert abs(val - 132.63) < 0.5, (
        "the move is valued at %s, expected about 132.63 (4 units at the 33.16 average)"
        % val)
    lines = env.call("account.move.line", "search_read",
                     [("move_id", "=", moves[0]["account_move_id"][0])],
                     fields=["debit", "credit", "account_id"])
    assert len(lines) == 2, "expected two journal lines, found %d" % len(lines)
    debits = [l for l in lines if l["debit"]]
    credits = [l for l in lines if l["credit"]]
    assert debits and credits, "the entry should have one debit and one credit"
    assert abs(debits[0]["debit"] - credits[0]["credit"]) < 0.01, (
        "the stock entry does not balance, which chapter 27 says is impossible")


def rounding_method_is_back_to_round_per_tax(env):
    company = env.call("res.users", "read", [env.uid], fields=["company_id"])[0]["company_id"][0]
    method = env.call("res.company", "read", [company],
                      fields=["tax_calculation_rounding_method"])[0]["tax_calculation_rounding_method"]
    assert method == "round_globally", (
        "the company's tax rounding method is %r. The hands-on flips it to Round per "
        "Line to make the cent appear, then puts it back to Round per Tax, which is "
        "Odoo 19's default. Leaving it flipped changes every total computed after this "
        "chapter." % method)


# ---------------------------------------------------- inv01 checks --
# Inventory deep dive, chapter 1: the warehouse map. Database "warehouse".

def inventory_app_installed(env):
    rows = env.call("ir.module.module", "search_read", [("name", "=", "stock")], fields=["state"])
    assert rows and rows[0]["state"] == "installed", "the Inventory app (module 'stock') is not installed"


def _in_group(env, xmlid):
    # has_group over XML-RPC returns None for some groups in 19; the group list does not lie
    gid = _xmlid(env, xmlid)  # first call of a run: this is what logs in and sets env.uid
    return bool(env.call("res.users", "search_count", [("id", "=", env.uid), ("all_group_ids", "in", [gid])]))


def storage_locations_are_on(env):
    assert _in_group(env, "stock.group_stock_multi_locations"), (
        "the Storage Locations setting is off; Inventory > Configuration > Settings > Storage Locations")


def depot_warehouse_exists(env):
    rows = env.call("stock.warehouse", "search_read", [("code", "=", "LFD")], fields=["name", "lot_stock_id"])
    assert rows, "no warehouse with Short Name LFD; rename the default warehouse (Configuration > Warehouses)"
    assert rows[0]["name"] == "LibreFleet Depot", "the LFD warehouse is named %r, expected 'LibreFleet Depot'" % rows[0]["name"]
    assert rows[0]["lot_stock_id"][1] == "LFD/Stock", (
        "the warehouse's stock location is %r, expected LFD/Stock: the Short Name renames every location under it"
        % rows[0]["lot_stock_id"][1])


def two_shelves_under_stock(env):
    rows = env.call("stock.location", "search_read",
                    [("complete_name", "in", ["LFD/Stock/Shelf A", "LFD/Stock/Shelf B"])], fields=["usage"])
    assert len(rows) == 2, "expected both LFD/Stock/Shelf A and LFD/Stock/Shelf B; found %d" % len(rows)
    assert all(r["usage"] == "internal" for r in rows), "a shelf is not an Internal location"


def products_of_each_kind(env):
    rows = env.call("product.template", "search_read",
                    [("name", "in", ["Brake Pad Set", "Engine Oil 5W-30 1L", "Diagnostic Tablet", "Shop Rags", "Labour Hour"])],
                    fields=["name", "type", "is_storable"])
    found = {r["name"]: r for r in rows}
    missing = [n for n in ("Brake Pad Set", "Engine Oil 5W-30 1L", "Diagnostic Tablet", "Shop Rags", "Labour Hour") if n not in found]
    assert not missing, "products missing: %s" % ", ".join(missing)
    for name in ("Brake Pad Set", "Engine Oil 5W-30 1L", "Diagnostic Tablet"):
        assert found[name]["type"] == "consu" and found[name]["is_storable"], (
            "%s must be Goods with Track Inventory ticked" % name)
    assert found["Shop Rags"]["type"] == "consu" and not found["Shop Rags"]["is_storable"], (
        "Shop Rags must be Goods with Track Inventory unticked: it is used up, never counted")
    assert found["Labour Hour"]["type"] == "service", "Labour Hour must be a Service"


def first_receipt_is_done(env):
    rows = env.call("stock.picking", "search_read",
                    [("picking_type_id.code", "=", "incoming"), ("state", "=", "done")],
                    fields=["name", "move_ids"])
    assert rows, "no validated receipt yet; Inventory > Operations > Receipts > New, four lines, Validate"
    assert any(len(r["move_ids"]) >= 4 for r in rows), (
        "a receipt is done but none has four lines; the chapter receives all four goods at once")


def quants_say_what_is_on_the_shelf(env):
    stock = env.call("stock.location", "search", [("complete_name", "=", "LFD/Stock")])
    assert stock, "no LFD/Stock location"
    rows = env.call("stock.quant", "search_read", [("location_id", "=", stock[0])],
                    fields=["product_id", "quantity"])
    have = {r["product_id"][1]: r["quantity"] for r in rows}
    assert have.get("Brake Pad Set") == 20.0, "LFD/Stock should hold 20 Brake Pad Set, it holds %s" % have.get("Brake Pad Set")
    assert have.get("Engine Oil 5W-30 1L") == 12.0, "LFD/Stock should hold 12 Engine Oil 5W-30 1L"
    assert have.get("Diagnostic Tablet") == 1.0, "LFD/Stock should hold 1 Diagnostic Tablet"
    assert "Shop Rags" not in have, (
        "Shop Rags has a quant, so it is tracked: untick Track Inventory on it (a product that is "
        "not tracked is received and then forgotten, by design)")


def _moves_of(env, pickings, **domain):
    return env.call("stock.move", "search_read", [("picking_id", "in", pickings)] + list(domain.items()),
                    fields=["product_id", "product_uom_qty", "quantity", "state"])


def delivery_to_garage_nord_is_done(env):
    rows = env.call("stock.picking", "search_read",
                    [("picking_type_id.code", "=", "outgoing"), ("state", "=", "done"),
                     ("partner_id.name", "=", "Garage Nord")], fields=["name"])
    assert rows, ("no done delivery to Garage Nord yet; Operations > Transfers > Deliveries > New, "
                  "Delivery Address Garage Nord, Brake Pad Set 8 and Engine Oil 5W-30 1L 2, Mark as Todo, Validate")
    got = {(m["product_id"][1], m["quantity"]) for m in _moves_of(env, [r["id"] for r in rows])}
    assert ("Brake Pad Set", 8.0) in got and ("Engine Oil 5W-30 1L", 2.0) in got, (
        "a delivery to Garage Nord is done, but not one with 8 Brake Pad Set and 2 Engine Oil 5W-30 1L")


def backorder_was_created_then_delivered(env):
    rows = env.call("stock.picking", "search_read",
                    [("backorder_id", "!=", False), ("picking_type_id.code", "=", "outgoing")],
                    fields=["name", "state"])
    assert rows, ("no backorder yet; deliver 15 Brake Pad Set while only 12 are free, Validate, and "
                  "answer Create Backorder")
    done = [r["id"] for r in rows if r["state"] == "done"]
    assert done, ("the backorder exists but is not done; receive 10 Brake Pad Set from Brembo Parts, "
                  "then Validate the backorder once it turns Ready by itself")
    assert any(m["product_uom_qty"] == 3.0 for m in _moves_of(env, done)), (
        "the done backorder should carry the 3 Brake Pad Set that were missing")


def ten_more_pads_were_received(env):
    moves = env.call("stock.move", "search_read",
                     [("picking_id.picking_type_id.code", "=", "incoming"), ("state", "=", "done"),
                      ("product_id.name", "=", "Brake Pad Set"), ("product_uom_qty", "=", 10)],
                     fields=["reference"])
    assert moves, ("no done receipt of 10 Brake Pad Set; Operations > Transfers > Receipts > New, "
                   "Receive From Brembo Parts, Brake Pad Set 10, Validate")


def two_pads_came_back(env):
    rows = env.call("stock.picking", "search_read", [("return_id", "!=", False), ("state", "=", "done")],
                    fields=["name"])
    assert rows, ("no done return yet; open the done delivery LFD/OUT/00001, click Return, set Brake Pad "
                  "Set to 2, delete the oil line, click Return, then Validate the receipt it opens")
    got = {(m["product_id"][1], m["quantity"]) for m in _moves_of(env, [r["id"] for r in rows])}
    assert ("Brake Pad Set", 2.0) in got, "a return is done, but not one bringing back 2 Brake Pad Set"


def one_bottle_was_scrapped(env):
    rows = env.call("stock.scrap", "search_read", [("state", "=", "done")], fields=["product_id", "scrap_qty"])
    assert rows, "no validated scrap; Operations > Adjustments > Scrap > New, Engine Oil 5W-30 1L, quantity 1, Validate"
    assert any(r["product_id"][1] == "Engine Oil 5W-30 1L" and r["scrap_qty"] == 1.0 for r in rows), (
        "a scrap is done, but not for 1 Engine Oil 5W-30 1L")


def tablet_delivery_was_cancelled(env):
    rows = env.call("stock.picking", "search_read",
                    [("state", "=", "cancel"), ("picking_type_id.code", "=", "outgoing")], fields=["name"])
    assert rows, ("no cancelled delivery; with Delivery Orders set to reserve Manually, create a delivery "
                  "of 1 Diagnostic Tablet, Mark as Todo, Check Availability, then Cancel")
    assert any(m["product_id"][1] == "Diagnostic Tablet" for m in _moves_of(env, [r["id"] for r in rows])), (
        "a delivery is cancelled, but not the one for the Diagnostic Tablet")


def deliveries_reserve_at_confirmation_again(env):
    rows = env.call("stock.picking.type", "search_read",
                    [("code", "=", "outgoing"), ("warehouse_id", "!=", False)], fields=["reservation_method"])
    assert rows and all(r["reservation_method"] == "at_confirm" for r in rows), (
        "Delivery Orders still reserve Manually; Configuration > Operations Types > Delivery Orders, "
        "set Reservation Method back to At Confirmation so the next chapters behave as described")


def shelf_holds_nine_nine_and_one(env):
    stock = env.call("stock.location", "search", [("complete_name", "=", "LFD/Stock")])
    assert stock, "no LFD/Stock location"
    rows = env.call("stock.quant", "search_read", [("location_id", "=", stock[0])],
                    fields=["product_id", "quantity", "reserved_quantity"])
    have = {r["product_id"][1]: r["quantity"] for r in rows}
    assert have.get("Brake Pad Set") == 9.0, (
        "LFD/Stock should hold 9 Brake Pad Set (20 - 8 - 12 + 10 - 3 + 2), it holds %s" % have.get("Brake Pad Set"))
    assert have.get("Engine Oil 5W-30 1L") == 9.0, (
        "LFD/Stock should hold 9 Engine Oil 5W-30 1L (12 - 2 - 1 scrapped), it holds %s" % have.get("Engine Oil 5W-30 1L"))
    assert have.get("Diagnostic Tablet") == 1.0, "the cancelled delivery must leave the Diagnostic Tablet on the shelf"
    assert all(r["reserved_quantity"] == 0 for r in rows), (
        "something is still reserved in LFD/Stock; a cancelled or done transfer holds no reservation, "
        "so a transfer is still open: find it under Operations > Transfers")


def multi_step_routes_is_on(env):
    assert _in_group(env, "stock.group_adv_location"), (
        "Multi-Step Routes is off; Inventory > Configuration > Settings > Warehouse > Multi-Step Routes, Save")


def depot_receives_in_two_steps_and_ships_in_three(env):
    wh = env.call("stock.warehouse", "search_read", [("code", "=", "LFD")], fields=["reception_steps", "delivery_steps"])
    assert wh, "no warehouse with Short Name LFD"
    assert wh[0]["reception_steps"] == "two_steps", (
        "Incoming Shipments is %r; Configuration > Warehouses > LibreFleet Depot, pick Receive then Store (2 steps)"
        % wh[0]["reception_steps"])
    assert wh[0]["delivery_steps"] == "pick_pack_ship", (
        "Outgoing Shipments is %r; on the same form pick Pick, Pack, then Deliver (3 steps)" % wh[0]["delivery_steps"])


def _done_moves(env, type_code, product, qty):
    return env.call("stock.move", "search_read",
                    [("state", "=", "done"), ("picking_id.picking_type_id.sequence_code", "=", type_code),
                     ("product_id.name", "=", product), ("product_uom_qty", "=", qty)],
                    fields=["reference", "move_orig_ids", "move_dest_ids"])


def six_bottles_came_in_through_input(env):
    assert _done_moves(env, "IN", "Engine Oil 5W-30 1L", 6), (
        "no done receipt of 6 Engine Oil 5W-30 1L; Receipts > New, Receive From Brembo Parts, 6 bottles, Validate. "
        "With two-step reception the receipt lands in LFD/Input")
    stor = _done_moves(env, "STOR", "Engine Oil 5W-30 1L", 6)
    assert stor, ("the receipt is done but its Storage transfer is not; open the receipt, click Next Transfer "
                  "(the push rule made it) and Validate it, that is what puts the bottles in LFD/Stock")
    assert stor[0]["move_orig_ids"], "the Storage transfer is not chained to the receipt; it should come from the push rule, not be typed by hand"


def four_pads_went_pick_pack_ship(env):
    for code, hint in (("PICK", "Overview > Pick > New: Garage Nord, Brake Pad Set 4, Mark as Todo, Validate"),
                       ("PACK", "validate the Pick, then Next Transfer opens the Pack it pushed: Validate it"),
                       ("OUT", "validate the Pack, then Next Transfer opens the delivery: Validate it")):
        assert _done_moves(env, code, "Brake Pad Set", 4), "no done %s transfer of 4 Brake Pad Set; %s" % (code, hint)
    out = _done_moves(env, "OUT", "Brake Pad Set", 4)
    assert out[0]["move_orig_ids"], ("the delivery of 4 pads was typed by hand, not pushed from a Pack; in a "
                                     "three-step warehouse the chain starts at the Pick")


def sales_and_purchase_are_installed(env):
    rows = env.call("ir.module.module", "search_read",
                    [("name", "in", ["sale_management", "purchase"]), ("state", "=", "installed")], fields=["name"])
    missing = {"sale_management", "purchase"} - {r["name"] for r in rows}
    assert not missing, "Apps > Activate Sales and Purchase; still missing: %s" % ", ".join(sorted(missing))


def tablet_is_replenished_on_order(env):
    mto = env.call("stock.route", "search_read", [("name", "ilike", "Replenish on Order")],
                   fields=["active"], context={"active_test": False})
    assert mto and mto[0]["active"], (
        "the Replenish on Order (MTO) route is archived; Inventory > Configuration > Settings > Replenish on Order (MTO), Save")
    tmpl = env.call("product.template", "search_read", [("name", "=", "Diagnostic Tablet")], fields=["route_ids", "seller_ids"])
    assert tmpl, "no Diagnostic Tablet product"
    assert mto[0]["id"] in tmpl[0]["route_ids"], (
        "the tablet does not have the Replenish on Order (MTO) route; product form > Inventory tab > Routes")
    assert tmpl[0]["seller_ids"], (
        "the tablet has no vendor; product form > Purchase tab > Add a line, Brembo Parts. The Buy rule only "
        "fires for a product that has someone to buy it from")


def the_order_bought_the_tablet(env):
    so = env.call("sale.order", "search_read",
                  [("partner_id.name", "=", "Garage Nord"), ("state", "=", "sale"),
                   ("order_line.product_id.name", "=", "Diagnostic Tablet")], fields=["name", "order_line"])
    assert so, "no confirmed sales order for a Diagnostic Tablet to Garage Nord; Sales > New, Diagnostic Tablet 1, Confirm"
    po = env.call("purchase.order", "search_read", [("origin", "=", so[0]["name"])], fields=["state", "picking_ids"])
    assert po, ("confirming the order created no purchase; the chain is MTO route on the product + a vendor on the "
                "product + the warehouse's Buy rule. Check the three, then confirm a new order")
    assert po[0]["state"] in ("purchase", "done"), "the request for quotation %s is still open; open it and Confirm Order" % so[0]["name"]
    pickings = env.call("stock.picking", "search_read", [("id", "in", po[0]["picking_ids"])], fields=["state"])
    assert pickings and all(p["state"] == "done" for p in pickings), (
        "the purchase's receipt is not done; open it from the purchase order, Validate, then Validate the Storage it pushes")
    line = env.call("sale.order.line", "read", so[0]["order_line"], ["qty_delivered"])[0]
    assert line["qty_delivered"] == 1.0, (
        "the order shows %s delivered; the Pick woke up when the Storage was done, so Validate Pick, then Pack, then the delivery"
        % line["qty_delivered"])


def shelf_holds_five_fifteen_and_one(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "=", "internal")],
                    fields=["product_id", "location_id", "quantity", "reserved_quantity"])
    stock = {r["product_id"][1]: r["quantity"] for r in rows if r["location_id"][1] == "LFD/Stock"}
    assert stock.get("Brake Pad Set") == 5.0, "LFD/Stock should hold 5 Brake Pad Set (9 - 4 picked), it holds %s" % stock.get("Brake Pad Set")
    assert stock.get("Engine Oil 5W-30 1L") == 15.0, "LFD/Stock should hold 15 Engine Oil 5W-30 1L (9 + 6 stored), it holds %s" % stock.get("Engine Oil 5W-30 1L")
    assert stock.get("Diagnostic Tablet") == 1.0, "LFD/Stock should hold 1 Diagnostic Tablet: the bought one came in and went out"
    stuck = [(r["location_id"][1], r["product_id"][1], r["quantity"]) for r in rows
             if r["location_id"][1] != "LFD/Stock" and r["quantity"]]
    assert not stuck, "goods are sitting in a step location: %s. A transfer in the chain is not validated" % stuck


def manufacturing_is_installed(env):
    rows = env.call("ir.module.module", "search_read", [("name", "=", "mrp"), ("state", "=", "installed")], fields=["name"])
    assert rows, "Apps > Manufacturing > Activate (the module is called mrp)"


def depot_manufactures_in_three_steps(env):
    wh = env.call("stock.warehouse", "search_read", [("code", "=", "LFD")], fields=["manufacture_steps"])
    assert wh and wh[0]["manufacture_steps"] == "pbm_sam", (
        "Manufacture is %r on the warehouse; Configuration > Warehouses > LibreFleet Depot, Resupply, pick "
        "Pick components, manufacture, then store products (3 steps)" % (wh and wh[0]["manufacture_steps"]))


def the_two_bills_of_materials_exist(env):
    boms = env.call("mrp.bom", "search_read", [], fields=["product_tmpl_id", "type", "bom_line_ids", "product_qty"])
    by_name = {b["product_tmpl_id"][1]: b for b in boms}
    pads = by_name.get("Brake Pad Set")
    assert pads and pads["type"] == "normal", ("no bill of materials of type Manufacture this product for Brake Pad Set; "
                                               "Manufacturing > Products > Bills of Materials > New")
    lines = {l["product_id"][1]: l["product_qty"] for l in
             env.call("mrp.bom.line", "search_read", [("bom_id", "=", pads["id"])], fields=["product_id", "product_qty"])}
    assert lines == {"Friction Pad": 2.0, "Backing Plate": 2.0}, (
        "the Brake Pad Set BoM should have 2 Friction Pad and 2 Backing Plate per set, it has %s" % lines)
    kit = by_name.get("Brake Service Kit")
    assert kit and kit["type"] == "phantom", ("no Kit bill of materials for Brake Service Kit; on the product, Bill of "
                                              "Materials > New, BoM Type Kit, 1 Brake Pad Set and 2 Engine Oil 5W-30 1L")


def components_were_received_and_stored(env):
    for name in ("Friction Pad", "Backing Plate"):
        assert _done_moves(env, "STOR", name, 20), (
            "no done Storage of 20 %s; Receipts > New from Brembo Parts, 20 of each component, Validate, then "
            "Next Transfer and Validate the Storage" % name)


def three_pads_were_made_from_stock(env):
    mos = env.call("mrp.production", "search_read", [("state", "=", "done"), ("product_qty", "=", 3)],
                   fields=["name", "origin", "product_id"])
    assert any(m["product_id"][1] == "Brake Pad Set" and not m["origin"] for m in mos), (
        "no done manufacturing order for 3 Brake Pad Set typed by hand; Manufacturing > Operations > Manufacturing "
        "Orders > New, Brake Pad Set, 3, Confirm, Produce All")


def a_kit_was_delivered_as_its_parts(env):
    moves = env.call("stock.move", "search_read",
                     [("state", "=", "done"), ("bom_line_id", "!=", False),
                      ("picking_id.picking_type_id.sequence_code", "=", "OUT")],
                     fields=["product_id", "product_uom_qty"])
    got = {(m["product_id"][1], m["product_uom_qty"]) for m in moves}
    assert ("Brake Pad Set", 1.0) in got and ("Engine Oil 5W-30 1L", 2.0) in got, (
        "no done delivery that came from a kit; Overview > Pick > New, Garage Nord, Brake Service Kit 1, Mark as Todo "
        "(the kit explodes into its parts), Validate, then Next Transfer twice")


def the_order_made_its_own_pads(env):
    so = env.call("sale.order", "search_read",
                  [("partner_id.name", "=", "Garage Nord"), ("state", "=", "sale"),
                   ("order_line.product_id.name", "=", "Brake Pad Set")], fields=["name", "order_line"])
    assert so, "no confirmed sales order for Brake Pad Set to Garage Nord; put the MTO route on the pads first, then Sales > New, 2 pads, Confirm"
    mo = env.call("mrp.production", "search_read", [("origin", "=", so[0]["name"])], fields=["state", "product_qty"])
    assert mo, ("confirming the order created no manufacturing order; the pads need the Replenish on Order (MTO) route and "
                "a bill of materials, and the warehouse Manufacture to Resupply")
    assert mo[0]["state"] == "done", "the manufacturing order from the sale is not done; Validate its Pick Components, then Produce All"
    for code, hint in (("PC", "Pick Components, from the MO's Transfers button"),
                       ("SFP", "Store Finished Product, pushed when the MO was done")):
        assert _done_moves(env, code, "Brake Pad Set" if code == "SFP" else "Friction Pad", 2 if code == "SFP" else 4), (
            "no done %s transfer; %s" % (code, hint))
    line = env.call("sale.order.line", "read", so[0]["order_line"], ["qty_delivered"])[0]
    assert line["qty_delivered"] == 2.0, (
        "the order shows %s delivered; the Pick woke up when the Store Finished Product was done, so Validate Pick, Pack, delivery"
        % line["qty_delivered"])


def shelf_holds_seven_thirteen_ten_ten_and_one(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "=", "internal")],
                    fields=["product_id", "location_id", "quantity"])
    stock = {r["product_id"][1]: r["quantity"] for r in rows if r["location_id"][1] == "LFD/Stock"}
    want = {"Brake Pad Set": 7.0, "Engine Oil 5W-30 1L": 13.0, "Friction Pad": 10.0, "Backing Plate": 10.0, "Diagnostic Tablet": 1.0}
    for name, qty in want.items():
        assert stock.get(name) == qty, "LFD/Stock should hold %s %s, it holds %s" % (qty, name, stock.get(name))
    stuck = [(r["location_id"][1], r["product_id"][1], r["quantity"]) for r in rows
             if r["location_id"][1] != "LFD/Stock" and r["quantity"]]
    assert not stuck, "goods are sitting in a step location: %s. A transfer in a chain is not validated" % stuck


def _rule_for(env, product):
    return env.call("stock.warehouse.orderpoint", "search_read",
                    [("product_id.name", "=", product), ("location_id.complete_name", "=", "LFD/Stock")],
                    fields=["name", "trigger", "product_min_qty", "product_max_qty", "replenishment_uom_id", "route_id"])


def twenty_bottles_were_sold_and_shipped(env):
    lines = env.call("sale.order.line", "search_read",
                     [("order_id.partner_id.name", "=", "Garage Nord"), ("order_id.state", "=", "sale"),
                      ("product_id.name", "=", "Engine Oil 5W-30 1L"), ("product_uom_qty", "=", 20)],
                     fields=["qty_delivered"])
    assert lines, "no confirmed sales order for 20 Engine Oil 5W-30 1L to Garage Nord; Sales > New, 20 bottles at 12, Confirm"
    assert lines[0]["qty_delivered"] == 20.0, (
        "the order shows %s delivered; once the replenishment arrived the Pick was fully reserved, so Validate "
        "Pick, Pack and the delivery" % lines[0]["qty_delivered"])


def oil_has_a_vendor_and_a_pack(env):
    tmpl = env.call("product.template", "search_read", [("name", "=", "Engine Oil 5W-30 1L")], fields=["seller_ids", "uom_ids"])
    sellers = env.call("product.supplierinfo", "search_read", [("id", "in", tmpl[0]["seller_ids"])],
                       fields=["partner_id", "price", "delay"])
    assert any(r["partner_id"][1] == "Nordic Lubricants" and r["price"] == 6 and r["delay"] == 3 for r in sellers), (
        "the oil has no vendor line Nordic Lubricants at 6.00 with a 3-day lead time; product form, Purchase tab, "
        "Add a line. Without a vendor the Buy rule is invisible to it")
    packs = env.call("uom.uom", "search_read", [("id", "in", tmpl[0]["uom_ids"])], fields=["name"])
    assert any(r["name"] == "Pack of 6" for r in packs), (
        "Pack of 6 is not among the oil's packagings; product form, Sales tab, Packagings. Only packagings and the "
        "vendor's unit are offered as a Multiple")


def oil_rule_is_automatic_min_max_by_the_pack(env):
    rows = _rule_for(env, "Engine Oil 5W-30 1L")
    assert rows, "no reordering rule for the oil in LFD/Stock; the Replenishment report creates one when the forecast goes negative"
    r = rows[0]
    assert (r["product_min_qty"], r["product_max_qty"]) == (10.0, 30.0), (
        "the oil's rule is Min %s / Max %s, expected 10 / 30" % (r["product_min_qty"], r["product_max_qty"]))
    assert r["replenishment_uom_id"] and r["replenishment_uom_id"][1] == "Pack of 6", (
        "the oil's Multiple is %r, expected Pack of 6 (show the Multiple column from the optional columns)"
        % (r["replenishment_uom_id"] and r["replenishment_uom_id"][1]))
    assert r["trigger"] == "auto", "the oil's rule is still Manual; Automate orders once and switches the trigger to Auto"


def automate_bought_42_bottles(env):
    rule = _rule_for(env, "Engine Oil 5W-30 1L")
    lines = env.call("purchase.order.line", "search_read",
                     [("orderpoint_id", "in", [r["id"] for r in rule]), ("product_qty", "=", 42)],
                     fields=["order_id", "qty_received", "partner_id"])
    assert lines, ("no purchase line for 42 bottles from the oil's rule; 30 minus a forecast of -7 is 37, rounded up "
                   "to 7 packs of 6, then Automate")
    assert lines[0]["partner_id"][1] == "Nordic Lubricants", "the 42 bottles were bought from %s" % lines[0]["partner_id"][1]
    assert lines[0]["qty_received"] == 42.0, (
        "%s is not received; Confirm Order, Receive, Validate, then Next Transfer and Validate the Storage"
        % lines[0]["order_id"][1])


def pads_rule_manufactures_automatically(env):
    rows = _rule_for(env, "Brake Pad Set")
    assert rows, "no reordering rule for Brake Pad Set; product form, More, Reordering Rules, New"
    r = rows[0]
    assert (r["product_min_qty"], r["product_max_qty"]) == (10.0, 15.0), (
        "the pads' rule is Min %s / Max %s, expected 10 / 15" % (r["product_min_qty"], r["product_max_qty"]))
    assert r["route_id"] and r["route_id"][1] == "Manufacture", "the pads' rule should use the Manufacture route"
    assert r["trigger"] == "auto", "the pads' rule must be Auto, so the scheduler acts on it"


def the_scheduler_made_eight_pads(env):
    rule = _rule_for(env, "Brake Pad Set")
    mos = env.call("mrp.production", "search_read", [("orderpoint_id", "in", [r["id"] for r in rule])],
                   fields=["name", "state", "product_qty"])
    assert mos, ("no manufacturing order from the pads' rule; in debug mode, Inventory > Operations > Procurement: run "
                 "scheduler. An automatic rule waits for the scheduler")
    assert mos[0]["product_qty"] == 8.0, "the rule's order is for %s, expected 15 minus 7 = 8" % mos[0]["product_qty"]
    assert mos[0]["state"] == "done", ("%s is not done; buy the components, Validate the Pick Components, Produce All, "
                                       "then Validate the Store Finished Product" % mos[0]["name"])


def components_were_bought_on_one_order(env):
    lines = env.call("purchase.order.line", "search_read",
                     [("product_id.name", "in", ["Friction Pad", "Backing Plate"]), ("product_qty", "=", 6)],
                     fields=["order_id", "partner_id", "qty_received"])
    orders = {l["order_id"][0] for l in lines}
    assert len(lines) == 2 and len(orders) == 1, (
        "expected one purchase order with 6 Friction Pad and 6 Backing Plate; give both Brembo Parts as vendor, "
        "select both suggestions in Replenishment and Order")
    assert all(l["qty_received"] == 6.0 for l in lines), "the components are not received; Confirm Order, Receive, Storage"
    left = env.call("stock.warehouse.orderpoint", "search_count",
                    [("product_id.name", "in", ["Friction Pad", "Backing Plate"])])
    assert not left, "the components still have reordering rules; ordering once removes the report's own suggestions"


def shelf_holds_fifteen_thirty_five_and_one(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "=", "internal")],
                    fields=["product_id", "location_id", "quantity"])
    stock = {}
    for r in rows:
        if r["location_id"][1] == "LFD/Stock":
            stock[r["product_id"][1]] = stock.get(r["product_id"][1], 0) + r["quantity"]
    want = {"Brake Pad Set": 15.0, "Engine Oil 5W-30 1L": 35.0, "Diagnostic Tablet": 1.0, "Friction Pad": 0, "Backing Plate": 0}
    for name, qty in want.items():
        assert stock.get(name, 0) == qty, "LFD/Stock should hold %s %s, it holds %s" % (qty, name, stock.get(name, 0))
    stuck = [(r["location_id"][1], r["product_id"][1], r["quantity"]) for r in rows
             if r["location_id"][1] != "LFD/Stock" and r["quantity"]]
    assert not stuck, "goods are sitting in a step location: %s. A transfer in a chain is not validated" % stuck


def _van(env):
    rows = env.call("stock.warehouse", "search_read", [("code", "=", "VAN")],
                    fields=["name", "reception_steps", "delivery_steps", "resupply_wh_ids", "buy_to_resupply",
                            "manufacture_to_resupply", "lot_stock_id"])
    assert rows, "no warehouse with Short Name VAN; Configuration > Warehouses > New, Service Van, VAN"
    return rows[0]


def van_warehouse_exists(env):
    van = _van(env)
    assert van["name"] == "Service Van", "the VAN warehouse is named %r, expected 'Service Van'" % van["name"]
    assert (van["reception_steps"], van["delivery_steps"]) == ("one_step", "ship_only"), (
        "the van should receive and deliver in 1 step, it is %s / %s" % (van["reception_steps"], van["delivery_steps"]))


def van_is_resupplied_from_the_depot_only(env):
    van = _van(env)
    lfd = env.call("stock.warehouse", "search", [("code", "=", "LFD")])
    assert van["resupply_wh_ids"] == lfd, "Resupply From on the van should tick LibreFleet Depot (and nothing else)"
    assert not van["buy_to_resupply"] and not van["manufacture_to_resupply"], (
        "untick Buy to Resupply and Manufacture to Resupply on the van: it is refilled from the depot only")
    assert env.call("stock.route", "search_count", [("supplied_wh_id.code", "=", "VAN"), ("supplier_wh_id.code", "=", "LFD")]), (
        "no route 'Service Van: Supply Product from LibreFleet Depot'; saving Resupply From creates it")


def van_has_an_automatic_oil_rule(env):
    rows = env.call("stock.warehouse.orderpoint", "search_read",
                    [("product_id.name", "=", "Engine Oil 5W-30 1L"), ("location_id.complete_name", "=", "VAN/Stock")],
                    fields=["trigger", "product_min_qty", "product_max_qty", "route_id"])
    assert rows, "no reordering rule for the oil in VAN/Stock; oil > Reordering Rules > New, Location VAN/Stock"
    r = rows[0]
    assert (r["product_min_qty"], r["product_max_qty"]) == (4.0, 10.0), (
        "the van's oil rule is Min %s / Max %s, expected 4 / 10" % (r["product_min_qty"], r["product_max_qty"]))
    assert r["route_id"] and "Supply Product from LibreFleet Depot" in r["route_id"][1], (
        "the van's oil rule should use the route Service Van: Supply Product from LibreFleet Depot")
    assert r["trigger"] == "auto", "the van's oil rule should be Auto"


def ten_bottles_travelled_to_the_van(env):
    out = env.call("stock.move", "search_read",
                   [("state", "=", "done"), ("product_id.name", "=", "Engine Oil 5W-30 1L"), ("product_uom_qty", "=", 10),
                    ("location_dest_id.usage", "=", "transit")], fields=["reference"])
    assert out, ("no done delivery of 10 bottles from the depot to Inter-warehouse transit; Order on the van's rule, "
                 "then Validate the depot's Pick, Pack and Delivery Orders")
    inn = env.call("stock.move", "search_read",
                   [("state", "=", "done"), ("product_id.name", "=", "Engine Oil 5W-30 1L"), ("product_uom_qty", "=", 10),
                    ("location_id.usage", "=", "transit"), ("location_dest_id.complete_name", "=", "VAN/Stock")],
                   fields=["reference"])
    assert inn, "the bottles left the depot but the van's receipt is not done; Validate VAN/IN, from Inter-warehouse transit"


def the_van_sold_two_bottles(env):
    lines = env.call("sale.order.line", "search_read",
                     [("order_id.warehouse_id.code", "=", "VAN"), ("order_id.state", "=", "sale"),
                      ("product_id.name", "=", "Engine Oil 5W-30 1L")], fields=["product_uom_qty", "qty_delivered"])
    assert lines, "no confirmed sales order from the Service Van warehouse; Other Info > Warehouse: Service Van"
    assert lines[0]["qty_delivered"] == lines[0]["product_uom_qty"] == 2.0, (
        "the van's order should deliver 2 bottles, it shows %s of %s; Validate VAN/OUT"
        % (lines[0]["qty_delivered"], lines[0]["product_uom_qty"]))


def coolant_is_on_consignment(env):
    assert _in_group(env, "stock.group_tracking_owner"), "the Consignment setting is off; Inventory > Configuration > Settings"
    done = env.call("stock.picking", "search_read",
                    [("owner_id.name", "=", "Nordic Lubricants"), ("state", "=", "done"),
                     ("move_ids.product_id.name", "=", "Coolant 5L")], fields=["name"])
    assert done, "no done receipt of Coolant 5L with Assign Owner Nordic Lubricants"


def garage_nord_has_instructions_and_three_coolant(env):
    assert _in_group(env, "stock.group_warning_stock"), (
        "the Partner-Specific Instructions setting is off; Inventory > Configuration > Settings, Operations")
    msg = env.call("res.partner", "search_read", [("name", "=", "Garage Nord")], fields=["picking_warn_msg"])[0]["picking_warn_msg"]
    assert msg, "Garage Nord has no stock instruction; contact form, Notes tab, Instructions on the Stock Operations"
    assert _done_moves(env, "OUT", "Coolant 5L", 3), (
        "no done delivery of 3 Coolant 5L; a Pick for Garage Nord, then Pack and Delivery Orders")


def two_shelves_two_warehouses(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "owner_id"])
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["owner_id"] and r["owner_id"][1])
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False): 15.0, ("LFD/Stock", "Engine Oil 5W-30 1L", False): 25.0,
            ("LFD/Stock", "Diagnostic Tablet", False): 1.0, ("LFD/Stock", "Coolant 5L", "Nordic Lubricants"): 9.0,
            ("VAN/Stock", "Engine Oil 5W-30 1L", False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " owned by %s" % key[2] if key[2] else "", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "goods are sitting where the chapter leaves none: %s. A transfer is not validated" % extra


def lots_and_expiry_are_on(env):
    assert _in_group(env, "stock.group_production_lot"), "the Lots & Serial Numbers setting is off; Inventory > Configuration > Settings, Traceability"
    rows = env.call("ir.module.module", "search_read", [("name", "=", "product_expiry"), ("state", "=", "installed")], fields=["name"])
    assert rows, "Expiration Dates is not installed; tick it in the same Traceability block and Save (the module is product_expiry)"


def tablet_is_serial_tracked_with_a_prefix(env):
    t = env.call("product.template", "search_read", [("name", "=", "Diagnostic Tablet")], fields=["tracking", "lot_sequence_id"])[0]
    assert t["tracking"] == "serial", "the tablet's tracking is %r; General Information, Track Inventory: By Unique Serial Number" % t["tracking"]
    seq = env.call("ir.sequence", "read", [t["lot_sequence_id"][0]], ["prefix"])[0] if t["lot_sequence_id"] else {}
    assert seq.get("prefix") == "DT-", "the tablet's Custom Lot/Serial should be DT- (Inventory tab, Traceability)"


def every_tablet_has_a_serial(env):
    rows = env.call("stock.quant", "search_read", [("product_id.name", "=", "Diagnostic Tablet"), ("location_id.usage", "=", "internal")],
                    fields=["lot_id", "quantity"])
    have = sorted(r["lot_id"][1] for r in rows if r["quantity"] and r["lot_id"])
    loose = [r for r in rows if r["quantity"] and not r["lot_id"]]
    assert not loose, "a tablet is still on the shelf without a serial; Physical Inventory: count the no-serial line 0 and add one with a serial"
    assert have == ["DT-0000001", "DT-0000002", "DT-0000003"], (
        "the shelf should hold tablets DT-0000001 to DT-0000003, it holds %s; receive 2 with Generate Serials from DT-0000002" % have)


def brake_fluid_has_lots_and_dates(env):
    rows = env.call("product.template", "search_read", [("name", "=", "Brake Fluid DOT 4 1L")],
                    fields=["tracking", "use_expiration_date", "expiration_time", "use_time", "removal_time", "alert_time"])
    assert rows, "no product Brake Fluid DOT 4 1L; Products > New"
    r = rows[0]
    assert r["tracking"] == "lot" and r["use_expiration_date"], "Brake Fluid must be tracked By Lots with Expiration Date ticked"
    got = (r["expiration_time"], r["use_time"], r["removal_time"], r["alert_time"])
    assert got == (365, 60, 30, 45), "its dates should be 365 / 60 / 30 / 45 days, they are %s" % (got,)


def depot_stock_removes_first_expiry_first(env):
    rows = env.call("stock.location", "search_read", [("complete_name", "=", "LFD/Stock")], fields=["removal_strategy_id"])
    rs = rows[0]["removal_strategy_id"]
    assert rs and "FEFO" in rs[1], "LFD/Stock's Removal Strategy is %r; Configuration > Locations > LFD/Stock, First Expiry First Out (FEFO)" % (rs and rs[1])


def lot_bf001_was_recalled(env):
    lot = env.call("stock.lot", "search_read", [("name", "=", "BF-001")], fields=["id", "product_expiry_alert"])
    assert lot, "no lot BF-001; receive 24 Brake Fluid with Generate Serials/Lots, first lot BF-001, 12 per lot"
    moves = env.call("stock.move.line", "search_read", [("lot_id", "=", lot[0]["id"]), ("state", "=", "done")],
                     fields=["location_id", "location_dest_id", "quantity"])
    usage = {l["id"]: l["usage"] for l in env.call("stock.location", "search_read", [], fields=["usage"])}
    sold = [m for m in moves if usage[m["location_dest_id"][0]] == "customer"]
    back = [m for m in moves if usage[m["location_id"][0]] == "customer"]
    scrapped = [m for m in moves if usage[m["location_dest_id"][0]] == "inventory"]
    assert sold, "BF-001 never left for a customer; sell 6 Brake Fluid to Garage Nord, FEFO picks BF-001"
    assert back, "the 6 bottles of BF-001 were not returned; on the delivery, Return, Return All, then Validate twice"
    assert lot[0]["product_expiry_alert"], "BF-001 is not blocked; set its Expiration Date to a moment in the past"
    assert sum(m["quantity"] for m in scrapped) == 12, "BF-001 should be scrapped entirely, 12 bottles; Operations > Scrap"


def shelf_after_the_recall(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "lot_id", "owner_id"])
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["lot_id"] and r["lot_id"][1])
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False): 15.0, ("LFD/Stock", "Engine Oil 5W-30 1L", False): 25.0,
            ("LFD/Stock", "Coolant 5L", False): 9.0, ("LFD/Stock", "Brake Fluid DOT 4 1L", "BF-002"): 12.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000001"): 1.0, ("LFD/Stock", "Diagnostic Tablet", "DT-0000002"): 1.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000003"): 1.0, ("VAN/Stock", "Engine Oil 5W-30 1L", False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " lot %s" % key[2] if key[2] else "", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "unexpected stock: %s. A transfer, return or scrap is not finished" % extra


def packages_are_on(env):
    assert _in_group(env, "stock.group_tracking_lot"), "the Packages setting is off; Inventory > Configuration > Settings, Operations"


def _package_types(env):
    rows = env.call("stock.package.type", "search_read", [],
                    fields=["name", "package_use", "sequence_code", "barcode", "packaging_length", "width", "height", "max_weight"])
    return {r["name"]: r for r in rows}


def carton_pallet_and_tote_exist(env):
    types = _package_types(env)
    for name in ("Carton", "Pallet", "Tote"):
        assert name in types, "no package type %s; Configuration > Package Types (the Tote comes in by Import records)" % name
    c, p, t = types["Carton"], types["Pallet"], types["Tote"]
    assert (c["sequence_code"], c["barcode"]) == ("CTN", "CARTON"), "Carton needs Sequence Prefix CTN and Barcode CARTON"
    assert (c["packaging_length"], c["width"], c["height"], c["max_weight"]) == (400, 300, 300, 20), (
        "Carton's Dimensions tab should read 400 x 300 x 300 mm, Max Weight 20 kg")
    assert p["sequence_code"] == "PAL", "Pallet needs Sequence Prefix PAL"
    assert c["package_use"] == p["package_use"] == "disposable", "Carton and Pallet must stay disposable, or they get emptied at the next step"
    assert t["package_use"] == "reusable", ("the Tote is %r; import it with the column Package Use set to Reusable Box (totes): "
                                            "the form has no such field" % t["package_use"])


def receipts_and_pick_ask_for_a_type(env):
    rows = env.call("stock.picking.type", "search_read", [("warehouse_id.code", "=", "LFD")], fields=["sequence_code", "set_package_type"])
    on = {r["sequence_code"] for r in rows if r["set_package_type"]}
    assert {"IN", "PICK"} <= on, ("Set Package Type should be ticked on LibreFleet Depot: Receipts and Pick "
                                  "(Configuration > Operations Types), it is on %s" % sorted(on))
    assert "PACK" not in on, "leave Set Package Type off on Pack: there the Pack of 6 picks the Carton by itself"


def pack_of_6_is_a_carton(env):
    rows = env.call("uom.uom", "search_read", [("name", "=", "Pack of 6")], fields=["package_type_id"])
    assert rows and rows[0]["package_type_id"] and rows[0]["package_type_id"][1] == "Carton", (
        "Configuration > Units & Packagings > Pack of 6, Package Type: Carton")


def oil_and_its_pack_have_barcodes(env):
    oil = env.call("product.product", "search_read", [("name", "=", "Engine Oil 5W-30 1L")], fields=["barcode"])[0]
    assert oil["barcode"] == "5901234123457", "the oil's Barcode (General Information tab) should be 5901234123457, it is %r" % oil["barcode"]
    rows = env.call("product.uom", "search_read", [("product_id", "=", oil["id"]), ("uom_id.name", "=", "Pack of 6")], fields=["barcode"])
    assert rows and rows[0]["barcode"] == "15901234123454", (
        "Pack of 6 > Packaging Barcodes needs a line for the oil with 15901234123454")


def a_pallet_of_two_cartons_is_stored(env):
    pallets = env.call("stock.package", "search_read", [("package_type_id.name", "=", "Pallet"), ("location_id.complete_name", "=", "LFD/Stock")],
                       fields=["child_package_ids"])
    assert pallets, "no Pallet package in LFD/Stock; put the two cartons on a pallet at the receipt, then Validate the Storage"
    kids = env.call("stock.package", "read", pallets[0]["child_package_ids"], ["package_type_id"])
    assert [k["package_type_id"] and k["package_type_id"][1] for k in kids] == ["Carton", "Carton"], (
        "the pallet should contain exactly two cartons, it contains %s" % [k["package_type_id"] for k in kids])
    quants = env.call("stock.quant", "search_read", [("package_id", "in", pallets[0]["child_package_ids"])], fields=["product_id", "quantity"])
    got = sorted((q["product_id"][1], q["quantity"]) for q in quants)
    assert got == [("Brake Pad Set", 10.0), ("Engine Oil 5W-30 1L", 12.0)], "the cartons should hold 12 oil and 10 pads, they hold %s" % got


def the_tote_was_emptied_and_the_carton_shipped(env):
    tote = env.call("stock.package", "search_read", [("package_type_id.name", "=", "Tote")], fields=["quant_ids"])
    assert tote, "no Tote package; Products > Packages > New, Package Type Tote"
    assert not tote[0]["quant_ids"], "the tote still holds goods; the Pack step should take them out of it"
    picked = env.call("stock.move.line", "search_count", [("result_package_id", "=", tote[0]["id"]), ("state", "=", "done"),
                                                           ("picking_type_id.sequence_code", "=", "PICK")])
    assert picked, "the tote was never used at a Pick; in the Pick's Put in Pack choose the existing Package"
    shipped = env.call("stock.move.line", "search_read", [("state", "=", "done"), ("location_dest_id.usage", "=", "customer"),
                                                          ("result_package_id.package_type_id.name", "=", "Carton"),
                                                          ("move_id.packaging_uom_id.name", "=", "Pack of 6")], fields=["quantity"])
    assert shipped and shipped[0]["quantity"] == 12, ("no carton of 12 oil reached Garage Nord; sell 2 Pack of 6, "
                                                      "Put in Pack on the Pack step, Validate the delivery")


def shelf_after_packing(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "lot_id", "package_id"])
    kinds = {p["id"]: p["package_type_id"] and p["package_type_id"][1]
             for p in env.call("stock.package", "search_read", [], fields=["package_type_id"])}
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["lot_id"] and r["lot_id"][1], r["package_id"] and kinds[r["package_id"][0]])
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False, False): 15.0, ("LFD/Stock", "Brake Pad Set", False, "Carton"): 10.0,
            ("LFD/Stock", "Engine Oil 5W-30 1L", False, False): 13.0, ("LFD/Stock", "Engine Oil 5W-30 1L", False, "Carton"): 12.0,
            ("LFD/Stock", "Coolant 5L", False, False): 9.0, ("LFD/Stock", "Brake Fluid DOT 4 1L", "BF-002", False): 12.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000001", False): 1.0, ("LFD/Stock", "Diagnostic Tablet", "DT-0000002", False): 1.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000003", False): 1.0, ("VAN/Stock", "Engine Oil 5W-30 1L", False, False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " in a %s" % key[3] if key[3] else " loose", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "unexpected stock: %s. A transfer is not finished" % extra


def the_oil_is_in_category_fluids(env):
    rows = env.call("product.category", "search_read", [("complete_name", "=", "Goods / Fluids")], fields=["id"])
    assert rows, "no product category Goods / Fluids; Configuration > Product Categories > New, Parent Category Goods"
    oil = env.call("product.product", "search_read", [("name", "=", "Engine Oil 5W-30 1L")], fields=["categ_id"])[0]
    assert oil["categ_id"] and oil["categ_id"][0] == rows[0]["id"], "the oil's Category (General Information) should be Goods / Fluids"


def two_storage_categories_exist(env):
    cats = {c["name"]: c for c in env.call("stock.storage.category", "search_read", [], fields=["name", "allow_new_product", "capacity_ids"])}
    for name in ("Parts Shelf", "Pallet Bay"):
        assert name in cats, "no storage category %s; Configuration > Storage Categories > New" % name
    assert cats["Parts Shelf"]["allow_new_product"] == "same", "Parts Shelf: Allow New Product should be If all products are same"
    assert cats["Pallet Bay"]["allow_new_product"] == "empty", "Pallet Bay: Allow New Product should be If the location is empty"
    caps = env.call("stock.storage.category.capacity", "search_read", [("storage_category_id", "in", [cats["Parts Shelf"]["id"], cats["Pallet Bay"]["id"]])],
                    fields=["storage_category_id", "product_id", "package_type_id", "quantity"])
    got = sorted((c["storage_category_id"][1], (c["product_id"] or c["package_type_id"])[1], c["quantity"]) for c in caps)
    assert got == [("Pallet Bay", "Pallet", 1.0), ("Parts Shelf", "Brake Pad Set", 20.0)], (
        "capacities should be 20 Brake Pad Set per Parts Shelf and 1 Pallet per Pallet Bay, they are %s" % got)


def the_shelves_have_their_categories(env):
    rows = env.call("stock.location", "search_read", [("complete_name", "like", "LFD/Stock/")], fields=["complete_name", "storage_category_id"])
    have = {r["complete_name"]: r["storage_category_id"] and r["storage_category_id"][1] for r in rows}
    want = {"LFD/Stock/Shelf A": "Parts Shelf", "LFD/Stock/Shelf B": "Parts Shelf", "LFD/Stock/Pallet Bay 1": "Pallet Bay",
            "LFD/Stock/Pallet Bay 2": "Pallet Bay", "LFD/Stock/Fluids Rack": False}
    for name, cat in want.items():
        assert name in have, "no location %s; Configuration > Locations > New, Parent Location LFD/Stock" % name
        assert have[name] == cat, "%s should have Storage Category %s, it has %s" % (name, cat or "none", have[name] or "none")


def three_putaway_rules_on_lfd_stock(env):
    rules = env.call("stock.putaway.rule", "search_read", [("location_in_id.complete_name", "=", "LFD/Stock")],
                     fields=["product_id", "category_id", "package_type_ids", "location_out_id", "sublocation", "storage_category_id"])
    def find(test, what):
        hit = [r for r in rules if test(r)]
        assert hit, "no putaway rule for %s arriving in LFD/Stock; Configuration > Putaway Rules" % what
        return hit[0]
    pads = find(lambda r: r["product_id"] and r["product_id"][1] == "Brake Pad Set", "Brake Pad Set")
    assert (pads["sublocation"], pads["storage_category_id"] and pads["storage_category_id"][1]) == ("closest_location", "Parts Shelf"), (
        "the pads rule should be Sublocation Closest Location, Having Category Parts Shelf")
    fluids = find(lambda r: r["category_id"] and r["category_id"][1] == "Goods / Fluids", "the category Goods / Fluids")
    assert fluids["location_out_id"][1] == "LFD/Stock/Fluids Rack", "the Fluids rule should Store to LFD/Stock/Fluids Rack"
    pallet = find(lambda r: r["package_type_ids"], "the package type Pallet")
    assert (pallet["sublocation"], pallet["storage_category_id"] and pallet["storage_category_id"][1]) == ("closest_location", "Pallet Bay"), (
        "the Pallet rule should be Sublocation Closest Location, Having Category Pallet Bay")


def putaway_chose_the_shelves(env):
    lines = env.call("stock.move.line", "search_read", [("state", "=", "done"), ("picking_type_id.sequence_code", "=", "STOR"),
                                                        ("location_dest_id.complete_name", "in", ["LFD/Stock/Shelf A", "LFD/Stock/Shelf B", "LFD/Stock/Fluids Rack"])],
                     fields=["product_id", "location_dest_id", "quantity"])
    got = sorted((l["product_id"][1], l["location_dest_id"][1], l["quantity"]) for l in lines)
    want = [("Brake Pad Set", "LFD/Stock/Shelf A", 15.0), ("Brake Pad Set", "LFD/Stock/Shelf B", 10.0), ("Engine Oil 5W-30 1L", "LFD/Stock/Fluids Rack", 6.0)]
    assert got == want, ("Storage should have put 15 pads on Shelf A, then 10 on Shelf B (A was too full) and 6 oil on the Fluids Rack; "
                         "it did %s. Receive the pads in two receipts, 15 then 10" % got)


def the_pallet_sits_in_bay_1(env):
    lines = env.call("stock.move.line", "search_read", [("state", "=", "done"), ("picking_type_id.sequence_code", "=", "INT"),
                                                        ("result_package_id.parent_package_id.name", "=", "PAL0000001")],
                     fields=["location_dest_id"])
    assert lines and {l["location_dest_id"][1] for l in lines} == {"LFD/Stock/Pallet Bay 1"}, (
        "no done internal transfer moved PAL0000001 to LFD/Stock/Pallet Bay 1; Internal Transfers > New, Move a Pack")


def lifo_took_the_newest_oil(env):
    cat = env.call("product.category", "search_read", [("complete_name", "=", "Goods / Fluids")], fields=["removal_strategy_id"])
    assert cat and cat[0]["removal_strategy_id"] and "LIFO" in cat[0]["removal_strategy_id"][1], (
        "Goods / Fluids should have Force Removal Strategy Last In First Out (LIFO)")
    lines = env.call("stock.move.line", "search_read", [("state", "=", "done"), ("picking_type_id.sequence_code", "=", "PICK"),
                                                        ("product_id.name", "=", "Engine Oil 5W-30 1L"), ("picking_partner_id.name", "=", "Garage Nord"),
                                                        ("location_id.complete_name", "=", "LFD/Stock/Fluids Rack")], fields=["quantity"])
    assert lines and lines[0]["quantity"] == 6, ("no done Pick of 6 oil from the Fluids Rack; sell 6 to Garage Nord, set LIFO, "
                                                 "Unreserve and Check Availability on the Pick, then finish the chain")


def shelf_after_putaway(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "lot_id", "package_id"])
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["lot_id"] and r["lot_id"][1], bool(r["package_id"]))
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False, False): 15.0, ("LFD/Stock/Shelf A", "Brake Pad Set", False, False): 15.0,
            ("LFD/Stock/Shelf B", "Brake Pad Set", False, False): 10.0, ("LFD/Stock/Pallet Bay 1", "Brake Pad Set", False, True): 10.0,
            ("LFD/Stock", "Engine Oil 5W-30 1L", False, False): 13.0, ("LFD/Stock/Pallet Bay 1", "Engine Oil 5W-30 1L", False, True): 12.0,
            ("LFD/Stock", "Coolant 5L", False, False): 9.0, ("LFD/Stock", "Brake Fluid DOT 4 1L", "BF-002", False): 12.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000001", False): 1.0, ("LFD/Stock", "Diagnostic Tablet", "DT-0000002", False): 1.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000003", False): 1.0, ("VAN/Stock", "Engine Oil 5W-30 1L", False, False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " in packages" if key[3] else "", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "unexpected stock: %s. A transfer is not finished" % extra


def the_oil_count_was_reverted(env):
    moves = env.call("stock.move", "search_read", [("is_inventory", "=", True), ("state", "=", "done"), ("product_id.name", "=", "Engine Oil 5W-30 1L")],
                     fields=["reference", "location_id", "location_dest_id", "quantity"])
    out = [m for m in moves if m["location_id"][1] == "LFD/Stock" and m["quantity"] == 1]
    back = [m for m in moves if m["location_dest_id"][1] == "LFD/Stock" and "[reverted]" in m["reference"]]
    assert out, "no applied count of the oil in LFD/Stock at 12 (one missing); Physical Inventory, Counted 12, Apply"
    assert back, "the oil count was not reverted; its History, select the line, Actions > Revert Inventory Adjustment"


def the_shelves_were_counted_with_a_reason(env):
    moves = env.call("stock.move", "search_read", [("is_inventory", "=", True), ("state", "=", "done"), ("product_id.name", "=", "Brake Pad Set"),
                                                   ("location_id.complete_name", "in", ["LFD/Stock/Shelf A", "LFD/Stock/Shelf B"])],
                     fields=["reference", "location_id", "quantity"])
    named = {m["location_id"][1]: m for m in moves if not m["reference"].startswith("Product Quantity")}
    assert set(named) == {"LFD/Stock/Shelf A", "LFD/Stock/Shelf B"}, (
        "Shelf A and Shelf B should both be counted and applied together with an Inventory Reason (select both, header Apply)")
    assert named["LFD/Stock/Shelf B"]["quantity"] == 1, "Shelf B was counted at 9 of 10: the adjustment should remove 1 pad"


def bf002_was_scrapped_as_damaged(env):
    rows = env.call("stock.scrap", "search_read", [("state", "=", "done"), ("lot_id.name", "=", "BF-002")], fields=["scrap_qty", "scrap_reason_tag_ids"])
    assert rows and rows[0]["scrap_qty"] == 1, "no done scrap of 1 Brake Fluid, lot BF-002; Operations > Scrap"
    tags = env.call("stock.scrap.reason.tag", "read", rows[0]["scrap_reason_tag_ids"], ["name"])
    assert "Damaged" in [t["name"] for t in tags], "the scrap's Scrap Reason should be Damaged"


def the_conflict_kept_the_difference(env):
    added = env.call("stock.move.line", "search_count", [("move_id.is_inventory", "=", True), ("state", "=", "done"), ("lot_id.name", "=", "BF-002"),
                                                         ("location_dest_id.complete_name", "=", "LFD/Stock"), ("quantity", ">", 0)])
    assert not added, "a count put a bottle of BF-002 back into LFD/Stock: on the conflict choose Keep Difference, not Keep Counted Quantity"
    q = env.call("stock.quant", "search_read", [("lot_id.name", "=", "BF-002"), ("location_id.complete_name", "=", "LFD/Stock")], fields=["quantity", "inventory_quantity_set"])
    assert q and not q[0]["inventory_quantity_set"], "BF-002 still has a count waiting; Apply it (Keep Difference)"


def the_coolant_was_relocated(env):
    q = env.call("stock.quant", "search_read", [("product_id.name", "=", "Coolant 5L"), ("quantity", ">", 0), ("location_id.usage", "=", "internal")],
                 fields=["location_id", "owner_id", "quantity"])
    assert q and q[0]["location_id"][1] == "LFD/Stock/Fluids Rack", "the coolant should sit in LFD/Stock/Fluids Rack; Physical Inventory, Actions > Relocate"
    assert q[0]["owner_id"] and q[0]["owner_id"][1] == "Nordic Lubricants", "the relocated coolant should still be owned by Nordic Lubricants"


def shelf_a_is_counted_every_30_days(env):
    r = env.call("stock.location", "search_read", [("complete_name", "=", "LFD/Stock/Shelf A")], fields=["cyclic_inventory_frequency"])[0]
    assert r["cyclic_inventory_frequency"] == 30, "LFD/Stock/Shelf A: Inventory Frequency should be 30 days"


def picks_are_batched_automatically(env):
    mod = env.call("ir.module.module", "search_read", [("name", "=", "stock_picking_batch"), ("state", "=", "installed")], fields=["name"])
    assert mod, "Batch, Wave & Cluster Transfers is not installed; Inventory > Configuration > Settings, Operations"
    t = env.call("stock.picking.type", "search_read", [("warehouse_id.code", "=", "LFD"), ("sequence_code", "=", "PICK")],
                 fields=["auto_batch", "batch_group_by_src_loc"])[0]
    assert t["auto_batch"] and t["batch_group_by_src_loc"], "LibreFleet Depot: Pick needs Automatic Batches and Batch Grouping Source Location"


def one_batch_picked_two_orders(env):
    rows = env.call("stock.picking.batch", "search_read", [("state", "=", "done"), ("picking_type_id.sequence_code", "=", "PICK")], fields=["picking_ids"])
    assert rows, "no done batch of Picks; two sales of Brake Fluid, then Validate the batch Odoo made"
    picks = env.call("stock.picking", "read", rows[0]["picking_ids"], ["partner_id", "origin"])
    assert sorted(p["partner_id"][1] for p in picks) == ["Garage Nord", "Garage Sud"], (
        "the batch should hold the Picks of Garage Nord and Garage Sud, it holds %s" % [p["partner_id"] for p in picks])
    outs = env.call("stock.picking", "search_count", [("origin", "in", [p["origin"] for p in picks]), ("picking_type_id.sequence_code", "=", "OUT"), ("state", "=", "done")])
    assert outs == 2, "both orders should be delivered; validate the Packs and Deliveries (Actions > Validate on a selection)"


def shelf_after_counting(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "lot_id", "package_id"])
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["lot_id"] and r["lot_id"][1], bool(r["package_id"]))
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False, False): 15.0, ("LFD/Stock/Shelf A", "Brake Pad Set", False, False): 15.0,
            ("LFD/Stock/Shelf B", "Brake Pad Set", False, False): 9.0, ("LFD/Stock/Pallet Bay 1", "Brake Pad Set", False, True): 10.0,
            ("LFD/Stock", "Engine Oil 5W-30 1L", False, False): 13.0, ("LFD/Stock/Pallet Bay 1", "Engine Oil 5W-30 1L", False, True): 12.0,
            ("LFD/Stock/Fluids Rack", "Coolant 5L", False, False): 9.0, ("LFD/Stock", "Brake Fluid DOT 4 1L", "BF-002", False): 6.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000001", False): 1.0, ("LFD/Stock", "Diagnostic Tablet", "DT-0000002", False): 1.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000003", False): 1.0, ("VAN/Stock", "Engine Oil 5W-30 1L", False, False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " lot %s" % key[2] if key[2] else "", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "unexpected stock: %s. A count, scrap or transfer is not finished" % extra


def shipping_dropship_and_subcontracting_are_on(env):
    want = {"stock_delivery", "stock_dropshipping", "mrp_subcontracting"}
    rows = env.call("ir.module.module", "search_read", [("name", "in", sorted(want)), ("state", "=", "installed")], fields=["name"])
    missing = want - {r["name"] for r in rows}
    assert not missing, "not installed: %s; Inventory > Configuration > Settings, tick Delivery Methods, Dropshipping and Subcontracting" % sorted(missing)


def the_oil_has_shipping_data(env):
    p = env.call("product.template", "search_read", [("name", "=", "Engine Oil 5W-30 1L")], fields=["weight", "hs_code", "country_of_origin"])[0]
    assert p["weight"] == 1, "Engine Oil 5W-30 1L: Weight should be 1 kg (Inventory tab), it is %s" % p["weight"]
    assert p["hs_code"] == "271019", "Engine Oil 5W-30 1L: HS Code should be 271019, it is %r" % p["hs_code"]
    assert p["country_of_origin"] and p["country_of_origin"][1] == "Germany", "Engine Oil 5W-30 1L: Origin of Goods should be Germany"


def depot_van_is_free_over_100(env):
    rows = env.call("delivery.carrier", "search_read", [("name", "=", "Depot Van")], fields=["delivery_type", "fixed_price", "free_over", "amount"])
    assert rows, "no delivery method named Depot Van; Inventory > Configuration > Delivery Methods > New"
    c = rows[0]
    assert c["delivery_type"] == "fixed" and c["fixed_price"] == 15, "Depot Van: Provider Fixed Price, Fixed Price 15 (set it after the Delivery Product)"
    assert c["free_over"] and c["amount"] == 100, "Depot Van: tick Free if order amount is above, 100"


def the_courier_prices_by_weight(env):
    rows = env.call("delivery.carrier", "search_read", [("name", "=", "Courier by Weight")], fields=["delivery_type", "price_rule_ids", "tracking_url"])
    assert rows and rows[0]["delivery_type"] == "base_on_rule", "no Based on Rules delivery method named Courier by Weight"
    rules = env.call("delivery.price.rule", "read", rows[0]["price_rule_ids"],
                     ["variable", "operator", "max_value", "list_base_price", "list_price", "variable_factor"])
    got = [(r["variable"], r["operator"], r["max_value"], r["list_base_price"], r["list_price"], r["variable_factor"]) for r in rules]
    assert got == [("weight", "<=", 5, 8, 0, "weight"), ("weight", "<=", 30, 5, 1, "weight")], (
        "Courier by Weight should have two rules, in order: weight <= 5 then $8; weight <= 30 then $5 + $1 x weight. It has %s" % got)
    assert "<shipmenttrackingnumber>" in (rows[0]["tracking_url"] or ""), "Courier by Weight: Tracking Link must contain <shipmenttrackingnumber>"


def the_courier_order_charged_13(env):
    lines = env.call("sale.order.line", "search_read", [("order_id.partner_id.name", "=", "Garage Sud"), ("order_id.state", "=", "sale"),
                                                        ("is_delivery", "=", True), ("order_id.carrier_id.name", "=", "Courier by Weight")],
                     fields=["price_unit", "order_id"])
    assert lines, "no confirmed order of Garage Sud with a Courier by Weight line; sell 8 oil, Add shipping, Confirm"
    assert lines[0]["price_unit"] == 13, "8 kg should cost $5 + $1 x 8 = $13, the line says %s" % lines[0]["price_unit"]


def the_courier_delivery_has_a_tracking_number(env):
    rows = env.call("stock.picking", "search_read", [("picking_type_id.sequence_code", "=", "OUT"), ("state", "=", "done"),
                                                     ("carrier_id.name", "=", "Courier by Weight")],
                    fields=["carrier_tracking_ref", "shipping_weight", "partner_id"])
    assert rows, "no done Delivery with carrier Courier by Weight; finish the Pick, Pack and Delivery of the courier order"
    assert rows[0]["carrier_tracking_ref"] == "LF123456", "the Delivery's Tracking Reference (Additional Info) should be LF123456"
    assert rows[0]["shipping_weight"] == 8, "the Delivery's Weight for shipping should be 8 kg, it is %s" % rows[0]["shipping_weight"]


def the_tyres_were_dropshipped(env):
    p = env.call("product.template", "search_read", [("name", "=", "Tyre 205/55 R16")], fields=["route_ids", "seller_ids"])
    assert p, "no product named Tyre 205/55 R16"
    routes = env.call("stock.route", "read", p[0]["route_ids"], ["name"])
    assert [r["name"] for r in routes] == ["Dropship"], "Tyre 205/55 R16 should have the Dropship route ticked, and only that one"
    ds = env.call("stock.picking", "search_read", [("picking_type_id.code", "=", "dropship"), ("state", "=", "done"),
                                                   ("product_id.name", "=", "Tyre 205/55 R16")], fields=["partner_id", "location_dest_id"])
    assert ds and ds[0]["partner_id"][1] == "Pneu Direct", "no done Dropship of the tyres from Pneu Direct; sell 4 to Garage Nord, confirm the PO, validate the DS"
    stock = env.call("stock.quant", "search_count", [("product_id.name", "=", "Tyre 205/55 R16"), ("location_id.usage", "=", "internal"), ("quantity", "!=", 0)])
    assert not stock, "a tyre is in an internal location: a dropship never touches your stock"


def the_engine_was_subcontracted(env):
    bom = env.call("mrp.bom", "search_read", [("product_tmpl_id.name", "=", "Rebuilt Engine"), ("type", "=", "subcontract")],
                   fields=["subcontractor_ids", "bom_line_ids"])
    assert bom, "Rebuilt Engine needs a BoM of type Subcontracting"
    subs = env.call("res.partner", "read", bom[0]["subcontractor_ids"], ["name"])
    assert [s["name"] for s in subs] == ["Atelier Moteur"], "the Subcontracting BoM's Subcontractors should be Atelier Moteur"
    line = env.call("mrp.bom.line", "read", bom[0]["bom_line_ids"], ["product_id", "product_qty"])
    assert [(l["product_id"][1], l["product_qty"]) for l in line] == [("Engine Oil 5W-30 1L", 5)], "the BoM's only component: 5 Engine Oil 5W-30 1L"
    res = env.call("stock.picking", "search_count", [("picking_type_id.sequence_code", "=", "RES"), ("state", "=", "done"), ("partner_id.name", "=", "Atelier Moteur")])
    assert res, "the oil never went to Atelier Moteur: validate the Resupply transfer of the purchase order"
    mo = env.call("mrp.production", "search_count", [("product_id.name", "=", "Rebuilt Engine"), ("state", "=", "done"), ("subcontractor_id.name", "=", "Atelier Moteur")])
    assert mo, "no done subcontracting production; validate the purchase order's Receipt"


def shelf_after_shipping(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "lot_id", "package_id"])
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["lot_id"] and r["lot_id"][1], bool(r["package_id"]))
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False, False): 15.0, ("LFD/Stock/Shelf A", "Brake Pad Set", False, False): 15.0,
            ("LFD/Stock/Shelf B", "Brake Pad Set", False, False): 9.0, ("LFD/Stock/Pallet Bay 1", "Brake Pad Set", False, True): 10.0,
            ("LFD/Stock", "Engine Oil 5W-30 1L", False, False): 12.0, ("LFD/Stock", "Rebuilt Engine", False, False): 1.0,
            ("LFD/Stock/Fluids Rack", "Coolant 5L", False, False): 9.0, ("LFD/Stock", "Brake Fluid DOT 4 1L", "BF-002", False): 6.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000001", False): 1.0, ("LFD/Stock", "Diagnostic Tablet", "DT-0000002", False): 1.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000003", False): 1.0, ("VAN/Stock", "Engine Oil 5W-30 1L", False, False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " lot %s" % key[2] if key[2] else "", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "unexpected stock: %s. A transfer of the courier order or the subcontracting is not finished" % extra


def the_oil_costs_6(env):
    p = env.call("product.product", "search_read", [("name", "=", "Engine Oil 5W-30 1L")], fields=["standard_price", "cost_method", "total_value", "qty_available"])[0]
    assert p["cost_method"] == "standard", "the oil should stay on Standard Price, its category Goods / Fluids is %s" % p["cost_method"]
    assert p["standard_price"] == 6, "Engine Oil 5W-30 1L: Cost should be 6, it is %s" % p["standard_price"]
    assert p["total_value"] == 120, "20 bottles at $6 should be worth $120, Odoo says %s" % p["total_value"]


def filters_are_avco_and_perpetual(env):
    c = env.call("product.category", "search_read", [("complete_name", "=", "Goods / Filters")], fields=["property_cost_method", "property_valuation"])
    assert c, "no product category Goods / Filters"
    assert c[0]["property_cost_method"] == "average", "Goods / Filters: Costing Method should end on Average Cost (AVCO)"
    assert c[0]["property_valuation"] == "real_time", "Goods / Filters: Inventory Valuation should end on Perpetual (at invoicing)"


def the_receipts_carry_their_values(env):
    moves = env.call("stock.move", "search_read", [("product_id.name", "=", "Air Filter"), ("is_in", "=", True)], fields=["reference", "value"], order="id")
    got = [m["value"] for m in moves]
    assert got == [80, 100, 117], ("the three air filter receipts should be worth $80, $100 and $117 (10 at $8, 10 at $10, "
                                   "10 billed at $9.90 plus $18 freight); they are %s" % got)


def fifo_valued_the_first_sale(env):
    out = env.call("stock.move", "search_read", [("product_id.name", "=", "Air Filter"), ("is_out", "=", True), ("partner_id.name", "=", "Garage Nord")],
                   fields=["quantity", "value"])
    assert out and out[0]["quantity"] == 12, "no delivery of 12 air filters to Garage Nord"
    assert out[0]["value"] == 100, "under FIFO the 12 filters cost 10 x $8 + 2 x $10 = $100; the delivery says %s. Was Goods / Filters on FIFO then?" % out[0]["value"]


def the_bill_said_9_90(env):
    lines = env.call("account.move.line", "search_read", [("move_id.move_type", "=", "in_invoice"), ("parent_state", "=", "posted"),
                                                          ("product_id.name", "=", "Air Filter")], fields=["price_unit", "quantity"])
    assert lines and lines[0]["price_unit"] == 9.9, "no posted vendor bill for the last 10 air filters at $9.90 (Purchase Orders list, Create Bills)"


def freight_landed_on_the_receipt(env):
    lc = env.call("stock.landed.cost", "search_read", [("state", "=", "done")], fields=["picking_ids", "cost_lines", "amount_total"])
    assert lc, "no posted landed cost; Inventory > Operations > Landed Costs"
    line = env.call("stock.landed.cost.lines", "read", lc[0]["cost_lines"], ["product_id", "price_unit", "split_method"])[0]
    assert (line["product_id"][1], line["price_unit"], line["split_method"]) == ("Freight", 18, "by_quantity"), (
        "the landed cost should be Freight, $18, By Quantity; it is %s" % line)


def the_books_were_closed_at_309(env):
    mv = env.call("account.move", "search_read", [("ref", "=", "Stock Closing"), ("state", "=", "posted")], fields=["amount_total", "journal_id"])
    assert mv, "no posted Stock Closing entry; open /odoo/stock-valuation-closing, Generate Entry, Post"
    assert mv[0]["amount_total"] == 309, "the closing should move $309 (oil $120 + filters $189); it moved %s" % mv[0]["amount_total"]


def the_invoice_posted_cogs(env):
    lines = env.call("account.move.line", "search_read", [("move_id.move_type", "=", "out_invoice"), ("parent_state", "=", "posted"),
                                                          ("display_type", "=", "cogs"), ("product_id.name", "=", "Air Filter")],
                     fields=["account_id", "debit", "credit"])
    assert lines, "no cost of goods sold on a posted invoice; switch Filters to Perpetual first, then sell 2 to Garage Sud and invoice"
    assert sum(l["debit"] for l in lines) == 21 and sum(l["credit"] for l in lines) == 21, (
        "2 filters at $10.50 should post $21 of COGS; the lines are %s" % [(l["account_id"][1], l["debit"], l["credit"]) for l in lines])


def stock_value_matches_the_books(env):
    vals = env.call("product.product", "search_read", [("name", "in", ["Engine Oil 5W-30 1L", "Air Filter"])], fields=["name", "total_value", "qty_available"])
    got = {v["name"]: (v["qty_available"], v["total_value"]) for v in vals}
    assert got == {"Engine Oil 5W-30 1L": (20, 120), "Air Filter": (16, 168)}, "stock value should be oil 20 / $120 and filters 16 / $168; it is %s" % got
    acc = env.call("account.account", "search", [("code", "=", "110100")])
    bal = env.call("account.move.line", "read_group", [("account_id", "in", acc), ("parent_state", "=", "posted")], ["balance:sum"], [])
    assert bal and round(bal[0]["balance"], 2) == 288, "the Stock Valuation account should hold $288, like the stock; it holds %s" % (bal and bal[0]["balance"])


def shelf_after_valuation(env):
    rows = env.call("stock.quant", "search_read", [("location_id.usage", "in", ["internal", "transit"])],
                    fields=["product_id", "location_id", "quantity", "lot_id", "package_id"])
    have = {}
    for r in rows:
        if r["quantity"]:
            key = (r["location_id"][1], r["product_id"][1], r["lot_id"] and r["lot_id"][1], bool(r["package_id"]))
            have[key] = have.get(key, 0) + r["quantity"]
    want = {("LFD/Stock", "Brake Pad Set", False, False): 15.0, ("LFD/Stock/Shelf A", "Brake Pad Set", False, False): 15.0,
            ("LFD/Stock/Shelf B", "Brake Pad Set", False, False): 9.0, ("LFD/Stock/Pallet Bay 1", "Brake Pad Set", False, True): 10.0,
            ("LFD/Stock", "Engine Oil 5W-30 1L", False, False): 12.0, ("LFD/Stock", "Rebuilt Engine", False, False): 1.0,
            ("LFD/Stock", "Air Filter", False, False): 16.0,
            ("LFD/Stock/Fluids Rack", "Coolant 5L", False, False): 9.0, ("LFD/Stock", "Brake Fluid DOT 4 1L", "BF-002", False): 6.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000001", False): 1.0, ("LFD/Stock", "Diagnostic Tablet", "DT-0000002", False): 1.0,
            ("LFD/Stock", "Diagnostic Tablet", "DT-0000003", False): 1.0, ("VAN/Stock", "Engine Oil 5W-30 1L", False, False): 8.0}
    for key, qty in want.items():
        assert have.get(key) == qty, "%s should hold %s %s%s, it holds %s" % (
            key[0], qty, key[1], " lot %s" % key[2] if key[2] else "", have.get(key))
    extra = {k: v for k, v in have.items() if k not in want}
    assert not extra, "unexpected stock: %s. A purchase or sale of air filters is not finished" % extra


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
         "Settings > Users & Companies > Users > New, login 'tina', Workshop = "
         "User, then save. From odoo shell, don't forget env.cr.commit()."),
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
    "ch23": [
        ("the pricelists feature is enabled", pricelists_feature_is_on,
         "Settings > Sales > Pricelists. Until it is ticked, price_unit comes straight "
         "from the product and there are no pricelist records at all."),
        ("two rules compete on one pricelist", two_rules_compete_on_one_pricelist,
         "One global percentage rule and one variant-specific fixed rule."),
        ("the more specific rule wins", specific_rule_beats_global,
         "applied_on values are prefixed 0_ to 3_ precisely so the most specific rule "
         "sorts first. A 79.00 product should price at the 60.00 variant rule."),
        ("a claimed promotion added a negative line", a_promotion_added_a_negative_line,
         "Install Coupons & Loyalty, then apply the demo code 10pc. The reward is a new "
         "order line with a negative price_unit."),
    ],
    "ch24": [
        ("an RFQ for the brake pads was confirmed", purchase_order_confirmed,
         "Purchase > New, add 10 of Brake Pad Set (Front) from a vendor, then Confirm."),
        ("the goods were received", goods_were_received,
         "Confirming creates an incoming transfer. Set quantities and validate it."),
        ("ordered, received and billed all agree", three_way_match_is_complete,
         "Create Bill on the order, give it an invoice date, and post it. Odoo tracks the "
         "three quantities separately so a mismatch is visible."),
        ("the receipt moved stock out of the vendor location", receipt_moved_stock_both_ways,
         "A stock move always has a source and a destination, so receiving leaves a "
         "negative quant at Vendors and a positive one in WH/Stock."),
    ],
    "ch25": [
        ("a multi-step reception created an internal transfer", a_multi_step_transfer_happened,
         "Switch Incoming Shipments to 2 steps, receive a small purchase, and validate "
         "both the Receipt and the Storage transfer it spawns."),
        ("a reordering rule exists for the brake pads", a_reordering_rule_exists_for_brake_pads,
         "Inventory > Configuration > Reordering Rules > New, with a min and a max."),
        ("the warehouse is back on the one-step route", warehouse_reverted_to_one_step,
         "Switch Incoming Shipments back to 'Receive goods directly (1 step)' once "
         "you have seen the multi-step transfer."),
    ],
    "ch26": [
        ("the Brake Pad Set has a BoM with components and an operation",
         brake_pad_bom_has_components_and_an_operation,
         "Manufacturing > Bills of Materials > New: at least two component lines and "
         "one operation against a work center."),
        ("a manufacturing order for it was completed", a_manufacturing_order_completed,
         "Manufacturing > Manufacturing Orders > New, Confirm, then Mark as Done."),
        ("components were consumed exactly by the BoM ratio", components_were_consumed_by_bom_ratio,
         "Consumption should scale with product_qty times each component's BoM "
         "quantity. If it does not, check the reservation matched what was produced."),
    ],
    "ch27": [
        ("a manual journal entry was posted", manual_journal_entry_posted,
         "Invoicing > Accounting > Transactions > Journal Entries > New, journal "
         "Miscellaneous Operations, two lines of 250.00 (one debit, one credit), "
         "then Post."),
        ("its debits equal its credits", manual_entry_is_balanced,
         "Double-entry is not a convention here, it is enforced: Odoo refuses to post "
         "an unbalanced move."),
        ("the sequence numbered it at posting time", manual_entry_got_its_number_on_posting,
         "A draft move's name is False. Posting is what asks the journal's sequence for "
         "a number, which is why numbering has no gaps."),
        ("an invoice is the same model as that entry", an_invoice_is_the_same_model,
         "account.move holds both, told apart by move_type. Compare your entry with any "
         "demo invoice: both balance, both are account.move."),
    ],
    "ch28": [
        ("a customer invoice for the brake pads was posted", brake_pad_invoice_posted,
         "From the confirmed order: Create Invoice, then Confirm. Creating leaves it in "
         "draft, and a draft invoice has no number and no accounting effect."),
        ("it balances and carries a tax line", invoice_carries_a_tax_line,
         "Three lines: product revenue, tax, and the receivable that equals their sum."),
        ("it is fully paid", invoice_is_fully_paid,
         "Register Payment. The hands-on pays part of it first, on purpose, so you can "
         "see the 'partial' state before it reaches 'paid'."),
        ("the receivable line is reconciled", receivable_line_is_reconciled,
         "payment_state is a summary. Reconciliation on the line is the mechanism, and "
         "account.partial.reconcile is where the link actually lives."),
    ],
    "ch29": [
        ("the sales tax was split across two distribution lines", sales_tax_was_split_across_two_accounts,
         "On a copy of the 15% sales tax, Definition tab: two 'of tax' lines in "
         "Distribution for Invoices, 60% and 40%, each with its own account."),
        ("one tax posted two tax lines, split by factor", one_tax_posted_two_tax_lines,
         "Invoice something with that tax and Confirm. Repartition lines are what "
         "turn one tax into several journal lines, so you should see two."),
        ("a tax-included tax exists", a_tax_included_tax_exists,
         "Advanced Options > Included in Price = Tax Included. price_include itself "
         "is computed in Odoo 19; the override is the field you set."),
        ("its tax lands in a tax account, not in income", tax_included_tax_books_to_a_tax_account,
         "A brand new tax's distribution lines have no account, and Odoo then books "
         "the tax wherever the base line went. Set the account on both of them."),
        ("a 100.00 tax-included line invoiced as 86.96 plus 13.04", a_tax_included_line_was_invoiced,
         "With the tax included, the price you type is the total: 100 / 1.15 = 86.96 "
         "of revenue and 13.04 of tax. If you see 115.00, the override is not applying."),
        ("an export order dropped the domestic tax", an_export_order_dropped_the_domestic_tax,
         "Quote a customer whose country is not the company's. Foreign Trade "
         "auto-applies on country and maps the 15% to 0% Exports."),
        ("the rounding method is back to Round per Tax", rounding_method_is_back_to_round_per_tax,
         "Settings > Accounting > Taxes > Rounding Method. The hands-on borrows Round "
         "per Line for one comparison; put it back so later chapters agree with ours."),
    ],
    "ch30": [
        ("the brake pads have a product category", brake_pads_have_a_category,
         "Open the product and set Product Category to Goods. Without one, the product "
         "has no costing method, no valuation mode and no stock account, so it values "
         "at 0.00 however much you paid."),
        ("the category is AVCO and Perpetual", goods_category_is_avco_and_real_time,
         "Inventory > Configuration > Product Categories > Goods: Costing Method = "
         "Average Cost (AVCO), Inventory Valuation = Perpetual (at invoicing). Two "
         "separate switches: what it is worth, and when the books hear about it."),
        ("AVCO derived the unit cost from real movements", avco_derived_the_unit_cost,
         "Switching to AVCO makes Odoo recompute the cost from the receipts already in "
         "the database: 630.00 over 19 units is 33.16. If it reads 0.00 the category "
         "is still on Standard Price."),
        ("the Customers location routes stock to an expense account",
         customers_location_routes_to_cogs,
         "Inventory > Configuration > Locations > Customers, set Stock Valuation "
         "Account to 500000 Cost of Goods Sold. Odoo 19 puts the counterpart on the "
         "location, not on the category as older versions did."),
        ("chapter 22's delivery posted a balanced stock entry",
         the_waiting_delivery_posted_cogs,
         "Validate WH/OUT/00044, the delivery waiting since chapter 22. It posts one "
         "STJ entry: Stock Valuation credited, Cost of Goods Sold debited, 132.63 "
         "each way."),
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
        ("the service type name is a translatable field", service_type_name_is_translatable,
         "Add translate=True to librefleet.service.type.name and upgrade. Odoo "
         "migrates the varchar column to jsonb and moves existing values under an "
         "'en_US' key by itself, no migration script needed."),
        ("French is installed", french_is_installed,
         "odoo i18n loadlang -c /etc/odoo/odoo.conf -d tutorial -l fr. Note the "
         "subcommand: Odoo 19 replaced the old --load-language server flag."),
        ("Tire Rotation reads in French", tire_rotation_reads_in_french,
         "Export the template (i18n export ... librefleet -l pot -o -), write "
         "i18n/fr.po with msgstr \"Rotation des pneus\", then import it with "
         "i18n import -l fr. Both languages then live in the same jsonb column."),
    ],
    "ch35": [
        ("base_automation is installed", base_automation_is_installed,
         "Add \"base_automation\" to librefleet's depends in __manifest__.py, "
         "then upgrade. It pulls in digest, resource and sms as its own "
         "dependencies, that is normal."),
        ("the maintenance-reminder cron exists", maintenance_reminder_cron_exists,
         "An <record model=\"ir.cron\"> with ir_actions_server_id pointing at "
         "the server action below, interval_number 1, interval_type 'days'."),
        ("the reminder action is bound to the Vehicles list",
         reminder_action_is_bound_to_the_vehicle_list,
         "On the ir.actions.server record: binding_model_id ref to "
         "model_librefleet_vehicle, binding_view_types \"list\", state \"code\"."),
        ("running it reminded an overdue vehicle", running_it_reminded_an_overdue_vehicle,
         "Settings > Technical > Scheduled Actions > 'LibreFleet: maintenance "
         "reminders' > Run Manually. Pass user_id explicitly in "
         "activity_schedule(), it is not defaulted."),
        ("finishing an order cleared its vehicle's reminder",
         finishing_an_order_cleared_its_vehicle_reminder,
         "Take a service order to 'done' through the approve wizard, then check "
         "the base.automation fired: on_create_or_write, filter_pre_domain "
         "stage != 'done', filter_domain stage = 'done'."),
    ],
    "ch36": [
        ("the service report action is registered", service_report_action_is_registered,
         "<record model=\"ir.actions.report\">: model librefleet.service.order, "
         "report_type qweb-pdf, report_name \"librefleet.report_service_order\"."),
        ("it is bound to the Print menu", service_report_is_bound_to_the_print_menu,
         "binding_model_id ref to model_librefleet_service_order, "
         "binding_type \"report\" (chapter 35's server action used \"action\")."),
        ("both templates exist", service_report_templates_exist,
         "Two <template> records: report_service_order (the web.html_container "
         "wrapper, one per selected order) and report_service_order_document "
         "(the web.external_layout content), same shape as core's "
         "account.report_invoice / account.report_invoice_document."),
        ("the margin never prints on the customer document",
         service_report_never_prints_the_margin,
         "Do not add a t-field for o.margin anywhere in "
         "report_service_order_document. It is the workshop's profit, not "
         "something a customer-facing PDF should carry."),
    ],
    "ch37": [
        ("the public services page renders", services_page_renders,
         "@http.route(\"/librefleet/services\", type=\"http\", auth=\"public\") "
         "rendering the librefleet.services_page template."),
        ("the vehicle lookup endpoint works", vehicle_lookup_endpoint_works,
         "@http.route(\"/librefleet/vehicles/lookup\", type=\"jsonrpc\", "
         "auth=\"public\"). type=\"json\" still works but logs a deprecation "
         "warning, Odoo 19 renamed it."),
        ("the service order has portal.mixin", service_order_has_portal_mixin,
         "Add \"portal.mixin\" to librefleet.service.order's _inherit list, "
         "then override _compute_access_url to point at "
         "/my/service-orders/<id> instead of the mixin's default '#'."),
        ("the portal ACL is read-only", portal_access_is_read_only,
         "One ir.model.access row for base.group_portal on "
         "librefleet.service.order, perm_read=1 and the other three 0."),
        ("a record rule scopes it to the customer", portal_record_rule_scopes_to_customer,
         "An ir.rule for base.group_portal with domain_force "
         "[('customer_id', '=', user.partner_id.id)]. Without it the ACL "
         "alone lets any portal user read any order."),
    ],
    "ch39": [
        ("the WorkshopClock component is in the backend bundle",
         workshop_clock_is_in_the_backend_bundle,
         "Add an \"assets\" key to __manifest__.py, a SIBLING of \"data\", "
         "listing librefleet/static/src/**/*.js under \"web.assets_backend\", "
         "then upgrade. Assets never go in the \"data\" list."),
        ("its template is registered under the matching name",
         workshop_clock_template_is_registered,
         "List librefleet/static/src/**/*.xml in the same assets bundle, and "
         "make <t t-name=\"...\"> match static template = \"...\" exactly. A "
         "mismatch only shows up as OwlError in the browser console."),
        ("it reads open orders through the ORM service",
         workshop_clock_reads_open_orders_over_rpc,
         "useService(\"orm\") then orm.searchCount(\"librefleet.service.order\", "
         "[[\"stage\", \"not in\", [\"done\", \"cancelled\"]]]). The ORM service "
         "goes through the session, so access rules still apply."),
    ],
    "ch40": [
        ("the margin widget is registered", margin_widget_is_registered,
         "A component class plus an exported descriptor, then "
         "registry.category(\"fields\").add(\"librefleet_margin\", marginField). "
         "The registry name is what widget=\"...\" in a view looks up."),
        ("it declares which field types it supports",
         margin_widget_declares_supported_types,
         "supportedTypes: [\"float\", \"monetary\"] on the descriptor. This is "
         "what stops the widget being used on a field type it cannot render."),
        ("the service order form actually uses it", margin_widget_is_used_on_the_form,
         "Add widget=\"librefleet_margin\" to <field name=\"margin\"/> in "
         "views/service_order_views.xml. Registering a widget does not apply "
         "it anywhere by itself."),
        ("the FormController patch is scoped to one model",
         form_controller_patch_is_scoped,
         "patch(FormController.prototype, { async onWillSaveRecord(record) "
         "{...} }) with a record.resModel check inside. A patch applies to "
         "every form view in the client, so the guard is mandatory."),
    ],
    "ch41": [
        ("the client action record exists", dashboard_client_action_exists,
         "<record model=\"ir.actions.client\"> with tag "
         "\"librefleet_dashboard\", plus a menuitem pointing at it. Register "
         "the file AFTER librefleet_menus.xml, the parent menu lives there."),
        ("a component is registered under the same tag",
         dashboard_component_is_registered,
         "registry.category(\"actions\").add(\"librefleet_dashboard\", "
         "LibreFleetDashboard). The tag string is the only link between the "
         "database record and the JavaScript."),
        ("it aggregates in the database, not in JavaScript",
         dashboard_aggregates_server_side,
         "orm.formattedReadGroup(model, domain, [\"technician_ids\"], "
         "[\"__count\", \"margin:sum\"]). Odoo 19 renamed read_group, so "
         "there is no orm.readGroup."),
        ("the drill-down reuses each group's own domain",
         dashboard_reuses_the_group_domain,
         "formattedReadGroup returns __domain per group. Pass it straight to "
         "doAction rather than rebuilding a domain that can drift from the "
         "number the user clicked."),
        ("open orders actually group by technician",
         dashboard_open_orders_group_correctly,
         "Assign technicians to some open (draft/confirmed/in_progress) "
         "orders, or the dashboard renders an empty table."),
    ],
    "ch42": [
        ("website_sale is installed", website_sale_is_installed,
         "Settings > Apps > eCommerce (or -i website_sale). Run this "
         "chapter's checks with --db functional."),
        ("a real order was placed through the online store",
         a_website_order_was_placed,
         "http://localhost:8069/shop: pick a product, add to cart, check "
         "out with Wire Transfer (enable it first, it needs no external "
         "account)."),
        ("point_of_sale is installed", point_of_sale_is_installed,
         "Settings > Apps > Point of Sale (or -i point_of_sale). Run this "
         "chapter's checks with --db functional."),
        ("a POS session was opened and closed", a_pos_session_was_closed,
         "Point of Sale > New Session, ring up at least one order, then "
         "close the register from the hamburger menu."),
        ("the session's journal entry is posted and balanced",
         session_move_is_posted_and_balanced,
         "Closing the register is what posts the session's consolidated "
         "account.move. If it is missing, the session is still stuck at "
         "the Closing Register screen."),
        ("the counted cash matches what the till should hold",
         cash_count_matches_reality,
         "The Closing Register screen's Cash Count field defaults to 0. "
         "Enter the actual (or expected) drawer total before clicking "
         "Close Register, or the session reports a fake shortfall."),
    ],
    "ch46": [
        ("librefleet_maintenance_reminder is installed",
         maintenance_reminder_module_is_installed,
         "mkdir addons/librefleet_maintenance_reminder, move the code and "
         "data files per the chapter, then -i librefleet_maintenance_reminder."),
        ("librefleet no longer depends on base_automation",
         librefleet_no_longer_depends_on_base_automation,
         "Remove 'base_automation' from librefleet's own __manifest__.py "
         "depends list; the new module declares it instead, since it's the "
         "one actually using it now."),
        ("exactly one maintenance-clearing automation exists",
         exactly_one_maintenance_automation,
         "If this fails with 2, librefleet's old data file created a record "
         "that a plain -u never deleted. Run this chapter's cleanup SQL "
         "against the leftover ir_model_data-tracked rows under module="
         "'librefleet'."),
    ],
    "ch49": [
        ("sale_fixed_discount is installed",
         sale_fixed_discount_is_installed,
         "Clone OCA/sale-workflow into oca/, add /mnt/oca/sale-workflow to "
         "addons_path, restart, then -i sale_fixed_discount -d functional."),
        ("its cross-repository dependency came with it",
         fixed_discount_dependency_came_along,
         "The install refuses until OCA/account-invoicing is on the addons "
         "path too. One feature, two repositories."),
        ("sale.order.line gained a discount_fixed field",
         sale_order_line_has_discount_fixed,
         "The field is the module's whole point. If it is missing, the module "
         "is registered but its code did not load."),
    ],
    "ch50": [
        ("all four of this chapter's modules are installed",
         ch50_modules_are_installed,
         "One clone and one addons_path entry per repository, then "
         "-i crm_lead_code,product_secondary_unit,auditlog,web_responsive."),
        ("the auto_install bridge arrived on its own",
         auto_install_bridge_arrived,
         "sale_order_secondary_unit declares auto_install: True and depends on "
         "sale plus product_secondary_unit. Installing the second one is all "
         "it was waiting for."),
        ("every pre-existing lead was given a code",
         every_old_lead_got_a_code,
         "crm_lead_code's post_init_hook walks the leads that were already "
         "there. Hooks run on install, never on upgrade."),
        ("product.secondary.unit is a real model now",
         product_secondary_unit_model_exists,
         "This is the chapter's only brand-new model, and it comes from an "
         "OCA module rather than from your own code."),
    ],
    "ch51": [
        ("sale_fixed_discount_limit is installed and depends on the OCA module",
         discount_limit_module_installed,
         "Scaffold addons/sale_fixed_discount_limit with depends: "
         "['sale_fixed_discount'], then -i sale_fixed_discount_limit."),
        ("a fixed discount above the unit price is refused",
         discount_above_unit_price_refused,
         "The @api.constrains('discount_fixed', 'price_unit') raises "
         "ValidationError when discount_fixed exceeds price_unit. Give the "
         "method a name of its own: reusing the OCA module's _check_discounts "
         "replaces theirs instead of adding yours."),
        ("the refusal left the line exactly as it was",
         refused_write_left_the_line_alone,
         "A constraint raising ValidationError aborts the whole write. If the "
         "line kept a value, the guard is running somewhere that writes "
         "first, such as an overridden write(), rather than in a constraint."),
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
    "inv01": [
        ("the Inventory app is installed", inventory_app_installed,
         "Apps > Inventory > Activate (the module is called stock)."),
        ("Storage Locations is switched on", storage_locations_are_on,
         "Inventory > Configuration > Settings, tick Storage Locations, Save. Without it a "
         "warehouse is one undivided room and the Locations menu does not exist."),
        ("the depot is called LibreFleet Depot with Short Name LFD", depot_warehouse_exists,
         "Configuration > Warehouses, open the default warehouse, set Warehouse to "
         "LibreFleet Depot and Short Name to LFD. Saving renames LFD/Stock and the sequences."),
        ("Shelf A and Shelf B are Internal locations under LFD/Stock", two_shelves_under_stock,
         "Configuration > Locations > New: name Shelf A, Parent Location LFD/Stock, type Internal."),
        ("the five products have the right kinds", products_of_each_kind,
         "Three storable goods, one goods product without Track Inventory (Shop Rags), one "
         "Service (Labour Hour). The type and the Track Inventory box are on the General "
         "Information tab."),
        ("a receipt with four lines is done", first_receipt_is_done,
         "Receipts > New, Receive From Brembo Parts, four lines, Validate. A validated "
         "receipt is the only way quantities appear in this chapter."),
        ("the quants hold 20, 12 and 1 in LFD/Stock, and nothing for Shop Rags", quants_say_what_is_on_the_shelf,
         "Reporting > Locations shows one row per quant. A product with Track Inventory off "
         "never gets a quant, which is why Shop Rags is missing there."),
    ],
    "inv02": [
        ("a delivery of 8 pads and 2 oil to Garage Nord is done", delivery_to_garage_nord_is_done,
         "Deliveries > New, Delivery Address Garage Nord, two lines, Mark as Todo, then Validate. "
         "Mark as Todo confirms and reserves; Validate is what moves the quants."),
        ("a short delivery left a backorder, and the backorder is done", backorder_was_created_then_delivered,
         "Deliver 15 pads with 12 free: Validate asks Create Backorder? Answer Create Backorder. "
         "The remainder is a new transfer, Waiting until stock arrives."),
        ("a second receipt brought 10 pads", ten_more_pads_were_received,
         "Receipts > New, Receive From Brembo Parts, Brake Pad Set 10, Validate. A receipt has "
         "nothing to reserve, so it goes straight to Done."),
        ("two pads came back through a return", two_pads_came_back,
         "On the done delivery, Return opens a wizard with every line at 0. Type 2 on the pads, "
         "delete the oil line, Return, then Validate the receipt it creates."),
        ("one bottle of oil was scrapped", one_bottle_was_scrapped,
         "Operations > Adjustments > Scrap > New: product, quantity 1, Validate. The bottle moves "
         "to the Inventory adjustment location; Odoo 19 has no separate Scrap location."),
        ("a delivery of the tablet was reserved by hand, then cancelled", tablet_delivery_was_cancelled,
         "Set Delivery Orders to reserve Manually, create the delivery, Mark as Todo (it waits), "
         "Check Availability (it is ready), Cancel and confirm."),
        ("Delivery Orders reserve At Confirmation again", deliveries_reserve_at_confirmation_again,
         "Configuration > Operations Types > Delivery Orders > Reservation Method. Later chapters "
         "assume the default."),
        ("the shelf holds 9 pads, 9 oil and 1 tablet, nothing reserved", shelf_holds_nine_nine_and_one,
         "Reporting > Stock. Every number here is the sum of the transfers above; if one is off, "
         "Reporting > Moves History lists every done move line in order."),
    ],
    "inv03": [
        ("Multi-Step Routes is switched on", multi_step_routes_is_on,
         "Configuration > Settings > Warehouse > Multi-Step Routes. It adds the Routes and Rules menus "
         "and the step choices on the warehouse form."),
        ("the depot receives in 2 steps and delivers in 3", depot_receives_in_two_steps_and_ships_in_three,
         "Configuration > Warehouses > LibreFleet Depot: Incoming Shipments, Outgoing Shipments. Saving "
         "rewrites the routes and wakes up Input, Output and Packing Zone."),
        ("6 bottles came in through Input and were stored", six_bottles_came_in_through_input,
         "A receipt now stops in LFD/Input; the push rule creates a Storage transfer when it is done. "
         "Validate both."),
        ("4 pads went out as Pick, Pack, then Delivery", four_pads_went_pick_pack_ship,
         "Start at the Pick (Overview > Pick > New). Each Validate pushes the next transfer; Next Transfer "
         "opens it."),
        ("Sales and Purchase are installed", sales_and_purchase_are_installed,
         "Apps > Sales > Activate, Apps > Purchase > Activate. Purchase brings the Buy route, Sales lets "
         "an order start a chain."),
        ("the tablet is Replenish on Order with a vendor", tablet_is_replenished_on_order,
         "Settings > Replenish on Order (MTO) unarchives the route; then on the product, Inventory tab tick "
         "the route and Purchase tab add Brembo Parts."),
        ("the sales order bought, received, stored, picked, packed and shipped one tablet", the_order_bought_the_tablet,
         "Confirm the order, Confirm Order on the purchase it made, Validate the receipt, then follow Next "
         "Transfer until the delivery is Done."),
        ("the shelf holds 5 pads, 15 oil and 1 tablet, nothing in the step locations", shelf_holds_five_fifteen_and_one,
         "Reporting > Locations without the Internal filter shows Input, Packing Zone and Output. Anything "
         "left there is a chain you did not finish."),
    ],
    "inv04": [
        ("Manufacturing is installed", manufacturing_is_installed,
         "Apps > Manufacturing > Activate. It brings the Manufacture route, the Manufacturing operation "
         "type and the Manufacture steps on the warehouse."),
        ("20 Friction Pads and 20 Backing Plates were received and stored", components_were_received_and_stored,
         "Create the two components (Track Inventory on), then one receipt from Brembo Parts with both "
         "lines; two steps, so Validate the Storage too."),
        ("the pads have a bill of materials and the kit has a Kit bill", the_two_bills_of_materials_exist,
         "Manufacturing > Products > Bills of Materials. Brake Pad Set: 2 Friction Pad + 2 Backing Plate. "
         "Brake Service Kit: BoM Type Kit, 1 Brake Pad Set + 2 Engine Oil 5W-30 1L."),
        ("3 pads were manufactured from stock in one step", three_pads_were_made_from_stock,
         "Manufacturing Orders > New, Brake Pad Set, quantity 3, Confirm, Produce All. One click consumes "
         "the components and puts the pads on the shelf."),
        ("the depot manufactures in 3 steps", depot_manufactures_in_three_steps,
         "Configuration > Warehouses > LibreFleet Depot > Manufacture. Saving wakes up Pre-Production, "
         "Post-Production, Pick Components and Store Finished Product."),
        ("a Brake Service Kit went out as its parts", a_kit_was_delivered_as_its_parts,
         "A kit is never stocked: the Pick explodes it into 1 pad and 2 bottles the moment you confirm. "
         "Follow Next Transfer to the delivery."),
        ("the sales order manufactured, stored, picked, packed and shipped 2 pads", the_order_made_its_own_pads,
         "With the MTO route on the pads, Confirm makes a manufacturing order and a waiting Pick. Validate "
         "Pick Components, Produce All, Store Finished Product, then the Pick, Pack and delivery."),
        ("the shelf holds 7 pads, 13 oil, 10 of each component and 1 tablet", shelf_holds_seven_thirteen_ten_ten_and_one,
         "Reporting > Stock. 5 + 3 - 1 + 2 - 2 pads; 15 - 2 oil; 20 - 6 - 4 of each component. Anything left "
         "in Pre-Production or Post-Production is a step you skipped."),
    ],
    "inv05": [
        ("the order for 20 bottles was shipped in full", twenty_bottles_were_sold_and_shipped,
         "Sales > New for Garage Nord, 20 Engine Oil 5W-30 1L at 12, Confirm. Only 13 are on the shelf, "
         "which is what puts the oil in the Replenishment report."),
        ("the oil has a vendor at 6 with 3 days and a Pack of 6 packaging", oil_has_a_vendor_and_a_pack,
         "Product form: Purchase tab, vendor Nordic Lubricants, price 6, Lead Time 3; Sales tab, Packagings, Pack of 6."),
        ("the oil's rule is automatic, Min 10, Max 30, by the pack", oil_rule_is_automatic_min_max_by_the_pack,
         "In Replenishment: Min 10, Max 30, Multiple Pack of 6, then Automate."),
        ("Automate bought 42 bottles and they were received", automate_bought_42_bottles,
         "Automate creates the purchase order; confirm it and receive it in two steps."),
        ("the pads have an automatic Manufacture rule, Min 10, Max 15", pads_rule_manufactures_automatically,
         "Brake Pad Set > More > Reordering Rules > New: Route Manufacture, Trigger Auto, Min 10, Max 15."),
        ("the scheduler manufactured 8 pads", the_scheduler_made_eight_pads,
         "Debug mode, Inventory > Operations > Procurement: run scheduler. Then finish the order in three steps."),
        ("the components were bought on one order and the suggestions went away", components_were_bought_on_one_order,
         "Brembo Parts as vendor on both components, then select both lines in Replenishment, Order."),
        ("the shelf holds 15 pads, 35 oil, 1 tablet and no components", shelf_holds_fifteen_thirty_five_and_one,
         "Reporting > Locations without the Internal filter shows Input, Packing Zone, Output, Pre- and "
         "Post-Production. Anything left there is a chain you did not finish."),
    ],
    "inv06": [
        ("the Service Van warehouse exists, 1 step in and out", van_warehouse_exists,
         "Inventory > Configuration > Warehouses > New: Warehouse Service Van, Short Name VAN."),
        ("the van is resupplied from the depot only", van_is_resupplied_from_the_depot_only,
         "On the van's form: untick Buy to Resupply and Manufacture to Resupply, tick Resupply From LibreFleet Depot."),
        ("the van has an automatic oil rule, Min 4, Max 10, from the depot", van_has_an_automatic_oil_rule,
         "Oil > Reordering Rules > New: Location VAN/Stock, Route Service Van: Supply Product from LibreFleet Depot."),
        ("10 bottles travelled from the depot to the van", ten_bottles_travelled_to_the_van,
         "Order on the van's rule, then Pick, Pack, Delivery Orders at the depot, then the van's Receipt."),
        ("the van sold and delivered 2 bottles", the_van_sold_two_bottles,
         "Sales > New, Garage Nord, Other Info > Warehouse Service Van, 2 bottles, Confirm, Validate."),
        ("12 Coolant 5L came in on consignment from Nordic Lubricants", coolant_is_on_consignment,
         "Settings > Consignment, then a receipt from Nordic Lubricants with Assign Owner Nordic Lubricants."),
        ("Garage Nord has stock instructions and got 3 coolant", garage_nord_has_instructions_and_three_coolant,
         "Settings > Partner-Specific Instructions, Garage Nord's Notes tab, then a Pick of 3 Coolant 5L."),
        ("the depot and the van hold what the chapter says, nothing in transit", two_shelves_two_warehouses,
         "Reporting > Locations with Internal and Transit Locations shows every quant the check reads."),
    ],
    "inv07": [
        ("Lots & Serial Numbers and Expiration Dates are on", lots_and_expiry_are_on,
         "Inventory > Configuration > Settings, Traceability: Lots & Serial Numbers and Expiration Dates, Save."),
        ("the tablet is tracked by serial number, prefix DT-", tablet_is_serial_tracked_with_a_prefix,
         "Diagnostic Tablet: Track Inventory By Unique Serial Number; Inventory tab, Custom Lot/Serial DT-."),
        ("every tablet on the shelf has its own serial", every_tablet_has_a_serial,
         "Physical Inventory for the old tablet (DT-0000001), then a receipt of 2 with Generate Serials."),
        ("Brake Fluid is tracked by lots, with expiry dates 365/60/30/45", brake_fluid_has_lots_and_dates,
         "New product Brake Fluid DOT 4 1L, By Lots; Inventory tab, Expiration Date and the four day counts."),
        ("LFD/Stock removes first expiry first", depot_stock_removes_first_expiry_first,
         "Configuration > Locations > LFD/Stock, Removal Strategy First Expiry First Out (FEFO)."),
        ("lot BF-001 was sold, blocked, returned and scrapped", lot_bf001_was_recalled,
         "Sell 6 to Garage Nord, expire BF-001, return the delivery, scrap the 12 bottles of BF-001."),
        ("the shelf holds the serials, BF-002 and nothing recalled", shelf_after_the_recall,
         "Reporting > Locations shows quants by lot; BF-001 must be gone and the three tablets serialised."),
    ],
    "inv08": [
        ("the Packages setting is on", packages_are_on,
         "Inventory > Configuration > Settings, Operations: Packages, Save, then reload the page."),
        ("Carton and Pallet are disposable, the Tote is reusable", carton_pallet_and_tote_exist,
         "Configuration > Package Types: Carton (CTN, CARTON, 400 x 300 x 300, 0.4 / 20 kg), Pallet (PAL); the Tote by Import records."),
        ("Receipts and Pick ask for a package type", receipts_and_pick_ask_for_a_type,
         "Configuration > Operations Types > LibreFleet Depot: Receipts, then Pick: Set Package Type."),
        ("a Pack of 6 travels in a Carton", pack_of_6_is_a_carton,
         "Configuration > Units & Packagings > Pack of 6, Package Type: Carton."),
        ("the oil and its Pack of 6 have barcodes", oil_and_its_pack_have_barcodes,
         "Oil form, Barcode 5901234123457; Pack of 6 > Packaging Barcodes, the oil with 15901234123454."),
        ("a pallet of two cartons sits in LFD/Stock", a_pallet_of_two_cartons_is_stored,
         "Receive 12 oil and 10 pads from Nordic Lubricants: each line in a Carton, both cartons on a Pallet, then Storage."),
        ("the tote was emptied and a carton of 12 oil shipped", the_tote_was_emptied_and_the_carton_shipped,
         "Sell 2 Pack of 6 to Garage Nord: Pick into TOTE0000001, Put in Pack on the Pack step, then the delivery."),
        ("the shelf holds the cartons and the loose stock", shelf_after_packing,
         "Products > Packages shows what sits in which package; Reporting > Locations shows the loose rest."),
    ],    "inv09": [
        ("the oil is in the product category Goods / Fluids", the_oil_is_in_category_fluids,
         "Configuration > Product Categories > New: Fluids, Parent Category Goods; then the oil's Category."),
        ("Parts Shelf and Pallet Bay storage categories with their capacities", two_storage_categories_exist,
         "Configuration > Storage Categories: Parts Shelf (same products, 20 Brake Pad Set), Pallet Bay (empty only, 1 Pallet)."),
        ("the shelves and bays under LFD/Stock carry their categories", the_shelves_have_their_categories,
         "Configuration > Locations: Shelf A and B get Parts Shelf; new Pallet Bay 1 and 2 get Pallet Bay; new Fluids Rack gets none."),
        ("three putaway rules on LFD/Stock", three_putaway_rules_on_lfd_stock,
         "Configuration > Putaway Rules: Brake Pad Set closest Parts Shelf; Goods / Fluids to Fluids Rack; Pallet closest Pallet Bay."),
        ("putaway chose Shelf A, then Shelf B, then the Fluids Rack", putaway_chose_the_shelves,
         "Receive 15 pads, then 10 pads from Brembo, then 6 oil from Nordic, validating each Storage."),
        ("the pallet was moved whole to Pallet Bay 1", the_pallet_sits_in_bay_1,
         "Internal Transfers > New, LFD/Stock to LFD/Stock, Move a Pack: PAL0000001, Validate."),
        ("LIFO took the newest oil", lifo_took_the_newest_oil,
         "Sell 6 oil to Garage Nord; Fluids: Force Removal Strategy LIFO; on the Pick, Unreserve, Check Availability."),
        ("the shelf holds what putaway and the sale left", shelf_after_putaway,
         "Reporting > Locations shows every quant by location; Shelf A 15 pads, Shelf B 10, the pallet in Bay 1."),
    ],    "inv10": [
        ("the oil count was applied, then reverted", the_oil_count_was_reverted,
         "Physical Inventory: oil in LFD/Stock, Counted 12, Apply; then History, Actions > Revert Inventory Adjustment."),
        ("Shelf A and B were counted on request and applied with a reason", the_shelves_were_counted_with_a_reason,
         "Select both shelves, Request a Count, enter 15 and 9, select both again, header Apply with an Inventory Reason."),
        ("one bottle of BF-002 was scrapped as Damaged", bf002_was_scrapped_as_damaged,
         "Operations > Scrap: Brake Fluid DOT 4 1L, lot BF-002, quantity 1, Scrap Reason Damaged, Validate."),
        ("the outdated BF-002 count kept its difference", the_conflict_kept_the_difference,
         "Count BF-002 at 12 before the scrap, Apply after it, and choose Keep Difference in the conflict."),
        ("the coolant was relocated to the Fluids Rack", the_coolant_was_relocated,
         "Physical Inventory, select the coolant, Actions > Relocate, To Location LFD/Stock/Fluids Rack."),
        ("Shelf A is counted every 30 days", shelf_a_is_counted_every_30_days,
         "Configuration > Locations > LFD/Stock/Shelf A: Inventory Frequency 30."),
        ("Picks are batched automatically by source location", picks_are_batched_automatically,
         "Settings: Batch, Wave & Cluster Transfers; then the Pick operation type: Automatic Batches, Source Location."),
        ("one batch picked the orders of Garage Nord and Garage Sud", one_batch_picked_two_orders,
         "Sell 2 brake fluid to Garage Nord and 3 to Garage Sud, Validate the batch, then the Packs and Deliveries."),
        ("the shelf holds what the counts, scrap and sales left", shelf_after_counting,
         "Physical Inventory lists every quant; BF-002 6, Shelf B 9, the coolant on the Fluids Rack."),
    ],
    "inv11": [
        ("delivery methods, dropshipping and subcontracting are installed", shipping_dropship_and_subcontracting_are_on,
         "Inventory > Configuration > Settings: Delivery Methods (Shipping), Dropshipping (Logistics), Subcontracting (Manufacturing)."),
        ("the oil carries its weight, HS code and origin", the_oil_has_shipping_data,
         "Engine Oil 5W-30 1L, Inventory tab: Weight 1, HS Code 271019, Origin of Goods Germany."),
        ("Depot Van costs $15 and is free over $100", depot_van_is_free_over_100,
         "Delivery Methods > New: Fixed Price, Delivery Product Depot Van, then Fixed Price 15, Free if order amount is above 100."),
        ("Courier by Weight prices by weight in two rules", the_courier_prices_by_weight,
         "Based on Rules, Pricing tab: weight <= 5 then 8 + 0; weight <= 30 then 5 + 1 x Weight; Tracking Link with <shipmenttrackingnumber>."),
        ("the courier order charged $13 for 8 kg", the_courier_order_charged_13,
         "Sell 8 oil to Garage Sud, Add shipping, Courier by Weight, Add, Confirm."),
        ("the courier delivery left with a tracking number", the_courier_delivery_has_a_tracking_number,
         "Validate the Pick and Pack; on the Delivery, Additional Info, Tracking Reference LF123456, then Validate."),
        ("four tyres went from Pneu Direct straight to Garage Nord", the_tyres_were_dropshipped,
         "Tyre 205/55 R16 with vendor Pneu Direct and route Dropship; sell 4 to Garage Nord, confirm the PO, validate DS."),
        ("Atelier Moteur rebuilt an engine with your oil", the_engine_was_subcontracted,
         "Subcontracting BoM: Rebuilt Engine, Atelier Moteur, 5 oil; buy 1, validate the Resupply, then the Receipt."),
        ("the shelf holds what shipping and subcontracting left", shelf_after_shipping,
         "Physical Inventory: 12 loose oil in LFD/Stock, the carton in Pallet Bay 1 empty, one Rebuilt Engine."),
    ],    "inv12": [
        ("the oil is valued at a standard $6", the_oil_costs_6,
         "Engine Oil 5W-30 1L, General Information: Cost 6. Its category stays on Standard Price."),
        ("Goods / Filters ends on AVCO and Perpetual", filters_are_avco_and_perpetual,
         "Configuration > Product Categories > Goods / Filters: Costing Method AVCO, Inventory Valuation Perpetual."),
        ("the receipts are worth $80, $100 and $117", the_receipts_carry_their_values,
         "Buy 10 at $8 and 10 at $10 under FIFO, then 10 at $9 under AVCO, bill it at $9.90, add $18 freight."),
        ("FIFO valued the first sale at $100", fifo_valued_the_first_sale,
         "Sell 12 air filters to Garage Nord while Goods / Filters is still on FIFO."),
        ("the vendor billed $9.90", the_bill_said_9_90,
         "Purchase Orders list, tick the third order, Create Bills, Bill Date today, Price 9.90, Confirm."),
        ("$18 of freight landed on the last receipt", freight_landed_on_the_receipt,
         "Settings: Landed Costs. Product Freight (service, Is a Landed Cost); Landed Costs > New on that receipt, 18, By Quantity."),
        ("the books were closed at $309", the_books_were_closed_at_309,
         "Before switching to Perpetual: /odoo/stock-valuation-closing, Generate Entry, Post."),
        ("the invoice posted $21 of cost of goods sold", the_invoice_posted_cogs,
         "With Filters on Perpetual, sell 2 air filters to Garage Sud, deliver them, Create Invoice, Confirm."),
        ("the stock is worth what the books say", stock_value_matches_the_books,
         "Oil 20 at $6, filters 16 at $10.50: $288, and the Stock Valuation account holds $288 too."),
        ("the shelf holds what the purchases and sales left", shelf_after_valuation,
         "Physical Inventory: 16 air filters in LFD/Stock, the rest as after chapter 11."),
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
# so the "location-independent" contract in CONTRIBUTING.md holds: the tool
# works against any --url/--db from any directory.

SNAPSHOT_FILE = ".odoolings-snapshot.json"
SNAPSHOT_LIMIT = 800

# model -> fields worth showing when a record is created or changes.
WATCHED = {
    "crm.lead":          ["name", "stage_id", "probability"],
    "sale.order":        ["name", "state", "amount_untaxed", "amount_total", "invoice_status"],
    "sale.order.line":   ["product_id", "product_uom_qty", "price_unit", "discount"],
    "purchase.order":    ["name", "state", "amount_total", "receipt_status", "invoice_status"],
    "purchase.order.line": ["product_id", "product_qty", "price_unit", "qty_received", "qty_invoiced"],
    "stock.picking":     ["name", "state", "picking_type_id"],
    "stock.move":        ["reference", "product_id", "product_uom_qty", "state"],
    "stock.quant":       ["product_id", "location_id", "quantity"],
    "mrp.production":    ["name", "state", "product_qty"],
    "account.account":   ["code", "name", "account_type"],
    # price_include is computed, not stored, in Odoo 19: watching it is how the
    # diff shows a tax-included tax without anyone having to read the override.
    "account.tax":       ["name", "amount", "type_tax_use", "price_include"],
    "account.move":      ["name", "move_type", "state", "amount_total", "payment_state"],
    "account.move.line": ["name", "account_id", "debit", "credit", "reconciled"],
    "account.payment":   ["display_name", "state", "amount", "payment_type"],
    "product.template":  ["name", "list_price", "type"],
    # product.product matters as much as the template: generating variants is the
    # one thing a template does that you cannot see by watching templates alone.
    "product.product":   ["display_name", "default_code", "lst_price"],
    "product.pricelist": ["name"],
    "res.partner":       ["name"],
    "stock.warehouse.orderpoint": ["product_id", "product_min_qty", "product_max_qty", "trigger"],
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
    "account.payment": "display_name",
    "stock.move": "product_id",
    "stock.quant": "product_id",
    "sale.order.line": "product_id",
    "purchase.order.line": "product_id",
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


# ------------------------------------------------------- start (jump in) --
# `start chNN` builds the database chapter NN begins with, for a reader who skipped
# the chapters before it. It replays every earlier chapter of that database in order:
# install what the chapter installed, redo its hand-made work (its seed), then run
# its checks, exactly as a reader going chapter by chapter would have.

ORDER = (["ch%02d" % n for n in range(1, 16)] + ["boss2"]
         + ["ch%02d" % n for n in range(16, 56)]
         + ["inv%02d" % n for n in range(1, 16)] + ["inv-boss"])
TUTORIAL = (["ch05", "ch06"] + ["ch%02d" % n for n in range(8, 16)] + ["boss2"]
            + ["ch%02d" % n for n in range(16, 21)] + ["ch%02d" % n for n in range(31, 42)]
            + ["ch44", "ch46", "ch52", "ch53", "ch54"])
FUNCTIONAL = ["ch%02d" % n for n in range(21, 31)] + ["ch42", "ch49", "ch50", "ch51", "ch53"]
WAREHOUSE = ["inv%02d" % n for n in range(1, 16)] + ["inv-boss"]  # the Inventory deep dive
SELF_BUILT = {"ch04": "tour", "ch05": "tutorial", "ch21": "functional", "inv01": "warehouse"}
# boss2 builds a module of its own that no later chapter uses
NOT_REPLAYED = {"boss2"}
# where start fetches checkpoints; override to test checkpoints that are not on main yet
FETCH_URL = os.environ.get("ODOOLINGS_FETCH_URL", "https://github.com/ronitjadhav/odoolings/archive/main.tar.gz")
CHECKPOINT_PREFIX = "odoolings-main/code/checkpoints/"
PRE_COMMIT_FILES = (".pre-commit-config.yaml", ".ruff.toml", ".pylintrc")
NEEDS_PRE_COMMIT = {"ch45", "ch46", "ch51", "ch52"}
NEEDS_GH = {"ch45", "ch47", "ch48", "ch51", "ch52"}
GH_NOTE = ("This chapter uses the GitHub CLI: install `gh` (https://cli.github.com) and sign "
           "in once with `gh auth login`.")
PRE_COMMIT_NOTE = "This chapter runs pre-commit: install it once with `pip install pre-commit`."

# The module versions each code/checkpoints/chNN ships.
CHECKPOINTS = {
    "ch08": {"librefleet": "19.0.1.0.0"}, "ch09": {"librefleet": "19.0.1.1.0"},
    "ch10": {"librefleet": "19.0.1.2.0"}, "ch11": {"librefleet": "19.0.1.3.0"},
    "ch12": {"librefleet": "19.0.1.4.0"}, "ch13": {"librefleet": "19.0.1.5.0"},
    "ch14": {"librefleet": "19.0.1.7.0"}, "ch15": {"librefleet": "19.0.1.8.0"},
    "ch16": {"librefleet": "19.0.1.9.0"}, "ch17": {"librefleet": "19.0.1.10.0"},
    "ch18": {"librefleet": "19.0.1.11.0"}, "ch19": {"librefleet": "19.0.1.13.0"},
    "ch20": {"librefleet": "19.0.1.15.0"}, "ch31": {"librefleet": "19.0.1.16.0"},
    "ch32": {"librefleet": "19.0.1.17.0"}, "ch33": {"librefleet": "19.0.1.18.0"},
    "ch34": {"librefleet": "19.0.1.20.0"}, "ch35": {"librefleet": "19.0.1.21.0"},
    "ch36": {"librefleet": "19.0.1.22.0"}, "ch37": {"librefleet": "19.0.1.23.0"},
    "ch38": {"librefleet": "19.0.1.24.0"}, "ch39": {"librefleet": "19.0.1.25.0"},
    "ch40": {"librefleet": "19.0.1.26.0"}, "ch41": {"librefleet": "19.0.1.27.0"},
    "ch44": {"librefleet": "19.0.1.28.0"},
    "ch46": {"librefleet": "19.0.1.29.0", "librefleet_maintenance_reminder": "19.0.1.0.0"},
    "ch51": {"sale_fixed_discount_limit": "19.0.1.0.0"},
    "ch53": {"librefleet": "19.0.1.30.0", "librefleet_maintenance_reminder": "19.0.1.0.0"},
}
TUTORIAL_CODE = ("librefleet", "librefleet_maintenance_reminder")

# What each functional chapter installs, in the order the chapters install it.
INSTALLS = {
    "ch21": ["sale_management", "purchase", "stock", "mrp", "crm"],
    "ch42": ["website_sale", "point_of_sale"],
    "ch49": ["sale_fixed_discount"],
    "ch50": ["crm_lead_code", "product_secondary_unit", "auditlog", "web_responsive"],
    "ch51": ["sale_fixed_discount_limit"],
    "inv03": ["sale_management", "purchase"],  # the Buy route, and an order that starts a chain
    "inv04": ["mrp"],
    "inv07": ["product_expiry"],  # Expiration Dates
    "inv10": ["stock_picking_batch"],  # Batch, Wave & Cluster Transfers
    "inv11": ["stock_delivery", "stock_dropshipping", "mrp_subcontracting"],  # Delivery Methods, Dropshipping, Subcontracting
    "inv12": ["stock_landed_costs"],  # Landed Costs
}
OCA_REPOS = {  # module -> the OCA repositories it needs, as chapters 49 and 50 clone them
    "sale_fixed_discount": ["sale-workflow", "account-invoicing"],
    "crm_lead_code": ["crm"], "product_secondary_unit": ["product-attribute"],
    "auditlog": ["server-tools"], "web_responsive": ["web"],
}


def _code_for(target):
    """{module: (version, checkpoint)} of the newest checkpoint before `target`."""
    code = {}
    for ch in ORDER[:ORDER.index(target)]:
        for module, version in CHECKPOINTS.get(ch, {}).items():
            code[module] = (version, ch)
    return code


def _call(env, model, method, *args, **kw):
    """env.call for methods that may return None, which XML-RPC cannot carry."""
    try:
        return env.call(model, method, *args, **kw)
    except xmlrpc.client.Fault as e:
        if "cannot marshal None" not in e.faultString:
            raise


def _id(env, model, domain, **kw):
    ids = env.call(model, "search", domain, limit=1, **kw)
    assert ids, "no %s matches %r" % (model, domain)
    return ids[0]


def _xmlid(env, xmlid):
    return env.call("ir.model.data", "check_object_reference", *xmlid.split("."))[1]


def _vehicle(env, plate):
    return _id(env, "librefleet.vehicle", [("license_plate", "=", plate)])


def _order(env, reference):
    return _id(env, "librefleet.service.order", [("reference", "=", reference)])


def _service_type(env, name):
    return _id(env, "librefleet.service.type", [("name", "=", name)])


def _run_cron(env, cron):
    """Run a scheduled action now, waiting if the scheduler is already running it."""
    for attempt in range(60):
        try:
            return _call(env, "ir.cron", "method_direct_trigger", [cron])
        except xmlrpc.client.Fault as e:
            if "already executing" not in e.faultString or attempt == 59:
                raise
            time.sleep(2)


def seed_ch06(env):
    env.call("res.partner", "create", {"name": "Ada Lovelace"})


def seed_ch09(env):
    vehicles = [
        {"license_plate": "ZH 468 202", "model_name": "Fiat Ducato", "year": 2021,
         "mileage_km": 84250.0},
        {"license_plate": "BE 30 447", "model_name": "VW Crafter", "year": 2019,
         "mileage_km": 143800.0},
    ]
    try:
        env.call("librefleet.vehicle", "create", vehicles)
    except xmlrpc.client.Fault as e:
        if "not allowed" not in e.faultString:
            raise
        # chapter 9's code has no access rules yet (chapter 10 adds them), and the
        # chapter creates these in a superuser shell: lend admin a rule for the seed
        acl = env.call("ir.model.access", "create", {
            "name": "odoolings start", "model_id": _id(env, "ir.model", [("model", "=", "librefleet.vehicle")]),
            "group_id": _xmlid(env, "base.group_system"),
            "perm_read": True, "perm_write": True, "perm_create": True, "perm_unlink": True,
        })
        # create() clears the access cache before its own check refills it, stale; write() clears it again
        env.call("ir.model.access", "write", [acl], {"active": True})
        env.call("librefleet.vehicle", "create", vehicles)
        env.call("ir.model.access", "unlink", [acl])


def seed_ch10(env):
    env.call("res.users", "create", {
        "name": "Tina Technician", "login": "tina", "password": "technician",
        "group_ids": [(4, _xmlid(env, "librefleet.group_librefleet_user"))],
    })
    env.call("librefleet.vehicle", "write", [_vehicle(env, "ZH 468 202")], {"mileage_km": 84900.0})


def seed_ch11(env):
    env.call("librefleet.service.type", "create", [
        {"name": "Oil change", "flat_fee": 89.0, "default_duration_h": 1.0},
        {"name": "Brake inspection", "flat_fee": 120.0, "default_duration_h": 1.5},
        {"name": "Full service", "flat_fee": 349.0, "default_duration_h": 4.0},
    ])


def seed_ch12(env):
    anna, beat = env.call("res.partner", "create", [{"name": "Anna Keller"}, {"name": "Beat Muster"}])
    env.call("librefleet.vehicle", "write", [_vehicle(env, "ZH 468 202")], {"owner_id": anna})
    env.call("librefleet.vehicle", "write", [_vehicle(env, "BE 30 447")], {"owner_id": beat})
    oil_filter, oil, _pads = env.call("librefleet.part", "create", [
        {"name": "Oil filter", "code": "OF-102", "standard_cost": 12.0, "list_price": 24.5},
        {"name": "Engine oil 5W30 (1l)", "code": "OIL-5W30", "standard_cost": 9.5, "list_price": 18.9},
        {"name": "Brake pads, front", "code": "BP-201", "standard_cost": 35.0, "list_price": 79.0},
    ])
    env.call("librefleet.service.order", "create", {
        "vehicle_id": _vehicle(env, "ZH 468 202"),
        "service_type_id": _service_type(env, "Oil change"),
        "technician_ids": [(4, _id(env, "res.users", [("login", "=", "tina")]))],
        "scheduled_start": "2026-07-16 08:00:00", "scheduled_end": "2026-07-16 09:00:00",
        "line_ids": [(0, 0, {"part_id": oil_filter, "qty": 1, "price_unit": 24.5}),
                     (0, 0, {"part_id": oil, "qty": 4, "price_unit": 18.9})],
    })
    env.call("librefleet.service.order", "create", {
        "vehicle_id": _vehicle(env, "BE 30 447"),
        "service_type_id": _service_type(env, "Brake inspection"),
        "scheduled_start": "2026-07-17 09:00:00", "scheduled_end": "2026-07-17 10:30:00",
    })


def seed_ch15(env):
    ids = env.call("librefleet.vehicle", "create", [
        {"license_plate": "SHELL-001", "model_name": "Toyota Hilux", "year": 2021},
        {"license_plate": "SHELL-002", "model_name": "VW Caddy", "year": 2019},
        {"license_plate": "SHELL-003", "model_name": "Ford Transit", "year": 2015},
    ])
    env.call("librefleet.vehicle", "write", ids, {"notes": "Checked in bulk from the shell"})
    env.call("librefleet.vehicle", "write", [ids[1]], {"active": False})
    env.call("librefleet.vehicle", "unlink", [ids[2]])


def seed_ch32(env):
    marta = env.call("res.partner", "create", {"name": "Marta Ferreira"})
    env.call("librefleet.vehicle", "create", [{"license_plate": "CH22-AAA", "owner_id": marta},
                                              {"license_plate": "CH22-BBB", "owner_id": marta}])


def seed_ch33(env):
    model = "librefleet.service.order"
    env.call("res.users", "write", [env.uid], {"email": "admin@example.com"})
    order = _order(env, "SO/2026/0002")
    env.call(model, "write", [order], {"stage": "confirmed"})
    env.call(model, "message_post", [order], body="Customer called: OK to keep the vehicle overnight.")
    customer = env.call(model, "read", [order], ["customer_id"])[0]["customer_id"][0]
    _call(env, model, "message_subscribe", [order], partner_ids=[customer])
    env.call("mail.activity", "create", {
        "res_model_id": _id(env, "ir.model", [("model", "=", model)]), "res_id": order,
        "activity_type_id": _xmlid(env, "mail.mail_activity_data_call"),
        "summary": "Call about pickup time", "user_id": env.uid,
    })


def seed_ch34(env):
    french = env.call("res.lang", "search", [("code", "=", "fr_FR")], context={"active_test": False})
    wizard = env.call("base.language.install", "create", {"lang_ids": [(6, 0, french)], "overwrite": True})
    _call(env, "base.language.install", "lang_install", [wizard])


def seed_ch35(env):
    model = "librefleet.service.order"
    _run_cron(env, _id(env, "ir.cron", [("code", "like", "action_send_maintenance_reminders")]))
    order = _order(env, "SO/2026/0001")
    env.call(model, "write", [order], {"stage": "confirmed"})
    env.call(model, "write", [order], {"stage": "in_progress"})
    wizard = env.call("librefleet.service.order.approve.wizard", "create", {"order_id": order})
    _call(env, "librefleet.service.order.approve.wizard", "action_confirm", [wizard])


def seed_ch39(env):
    env.call("librefleet.service.order", "create", {
        "vehicle_id": _vehicle(env, "SHELL-001"),
        "service_type_id": _service_type(env, "Brake inspection"),
        "scheduled_start": "2026-12-01 09:00:00", "scheduled_end": "2026-12-01 10:00:00",
    })


def seed_ch40(env):
    order = _id(env, "librefleet.service.order", [("vehicle_id.license_plate", "=", "SHELL-001"),
                                                  ("scheduled_start", "=", "2026-12-01 09:00:00")])
    env.call("librefleet.service.order.line", "create", {
        "order_id": order, "part_id": _id(env, "librefleet.part", [("code", "=", "BP-201")]),
        "qty": 15, "price_unit": 1.0,
    })


def seed_ch41(env):
    model = "librefleet.service.order"
    tina = _id(env, "res.users", [("login", "=", "tina")])
    env.call(model, "write", [_order(env, "SO/2026/0002")], {"technician_ids": [(6, 0, [tina])]})
    env.call(model, "create", {
        "vehicle_id": _vehicle(env, "ZH 468 202"), "service_type_id": _service_type(env, "Full service"),
        "scheduled_start": "2026-09-10 08:00:00", "scheduled_end": "2026-09-10 12:00:00",
        "stage": "confirmed", "technician_ids": [(6, 0, [tina, env.uid])],
    })
    env.call(model, "create", {
        "vehicle_id": _vehicle(env, "SHELL-001"), "service_type_id": _service_type(env, "Tire Rotation"),
        "scheduled_start": "2026-09-11 09:00:00", "scheduled_end": "2026-09-11 10:00:00",
        "stage": "in_progress", "technician_ids": [(6, 0, [env.uid])],
    })


# Functional track, Parts 4 and 5: each seed redoes what the chapter clicks, in order.

def _install(env, names):
    ids = env.call("ir.module.module", "search", [("name", "in", names)])
    for attempt in range(60):
        try:
            return _call(env, "ir.module.module", "button_immediate_install", ids)
        except xmlrpc.client.Fault as e:
            # a running scheduled action blocks module operations for a few seconds
            if "processing a scheduled action" not in e.faultString or attempt == 59:
                raise
            time.sleep(2)


def _settings(env, **values):
    wizard = env.call("res.config.settings", "create", values)
    _call(env, "res.config.settings", "execute", [wizard])


def _partner(env, name):
    return _id(env, "res.partner", [("name", "=", name), ("is_company", "=", True)])


def _account(env, code):
    return _id(env, "account.account", [("code", "=", code)])


def _brake_pads(env):
    """(template, Front variant, Rear variant): Front was created first."""
    tmpl = _id(env, "product.template", [("name", "=", "Brake Pad Set")])
    front, rear = env.call("product.product", "search", [("product_tmpl_id", "=", tmpl)], order="id")
    return tmpl, front, rear


def _first_brake_order(env):
    """Chapter 22's order: the oldest confirmed order with Brake Pads on it."""
    _, front, _ = _brake_pads(env)
    return _id(env, "sale.order", [("state", "=", "sale"), ("order_line.product_id", "=", front)], order="id")


def _validate(env, pickings):
    _call(env, "stock.picking", "button_validate", pickings, context={"skip_sms": True})


def _purchase(env, vendor, product, qty, price):
    po = env.call("purchase.order", "create", {
        "partner_id": _partner(env, vendor),
        "order_line": [(0, 0, {"product_id": product, "product_qty": qty, "price_unit": price})],
    })
    _call(env, "purchase.order", "button_confirm", [po])
    _validate(env, env.call("purchase.order", "read", [po], ["picking_ids"])[0]["picking_ids"])
    return po


def seed_ch21(env):
    axle = env.call("product.attribute", "create", {
        "name": "Axle", "create_variant": "always",
        "value_ids": [(0, 0, {"name": "Front"}), (0, 0, {"name": "Rear"})],
    })
    values = env.call("product.attribute.value", "search", [("attribute_id", "=", axle)], order="id")
    env.call("product.template", "create", {
        "name": "Brake Pad Set", "type": "consu", "is_storable": True, "list_price": 79.0,
        "categ_id": False,
        "attribute_line_ids": [(0, 0, {"attribute_id": axle, "value_ids": [(6, 0, values)]})],
    })
    # the scheduler fires about a minute after the install, making P00012 from a demo
    # reordering rule: run it now so the readers' purchase orders keep their numbers
    _run_cron(env, _xmlid(env, "stock.ir_cron_scheduler_action"))


def seed_ch22(env):
    _settings(env, group_use_lead=True)
    acme = _partner(env, "Acme Corporation")
    lead = env.call("crm.lead", "create", {"name": "Fleet brake refresh",
                                           "partner_name": "Acme Corporation", "type": "lead"})
    context = {"active_model": "crm.lead", "active_id": lead, "active_ids": [lead]}
    wizard = env.call("crm.lead2opportunity.partner", "create", {
        "lead_id": lead, "name": "convert", "action": "exist", "partner_id": acme}, context=context)
    _call(env, "crm.lead2opportunity.partner", "action_apply", [wizard], context=context)
    _, front, _ = _brake_pads(env)
    order = env.call("sale.order", "create", {
        "partner_id": acme, "opportunity_id": lead,
        "order_line": [(0, 0, {"product_id": front, "product_uom_qty": 4})],
    })
    _call(env, "sale.order", "action_confirm", [order])


def seed_ch23(env):
    _settings(env, group_product_pricelist=True)
    company = env.call("res.users", "read", [env.uid], ["company_id"])[0]["company_id"][0]
    pricelist = _id(env, "product.pricelist", [("company_id", "=", company)])
    tmpl, front, _ = _brake_pads(env)
    env.call("product.pricelist.item", "create", [
        {"pricelist_id": pricelist, "applied_on": "3_global",
         "compute_price": "percentage", "percent_price": 10.0},
        {"pricelist_id": pricelist, "applied_on": "0_product_variant", "product_tmpl_id": tmpl,
         "product_id": front, "compute_price": "fixed", "fixed_price": 60.0},
    ])
    quotation = {"partner_id": _partner(env, "Azure Interior"), "pricelist_id": pricelist,
                 "order_line": [(0, 0, {"product_id": front, "product_uom_qty": 2})]}
    order = env.call("sale.order", "create", quotation)
    _install(env, ["sale_loyalty"])
    coupon = env.call("sale.loyalty.coupon.wizard", "create", {"order_id": order, "coupon_code": "10pc"})
    action = env.call("sale.loyalty.coupon.wizard", "action_apply", [coupon])
    reward = env.call("sale.loyalty.reward.wizard", "create", {
        "order_id": order, "selected_reward_id": action["context"]["default_reward_ids"][0]},
        context={"active_id": order})
    _call(env, "sale.loyalty.reward.wizard", "action_apply", [reward])
    env.call("sale.order", "create", quotation)


def seed_ch24(env):
    _, front, _ = _brake_pads(env)
    po = _purchase(env, "Gemini Furniture", front, 10, 42.0)
    _call(env, "purchase.order", "action_create_invoice", [po])
    bills = env.call("purchase.order", "read", [po], ["invoice_ids"])[0]["invoice_ids"]
    env.call("account.move", "write", bills, {"invoice_date": time.strftime("%Y-%m-%d")})
    _call(env, "account.move", "action_post", bills)


def seed_ch25(env):
    _settings(env, group_stock_multi_locations=True, group_stock_adv_location=True)
    warehouse = _id(env, "stock.warehouse", [])
    env.call("stock.warehouse", "write", [warehouse], {"reception_steps": "two_steps"})
    _, front, _ = _brake_pads(env)
    _purchase(env, "Gemini Furniture", front, 5, 42.0)
    storage = env.call("stock.picking", "search", [("picking_type_id.code", "=", "internal"),
                                                   ("state", "=", "assigned"),
                                                   ("product_id", "=", front)])
    _validate(env, storage)
    _call(env, "stock.warehouse.orderpoint", "action_open_orderpoints")
    env.call("stock.warehouse.orderpoint", "create", {
        "product_id": front, "product_min_qty": 5, "product_max_qty": 15, "trigger": "auto"})
    env.call("stock.warehouse", "write", [warehouse], {"reception_steps": "one_step"})


def seed_ch26(env):
    components = env.call("product.template", "create", [
        {"name": "Friction Material", "type": "consu", "is_storable": True, "standard_price": 8.0},
        {"name": "Backing Plate", "type": "consu", "is_storable": True, "standard_price": 5.0},
    ])
    friction, plate = [env.call("product.product", "search", [("product_tmpl_id", "=", t)])[0]
                       for t in components]
    warehouse = _id(env, "stock.warehouse", [])
    stock = env.call("stock.warehouse", "read", [warehouse], ["lot_stock_id"])[0]["lot_stock_id"][0]
    counting = {"inventory_mode": True}
    quants = env.call("stock.quant", "create", [
        {"product_id": p, "location_id": stock, "inventory_quantity": 20} for p in (friction, plate)],
        context=counting)
    _call(env, "stock.quant", "action_apply_inventory", quants, context=counting)
    tmpl, front, _ = _brake_pads(env)
    env.call("mrp.bom", "create", {
        "product_tmpl_id": tmpl, "product_qty": 1, "type": "normal",
        "bom_line_ids": [(0, 0, {"product_id": friction, "product_qty": 0.5}),
                         (0, 0, {"product_id": plate, "product_qty": 1.0})],
        "operation_ids": [(0, 0, {"name": "Bond friction material",
                                  "workcenter_id": _id(env, "mrp.workcenter", [("name", "=", "Assembly 1")])})],
    })
    production = env.call("mrp.production", "create", {"product_id": front, "product_qty": 4})
    _call(env, "mrp.production", "action_confirm", [production])
    _call(env, "mrp.production", "button_mark_done", [production])


def seed_ch27(env):
    env.call("res.users", "write", [env.uid],
             {"group_ids": [(4, _xmlid(env, "account.group_account_readonly"))]})
    entry = env.call("account.move", "create", {
        "journal_id": _id(env, "account.journal", [("code", "=", "MISC")]), "move_type": "entry",
        "line_ids": [(0, 0, {"account_id": _account(env, "611000"), "name": "Workshop tool cabinet", "debit": 250.0}),
                     (0, 0, {"account_id": _account(env, "101401"), "name": "Paid from bank", "credit": 250.0})],
    })
    _call(env, "account.move", "action_post", [entry])


def seed_ch28(env):
    order = _first_brake_order(env)
    context = {"active_model": "sale.order", "active_ids": [order], "active_id": order}
    wizard = env.call("sale.advance.payment.inv", "create", {"advance_payment_method": "delivered"}, context=context)
    _call(env, "sale.advance.payment.inv", "create_invoices", [wizard], context=context)
    invoices = env.call("sale.order", "read", [order], ["invoice_ids"])[0]["invoice_ids"]
    _call(env, "account.move", "action_post", invoices)
    context = {"active_model": "account.move", "active_ids": invoices}
    for values in ({"amount": 200.0}, {}):  # 200.00 first, then the default: what is left
        register = env.call("account.payment.register", "create", values, context=context)
        _call(env, "account.payment.register", "action_create_payments", [register], context=context)


def _sale_tax(env, name, distribution, **values):
    """A 15% sale tax; distribution is [(repartition_type, factor, account)] for invoices and refunds."""
    lines = [(0, 0, {"document_type": doc, "repartition_type": kind, "factor_percent": factor,
                     "account_id": account})
             for doc in ("invoice", "refund") for kind, factor, account in distribution]
    return env.call("account.tax", "create", dict(
        name=name, amount_type="percent", amount=15.0, type_tax_use="sale",
        tax_group_id=_id(env, "account.tax.group", [("name", "=", "Tax 15%")]),
        country_id=_id(env, "res.country", [("code", "=", "US")]), repartition_line_ids=lines, **values))


def seed_ch29(env):
    acme = _partner(env, "Acme Corporation")
    _, front, _ = _brake_pads(env)

    def invoice(lines):
        move = env.call("account.move", "create", {
            "move_type": "out_invoice", "partner_id": acme,
            "invoice_line_ids": [(0, 0, {"product_id": front, "quantity": 1, "price_unit": price,
                                         "tax_ids": [(6, 0, [tax])]}) for price, tax in lines],
        })
        _call(env, "account.move", "action_post", [move])

    state_tax = _account(env, "251000")
    city_tax = env.call("account.account", "create", {
        "code": "251100", "name": "City Tax Received", "account_type": "liability_current"})
    split = _sale_tax(env, "15% Split (State 9 / City 6)",
                      [("base", 100.0, False), ("tax", 60.0, state_tax), ("tax", 40.0, city_tax)])
    invoice([(200.0, split)])
    included = _sale_tax(env, "15% (Tax Included)", [("base", 100.0, False), ("tax", 100.0, False)],
                         price_include_override="tax_included")
    invoice([(115.0, included), (100.0, included)])
    tax_lines = env.call("account.tax.repartition.line", "search",
                         [("tax_id", "=", included), ("repartition_type", "=", "tax")])
    env.call("account.tax.repartition.line", "write", tax_lines, {"account_id": state_tax})
    invoice([(115.0, included), (100.0, included)])

    nordwerk = env.call("res.partner", "create", {
        "name": "Nordwerk Fahrzeugtechnik GmbH", "is_company": True, "city": "Bremen", "zip": "28195",
        "country_id": _id(env, "res.country", [("code", "=", "DE")])})
    env.call("sale.order", "create", {"partner_id": nordwerk,
                                      "order_line": [(0, 0, {"product_id": front, "product_uom_qty": 4})]})
    company = env.call("res.users", "read", [env.uid], ["company_id"])[0]["company_id"][0]
    rounding = {"partner_id": acme, "order_line": [
        (0, 0, {"product_id": front, "product_uom_qty": 1, "price_unit": 10.10}) for _ in range(3)]}
    env.call("sale.order", "create", rounding)
    env.call("res.company", "write", [company], {"tax_calculation_rounding_method": "round_per_line"})
    env.call("sale.order", "create", rounding)
    env.call("res.company", "write", [company], {"tax_calculation_rounding_method": "round_globally"})


def seed_ch30(env):
    tmpl, _, _ = _brake_pads(env)
    goods = _id(env, "product.category", [("name", "=", "Goods")])
    env.call("product.template", "write", [tmpl], {"categ_id": goods})
    env.call("product.category", "write", [goods],
             {"property_cost_method": "average", "property_valuation": "real_time"})
    customers = _id(env, "stock.location", [("usage", "=", "customer")])
    env.call("stock.location", "write", [customers], {"valuation_account_id": _account(env, "500000")})
    delivery = env.call("sale.order", "read", [_first_brake_order(env)], ["picking_ids"])[0]["picking_ids"]
    _validate(env, delivery)


def seed_ch49(env):
    _settings(env, group_discount_per_so_line=True)


# Inventory deep dive, database "warehouse" (no demo data).

def seed_inv01(env):
    _install(env, ["stock"])
    _settings(env, group_stock_multi_locations=True, group_uom=True)
    depot = _id(env, "stock.warehouse", [])
    env.call("stock.warehouse", "write", [depot], {"name": "LibreFleet Depot", "code": "LFD"})
    stock = _id(env, "stock.location", [("complete_name", "=", "LFD/Stock")])
    env.call("stock.location", "create", [{"name": "Shelf A", "location_id": stock, "usage": "internal"},
                                          {"name": "Shelf B", "location_id": stock, "usage": "internal"}])
    goods = [{"name": n, "type": "consu", "is_storable": True}
             for n in ("Brake Pad Set", "Engine Oil 5W-30 1L", "Diagnostic Tablet")]
    goods += [{"name": "Shop Rags", "type": "consu", "is_storable": False},
              {"name": "Labour Hour", "type": "service"}]
    env.call("product.template", "create", goods)
    vendor = env.call("res.partner", "create", {"name": "Brembo Parts"})
    receipts = _id(env, "stock.picking.type", [("code", "=", "incoming"), ("warehouse_id", "=", depot)])
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    picking = env.call("stock.picking", "create", {
        "partner_id": vendor, "picking_type_id": receipts,
        "move_ids": [(0, 0, {"product_id": variant(n), "product_uom_qty": qty})
                     for n, qty in (("Brake Pad Set", 20), ("Engine Oil 5W-30 1L", 12),
                                    ("Diagnostic Tablet", 1), ("Shop Rags", 50))],
    })
    _validate(env, [picking])


def seed_inv02(env):
    depot = env.call("stock.warehouse", "read", [_id(env, "stock.warehouse", [])],
                     ["out_type_id", "in_type_id", "lot_stock_id"])[0]
    out_type, in_type, stock = depot["out_type_id"][0], depot["in_type_id"][0], depot["lot_stock_id"][0]
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    pads, oil, tablet = variant("Brake Pad Set"), variant("Engine Oil 5W-30 1L"), variant("Diagnostic Tablet")
    garage = env.call("res.partner", "create", {"name": "Garage Nord"})
    brembo = _id(env, "res.partner", [("name", "=", "Brembo Parts")])

    def picking(partner, kind, lines):
        return env.call("stock.picking", "create", {
            "partner_id": partner, "picking_type_id": kind,
            "move_ids": [(0, 0, {"product_id": p, "product_uom_qty": q}) for p, q in lines]})

    out1 = picking(garage, out_type, [(pads, 8), (oil, 2)])
    _call(env, "stock.picking", "action_confirm", [out1])
    _validate(env, [out1])
    out2 = picking(garage, out_type, [(pads, 15)])  # only 12 free: validated short, backorder for 3
    _call(env, "stock.picking", "action_confirm", [out2])
    _call(env, "stock.picking", "button_validate", [out2], context={"skip_backorder": True, "skip_sms": True})
    _validate(env, [picking(brembo, in_type, [(pads, 10)])])  # the receipt reserves the backorder by itself
    _validate(env, [_id(env, "stock.picking", [("backorder_id", "=", out2)])])
    wizard = env.call("stock.return.picking", "create", {"picking_id": out1})
    for line in env.call("stock.return.picking.line", "search_read", [("wizard_id", "=", wizard)], fields=["product_id"]):
        if line["product_id"][0] == pads:
            env.call("stock.return.picking.line", "write", [line["id"]], {"quantity": 2})
        else:
            env.call("stock.return.picking.line", "unlink", [line["id"]])
    _validate(env, [env.call("stock.return.picking", "action_create_returns", [wizard])["res_id"]])
    scrap = env.call("stock.scrap", "create", {"product_id": oil, "scrap_qty": 1, "location_id": stock,
                                                 "scrap_reason_tag_ids": [(0, 0, {"name": "Leaked"})]})
    _call(env, "stock.scrap", "action_validate", [scrap])
    env.call("stock.picking.type", "write", [out_type], {"reservation_method": "manual"})
    out4 = picking(garage, out_type, [(tablet, 1)])
    _call(env, "stock.picking", "action_confirm", [out4])
    _call(env, "stock.picking", "action_assign", [out4])
    _call(env, "stock.picking", "action_cancel", [out4])
    env.call("stock.picking.type", "write", [out_type], {"reservation_method": "at_confirm"})


def _finish_chain(env, picking):
    """Validate a transfer, then every Ready transfer its moves feed, as the reader clicks Next Transfer."""
    _validate(env, [picking])
    moves = env.call("stock.move", "search_read", [("picking_id", "=", picking)], fields=["move_dest_ids"])
    dests = [d for m in moves for d in m["move_dest_ids"]]
    for nxt in env.call("stock.move", "search_read", [("id", "in", dests), ("picking_id.state", "=", "assigned")],
                        fields=["picking_id"]):
        _finish_chain(env, nxt["picking_id"][0])


def seed_inv03(env):
    _install(env, ["sale_management", "purchase"])
    _settings(env, group_stock_adv_location=True)
    depot = _id(env, "stock.warehouse", [])
    env.call("stock.warehouse", "write", [depot], {"reception_steps": "two_steps", "delivery_steps": "pick_pack_ship"})
    kinds = env.call("stock.warehouse", "read", [depot], ["in_type_id", "pick_type_id"])[0]
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    pads, oil, tablet = variant("Brake Pad Set"), variant("Engine Oil 5W-30 1L"), variant("Diagnostic Tablet")
    garage = _id(env, "res.partner", [("name", "=", "Garage Nord")])
    brembo = _id(env, "res.partner", [("name", "=", "Brembo Parts")])

    def picking(partner, kind, lines):
        return env.call("stock.picking", "create", {
            "partner_id": partner, "picking_type_id": kind,
            "move_ids": [(0, 0, {"product_id": p, "product_uom_qty": q}) for p, q in lines]})

    _finish_chain(env, picking(brembo, kinds["in_type_id"][0], [(oil, 6)]))  # receipt, then the pushed Storage
    pick = picking(garage, kinds["pick_type_id"][0], [(pads, 4)])
    _call(env, "stock.picking", "action_confirm", [pick])
    _finish_chain(env, pick)  # pick, then the pushed Pack and Delivery
    _settings(env, replenish_on_order=True)
    mto = _id(env, "stock.route", [("name", "ilike", "Replenish on Order")])
    env.call("product.template", "write", [_id(env, "product.template", [("name", "=", "Diagnostic Tablet")])],
             {"route_ids": [(4, mto)], "seller_ids": [(0, 0, {"partner_id": brembo, "price": 400})]})
    order = env.call("sale.order", "create", {
        "partner_id": garage,
        "order_line": [(0, 0, {"product_id": tablet, "product_uom_qty": 1, "price_unit": 650})]})
    _call(env, "sale.order", "action_confirm", [order])
    po = _id(env, "purchase.order", [("origin", "=", env.call("sale.order", "read", [order], ["name"])[0]["name"])])
    _call(env, "purchase.order", "button_confirm", [po])
    for receipt in env.call("purchase.order", "read", [po], ["picking_ids"])[0]["picking_ids"]:
        _finish_chain(env, receipt)  # receipt, Storage, then the waiting Pick, Pack and Delivery


def seed_inv04(env):
    _install(env, ["mrp"])
    depot = _id(env, "stock.warehouse", [])
    kinds = env.call("stock.warehouse", "read", [depot], ["in_type_id", "pick_type_id", "sam_type_id"])[0]
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    env.call("product.template", "create", [{"name": "Friction Pad", "type": "consu", "is_storable": True},
                                            {"name": "Backing Plate", "type": "consu", "is_storable": True}])
    pads, oil, friction, plate = (variant(n) for n in ("Brake Pad Set", "Engine Oil 5W-30 1L", "Friction Pad", "Backing Plate"))
    garage = _id(env, "res.partner", [("name", "=", "Garage Nord")])
    brembo = _id(env, "res.partner", [("name", "=", "Brembo Parts")])

    def picking(partner, kind, lines):
        return env.call("stock.picking", "create", {
            "partner_id": partner, "picking_type_id": kind,
            "move_ids": [(0, 0, {"product_id": p, "product_uom_qty": q}) for p, q in lines]})

    _finish_chain(env, picking(brembo, kinds["in_type_id"][0], [(friction, 20), (plate, 20)]))
    pads_tmpl = _id(env, "product.template", [("name", "=", "Brake Pad Set")])
    env.call("mrp.bom", "create", {
        "product_tmpl_id": pads_tmpl, "product_qty": 1, "type": "normal",
        "bom_line_ids": [(0, 0, {"product_id": friction, "product_qty": 2}), (0, 0, {"product_id": plate, "product_qty": 2})]})
    mo = env.call("mrp.production", "create", {"product_id": pads, "product_qty": 3})
    _call(env, "mrp.production", "action_confirm", [mo])
    _call(env, "mrp.production", "button_mark_done", [mo])  # Produce All, in one step
    env.call("stock.warehouse", "write", [depot], {"manufacture_steps": "pbm_sam"})
    kit_tmpl = env.call("product.template", "create", {"name": "Brake Service Kit", "type": "consu",
                                                        "is_storable": False, "list_price": 150})
    env.call("mrp.bom", "create", {
        "product_tmpl_id": kit_tmpl, "product_qty": 1, "type": "phantom",
        "bom_line_ids": [(0, 0, {"product_id": pads, "product_qty": 1}), (0, 0, {"product_id": oil, "product_qty": 2})]})
    kit = picking(garage, kinds["pick_type_id"][0], [(variant("Brake Service Kit"), 1)])
    _call(env, "stock.picking", "action_confirm", [kit])  # explodes the kit into its parts
    _finish_chain(env, kit)
    env.call("product.template", "write", [pads_tmpl], {"route_ids": [(4, _id(env, "stock.route", [("name", "ilike", "Replenish on Order")]))]})
    order = env.call("sale.order", "create", {
        "partner_id": garage, "order_line": [(0, 0, {"product_id": pads, "product_uom_qty": 2, "price_unit": 120})]})
    _call(env, "sale.order", "action_confirm", [order])
    mo2 = _id(env, "mrp.production", [("origin", "=", env.call("sale.order", "read", [order], ["name"])[0]["name"])])
    for pc in env.call("mrp.production", "read", [mo2], ["picking_ids"])[0]["picking_ids"]:
        _validate(env, [pc])  # Pick Components: Stock to Pre-Production
    _call(env, "mrp.production", "button_mark_done", [mo2])
    sfp = _id(env, "stock.picking", [("picking_type_id", "=", kinds["sam_type_id"][0]), ("state", "=", "assigned")])
    _finish_chain(env, sfp)  # Store Finished Product, then the waiting Pick, Pack and Delivery


def seed_inv05(env):
    OP = "stock.warehouse.orderpoint"
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    tmpl = lambda n: _id(env, "product.template", [("name", "=", n)])
    pads, oil = variant("Brake Pad Set"), variant("Engine Oil 5W-30 1L")
    garage = _id(env, "res.partner", [("name", "=", "Garage Nord")])
    brembo = _id(env, "res.partner", [("name", "=", "Brembo Parts")])
    stock = _id(env, "stock.location", [("complete_name", "=", "LFD/Stock")])
    pack6 = _id(env, "uom.uom", [("name", "=", "Pack of 6")])
    order = env.call("sale.order", "create", {
        "partner_id": garage, "order_line": [(0, 0, {"product_id": oil, "product_uom_qty": 20, "price_unit": 12})]})
    _call(env, "sale.order", "action_confirm", [order])
    _call(env, OP, "action_open_orderpoints")  # the Replenishment report: creates the oil's suggestion
    nordic = env.call("res.partner", "create", {"name": "Nordic Lubricants"})
    env.call("product.template", "write", [tmpl("Engine Oil 5W-30 1L")], {
        "uom_ids": [(4, pack6)], "seller_ids": [(0, 0, {"partner_id": nordic, "price": 6, "delay": 3})]})
    op_oil = _id(env, OP, [("product_id", "=", oil)])
    env.call(OP, "write", [op_oil], {"product_min_qty": 10, "product_max_qty": 30, "replenishment_uom_id": pack6})
    env.call(OP, "action_replenish_auto", [op_oil])  # Automate: 42 bottles, trigger Auto
    po = _id(env, "purchase.order", [("order_line.orderpoint_id", "=", op_oil)])
    _call(env, "purchase.order", "button_confirm", [po])
    for receipt in env.call("purchase.order", "read", [po], ["picking_ids"])[0]["picking_ids"]:
        _finish_chain(env, receipt)
    pick = _id(env, "stock.picking", [("origin", "=", env.call("sale.order", "read", [order], ["name"])[0]["name"])])
    _finish_chain(env, pick)  # fully reserved now: Pick, Pack, Delivery
    env.call(OP, "create", {"product_id": pads, "location_id": stock, "product_min_qty": 10, "product_max_qty": 15,
                            "route_id": _id(env, "stock.route", [("name", "=", "Manufacture")]), "trigger": "auto"})
    _call(env, "stock.rule", "run_scheduler")  # Procurement: run scheduler
    _call(env, OP, "action_open_orderpoints")  # the components' suggestions, forecast -6
    for name, price in (("Friction Pad", 4), ("Backing Plate", 3)):
        env.call("product.template", "write", [tmpl(name)], {"seller_ids": [(0, 0, {"partner_id": brembo, "price": price})]})
    ops = env.call(OP, "search", [("product_id.name", "in", ["Friction Pad", "Backing Plate"])])
    _call(env, OP, "action_replenish", ops)
    po2 = _id(env, "purchase.order", [("order_line.product_id.name", "=", "Friction Pad")])
    _call(env, "purchase.order", "button_confirm", [po2])
    for receipt in env.call("purchase.order", "read", [po2], ["picking_ids"])[0]["picking_ids"]:
        _finish_chain(env, receipt)
    mo = _id(env, "mrp.production", [("orderpoint_id", "!=", False)])
    for pc in env.call("mrp.production", "read", [mo], ["picking_ids"])[0]["picking_ids"]:
        _validate(env, [pc])  # Pick Components
    _call(env, "mrp.production", "button_mark_done", [mo])
    sfp = _id(env, "stock.picking", [("picking_type_id.sequence_code", "=", "SFP"), ("state", "=", "assigned")])
    _validate(env, [sfp])


def seed_inv06(env):
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    oil = variant("Engine Oil 5W-30 1L")
    lfd = _id(env, "stock.warehouse", [("code", "=", "LFD")])
    van = env.call("stock.warehouse", "create", {"name": "Service Van", "code": "VAN"})
    env.call("stock.warehouse", "write", [van], {"buy_to_resupply": False, "manufacture_to_resupply": False,
                                                 "resupply_wh_ids": [(4, lfd)]})
    route = _id(env, "stock.route", [("supplied_wh_id", "=", van), ("supplier_wh_id", "=", lfd)])
    van_stock = env.call("stock.warehouse", "read", [van], ["lot_stock_id"])[0]["lot_stock_id"][0]
    op = env.call("stock.warehouse.orderpoint", "create", {
        "product_id": oil, "location_id": van_stock, "product_min_qty": 4, "product_max_qty": 10,
        "route_id": route, "trigger": "auto"})
    _call(env, "stock.warehouse.orderpoint", "action_replenish", [op])
    pick = _id(env, "stock.picking", [("origin", "=", env.call("stock.warehouse.orderpoint", "read", [op], ["name"])[0]["name"]),
                                      ("state", "=", "assigned")])
    _finish_chain(env, pick)  # Pick, Pack, Delivery to transit, then the van's Receipt
    garage = _id(env, "res.partner", [("name", "=", "Garage Nord")])
    order = env.call("sale.order", "create", {
        "partner_id": garage, "warehouse_id": van,
        "order_line": [(0, 0, {"product_id": oil, "product_uom_qty": 2, "price_unit": 12})]})
    _call(env, "sale.order", "action_confirm", [order])
    _validate(env, env.call("sale.order", "read", [order], ["picking_ids"])[0]["picking_ids"])
    _settings(env, group_stock_tracking_owner=True, group_warning_stock=True)
    nordic = _id(env, "res.partner", [("name", "=", "Nordic Lubricants")])
    env.call("product.template", "create", {"name": "Coolant 5L", "type": "consu", "is_storable": True, "standard_price": 20})
    coolant = variant("Coolant 5L")
    kinds = env.call("stock.warehouse", "read", [lfd], ["in_type_id", "pick_type_id"])[0]
    receipt = env.call("stock.picking", "create", {
        "partner_id": nordic, "owner_id": nordic, "picking_type_id": kinds["in_type_id"][0],
        "move_ids": [(0, 0, {"product_id": coolant, "product_uom_qty": 12})]})
    _finish_chain(env, receipt)  # receipt, then the pushed Storage, owner kept
    env.call("res.partner", "write", [garage], {"picking_warn_msg": "Deliveries at the back door, before 10:00."})
    pick = env.call("stock.picking", "create", {
        "partner_id": garage, "picking_type_id": kinds["pick_type_id"][0],
        "move_ids": [(0, 0, {"product_id": coolant, "product_uom_qty": 3})]})
    _call(env, "stock.picking", "action_confirm", [pick])
    _finish_chain(env, pick)


def seed_inv07(env):
    import datetime
    _install(env, ["product_expiry"])
    _settings(env, group_stock_production_lot=True, group_lot_on_delivery_slip=True)
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    tmpl = lambda n: _id(env, "product.template", [("name", "=", n)])
    lfd = _id(env, "stock.warehouse", [("code", "=", "LFD")])
    kinds = env.call("stock.warehouse", "read", [lfd], ["in_type_id", "lot_stock_id"])[0]
    stock = kinds["lot_stock_id"][0]
    tablet = variant("Diagnostic Tablet")
    env.call("product.template", "write", [tmpl("Diagnostic Tablet")], {"tracking": "serial", "serial_prefix_format": "DT-"})
    lot1 = env.call("stock.lot", "create", {"name": "DT-0000001", "product_id": tablet})
    inv = {"inventory_mode": True}
    old = env.call("stock.quant", "search", [("product_id", "=", tablet), ("location_id", "=", stock), ("lot_id", "=", False)])
    env.call("stock.quant", "write", old, {"inventory_quantity": 0}, context=inv)
    new = env.call("stock.quant", "create", {"product_id": tablet, "location_id": stock, "lot_id": lot1, "inventory_quantity": 1}, context=inv)
    _call(env, "stock.quant", "action_apply_inventory", old + [new], context=inv)

    def receive(partner, product, lines):
        pick = env.call("stock.picking", "create", {
            "partner_id": _id(env, "res.partner", [("name", "=", partner)]), "picking_type_id": kinds["in_type_id"][0],
            "move_ids": [(0, 0, {"product_id": product, "product_uom_qty": sum(q for _, q in lines)})]})
        _call(env, "stock.picking", "action_confirm", [pick])
        existing = env.call("stock.picking", "read", [pick], ["move_line_ids"])[0]["move_line_ids"]
        if len(existing) == len(lines):  # serials: one line per unit already, name them
            for line, (name, qty) in zip(existing, lines):
                env.call("stock.move.line", "write", [line], {"lot_name": name, "quantity": qty})
        else:  # lots: one line for everything, split it per lot
            env.call("stock.move.line", "write", existing, {"lot_name": lines[0][0], "quantity": lines[0][1]})
            for name, qty in lines[1:]:
                env.call("stock.move.line", "copy", existing, {"lot_name": name, "quantity": qty})
        _finish_chain(env, pick)  # receipt, then the pushed Storage

    receive("Brembo Parts", tablet, [("DT-0000002", 1), ("DT-0000003", 1)])
    env.call("product.template", "create", {"name": "Brake Fluid DOT 4 1L", "type": "consu", "is_storable": True, "list_price": 9,
                                            "tracking": "lot", "use_expiration_date": True, "expiration_time": 365,
                                            "use_time": 60, "removal_time": 30, "alert_time": 45})
    fluid = variant("Brake Fluid DOT 4 1L")
    receive("Nordic Lubricants", fluid, [("BF-001", 12), ("BF-002", 12)])
    bf1 = _id(env, "stock.lot", [("name", "=", "BF-001")])

    def dates(expiry):  # a write in code does not shift the other dates, so set all four
        f = lambda d: d.strftime("%Y-%m-%d %H:%M:%S")
        return {"expiration_date": f(expiry), "use_date": f(expiry - datetime.timedelta(days=60)),
                "removal_date": f(expiry - datetime.timedelta(days=30)), "alert_date": f(expiry - datetime.timedelta(days=45))}

    now = datetime.datetime.utcnow()
    env.call("stock.lot", "write", [bf1], dates(now + datetime.timedelta(days=40)))
    env.call("stock.location", "write", [stock], {"removal_strategy_id": _xmlid(env, "product_expiry.removal_fefo")})
    garage = _id(env, "res.partner", [("name", "=", "Garage Nord")])
    order = env.call("sale.order", "create", {
        "partner_id": garage, "order_line": [(0, 0, {"product_id": fluid, "product_uom_qty": 6, "price_unit": 9})]})
    _call(env, "sale.order", "action_confirm", [order])
    _finish_chain(env, env.call("sale.order", "read", [order], ["picking_ids"])[0]["picking_ids"][0])  # FEFO picks BF-001
    env.call("stock.lot", "write", [bf1], dates(now - datetime.timedelta(hours=1)))  # block the lot
    out = _id(env, "stock.picking", [("origin", "=", env.call("sale.order", "read", [order], ["name"])[0]["name"]),
                                     ("picking_type_id.sequence_code", "=", "OUT")])
    ctx = {"active_id": out, "active_ids": [out], "active_model": "stock.picking"}
    wizard = env.call("stock.return.picking", "create", {}, context=ctx)
    action = env.call("stock.return.picking", "action_create_returns_all", [wizard], context=ctx)
    skip = {"skip_sms": True, "skip_expired": True}  # Confirm on the expired-lot warning
    _call(env, "stock.picking", "button_validate", [action["res_id"]], context=skip)
    for mv in env.call("stock.move", "search_read", [("picking_id", "=", action["res_id"])], fields=["move_dest_ids"]):
        for nxt in env.call("stock.move", "read", mv["move_dest_ids"], ["picking_id"]):
            _call(env, "stock.picking", "button_validate", [nxt["picking_id"][0]], context=skip)
    scrap = env.call("stock.scrap", "create", {"product_id": fluid, "lot_id": bf1, "scrap_qty": 12, "location_id": stock,
                                               "origin": "Recall BF-001", "scrap_reason_tag_ids": [(0, 0, {"name": "Recalled"})]})
    _call(env, "stock.scrap", "action_validate", [scrap])


def seed_inv08(env):
    _settings(env, group_stock_tracking_lot=True)
    new_type = lambda vals: env.call("stock.package.type", "create", vals)
    carton = new_type({"name": "Carton", "sequence_code": "CTN", "barcode": "CARTON", "packaging_length": 400, "width": 300,
                       "height": 300, "base_weight": 0.4, "max_weight": 20})
    pallet = new_type({"name": "Pallet", "sequence_code": "PAL", "packaging_length": 1200, "width": 800, "height": 150,
                       "base_weight": 25, "max_weight": 1000})
    tote = new_type({"name": "Tote", "sequence_code": "TOTE", "package_use": "reusable"})
    lfd = _id(env, "stock.warehouse", [("code", "=", "LFD")])
    kinds = env.call("stock.warehouse", "read", [lfd], ["in_type_id", "pick_type_id"])[0]
    env.call("stock.picking.type", "write", [kinds["in_type_id"][0], kinds["pick_type_id"][0]], {"set_package_type": True})
    pack6 = _id(env, "uom.uom", [("name", "=", "Pack of 6")])
    env.call("uom.uom", "write", [pack6], {"package_type_id": carton})
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    oil, pads = variant("Engine Oil 5W-30 1L"), variant("Brake Pad Set")
    env.call("product.product", "write", [oil], {"barcode": "5901234123457"})
    env.call("product.uom", "create", {"product_id": oil, "uom_id": pack6, "barcode": "15901234123454"})
    receipt = env.call("stock.picking", "create", {
        "partner_id": _id(env, "res.partner", [("name", "=", "Nordic Lubricants")]), "picking_type_id": kinds["in_type_id"][0],
        "move_ids": [(0, 0, {"product_id": oil, "product_uom_qty": 12}), (0, 0, {"product_id": pads, "product_uom_qty": 10})]})
    _call(env, "stock.picking", "action_confirm", [receipt])
    lines = env.call("stock.move.line", "search", [("picking_id", "=", receipt)], order="id")
    for line in lines:  # one carton per line, as with one row selected in Moves
        _call(env, "stock.move.line", "action_put_in_pack", [line], package_type_id=carton)
    _call(env, "stock.move.line", "action_put_in_pack", lines, package_type_id=pallet, context={"force_move_lines": True})
    _finish_chain(env, receipt)  # receipt, then the Storage that moves the whole pallet
    tote_pkg = env.call("stock.package", "create", {"package_type_id": tote})
    order = env.call("sale.order", "create", {"partner_id": _id(env, "res.partner", [("name", "=", "Garage Nord")]),
                                              "order_line": [(0, 0, {"product_id": oil, "product_uom_qty": 2, "product_uom_id": pack6})]})
    _call(env, "sale.order", "action_confirm", [order])
    pick = env.call("sale.order", "read", [order], ["picking_ids"])[0]["picking_ids"][0]
    _call(env, "stock.picking", "action_put_in_pack", [pick], package_id=tote_pkg)
    _validate(env, [pick])
    pack = _id(env, "stock.picking", [("move_ids.move_orig_ids.picking_id", "=", pick)])
    _call(env, "stock.picking", "action_put_in_pack", [pack])  # the Pack of 6 picks the Carton
    _finish_chain(env, pack)


def seed_inv09(env):
    goods = _id(env, "product.category", [("complete_name", "=", "Goods")])
    fluids = env.call("product.category", "create", {"name": "Fluids", "parent_id": goods})
    variant = lambda n: _id(env, "product.product", [("name", "=", n)])
    oil, pads = variant("Engine Oil 5W-30 1L"), variant("Brake Pad Set")
    env.call("product.product", "write", [oil], {"categ_id": fluids})
    pallet = _id(env, "stock.package.type", [("name", "=", "Pallet")])
    shelf = env.call("stock.storage.category", "create", {"name": "Parts Shelf", "allow_new_product": "same",
                                                          "capacity_ids": [(0, 0, {"product_id": pads, "quantity": 20})]})
    bay = env.call("stock.storage.category", "create", {"name": "Pallet Bay", "allow_new_product": "empty",
                                                        "capacity_ids": [(0, 0, {"package_type_id": pallet, "quantity": 1})]})
    loc = lambda name: _id(env, "stock.location", [("complete_name", "=", name)])
    stock = loc("LFD/Stock")
    env.call("stock.location", "write", [loc("LFD/Stock/Shelf A"), loc("LFD/Stock/Shelf B")], {"storage_category_id": shelf})
    for name in ("Pallet Bay 1", "Pallet Bay 2"):
        env.call("stock.location", "create", {"name": name, "location_id": stock, "storage_category_id": bay})
    rack = env.call("stock.location", "create", {"name": "Fluids Rack", "location_id": stock})
    rule = lambda vals: env.call("stock.putaway.rule", "create", dict(vals, location_in_id=stock))
    rule({"product_id": pads, "location_out_id": stock, "sublocation": "closest_location", "storage_category_id": shelf})
    rule({"category_id": fluids, "location_out_id": rack})
    rule({"package_type_ids": [(6, 0, [pallet])], "location_out_id": stock, "sublocation": "closest_location", "storage_category_id": bay})
    lfd = _id(env, "stock.warehouse", [("code", "=", "LFD")])
    kinds = env.call("stock.warehouse", "read", [lfd], ["in_type_id", "int_type_id"])[0]
    for partner, product, qty in (("Brembo Parts", pads, 15), ("Brembo Parts", pads, 10), ("Nordic Lubricants", oil, 6)):
        receipt = env.call("stock.picking", "create", {
            "partner_id": _id(env, "res.partner", [("name", "=", partner)]), "picking_type_id": kinds["in_type_id"][0],
            "move_ids": [(0, 0, {"product_id": product, "product_uom_qty": qty})]})
        _call(env, "stock.picking", "action_confirm", [receipt])
        _finish_chain(env, receipt)  # receipt, then the Storage that putaway routes
    move = env.call("stock.picking", "create", {"picking_type_id": kinds["int_type_id"][0], "location_id": stock, "location_dest_id": stock})
    _call(env, "stock.picking", "action_add_entire_packs", [move], [_id(env, "stock.package", [("name", "=", "PAL0000001")])])
    _validate(env, [move])
    order = env.call("sale.order", "create", {"partner_id": _id(env, "res.partner", [("name", "=", "Garage Nord")]),
                                              "order_line": [(0, 0, {"product_id": oil, "product_uom_qty": 6})]})
    _call(env, "sale.order", "action_confirm", [order])
    pick = env.call("sale.order", "read", [order], ["picking_ids"])[0]["picking_ids"][0]
    env.call("product.category", "write", [fluids], {"removal_strategy_id": _xmlid(env, "stock.removal_lifo")})
    _call(env, "stock.picking", "do_unreserve", [pick])
    _call(env, "stock.picking", "action_assign", [pick])  # LIFO now takes the Fluids Rack
    _finish_chain(env, pick)

def seed_inv10(env):
    inv = {"inventory_mode": True}
    quant = lambda domain: _id(env, "stock.quant", domain)
    oil = quant([("product_id.name", "=", "Engine Oil 5W-30 1L"), ("location_id.complete_name", "=", "LFD/Stock"), ("package_id", "=", False)])
    env.call("stock.quant", "write", [oil], {"inventory_quantity": 12, "inventory_quantity_set": True}, context=inv)
    _call(env, "stock.quant", "action_apply_inventory", [oil], context=inv)  # a row Apply: no reason asked
    line = _id(env, "stock.move.line", [("is_inventory", "=", True), ("product_id.name", "=", "Engine Oil 5W-30 1L"), ("location_id.complete_name", "=", "LFD/Stock")], order="id desc")
    _call(env, "stock.move.line", "action_revert_inventory", [line])
    shelf_a = quant([("product_id.name", "=", "Brake Pad Set"), ("location_id.complete_name", "=", "LFD/Stock/Shelf A")])
    shelf_b = quant([("product_id.name", "=", "Brake Pad Set"), ("location_id.complete_name", "=", "LFD/Stock/Shelf B")])
    request = env.call("stock.request.count", "create", {"quant_ids": [(6, 0, [shelf_a, shelf_b])], "user_id": 2})
    _call(env, "stock.request.count", "action_request_count", [request])
    env.call("stock.quant", "write", [shelf_a], {"inventory_quantity": 15, "inventory_quantity_set": True}, context=inv)
    env.call("stock.quant", "write", [shelf_b], {"inventory_quantity": 9, "inventory_quantity_set": True}, context=inv)
    name = env.call("stock.inventory.adjustment.name", "create", {"quant_ids": [(6, 0, [shelf_a, shelf_b])], "inventory_adjustment_name": "Shelf count October"})
    _call(env, "stock.inventory.adjustment.name", "action_apply", [name])
    bf2 = quant([("lot_id.name", "=", "BF-002"), ("location_id.complete_name", "=", "LFD/Stock")])
    env.call("stock.quant", "write", [bf2], {"inventory_quantity": 12, "inventory_quantity_set": True}, context=inv)
    fluid = _id(env, "product.product", [("name", "=", "Brake Fluid DOT 4 1L")])
    stock = _id(env, "stock.location", [("complete_name", "=", "LFD/Stock")])
    scrap = env.call("stock.scrap", "create", {"product_id": fluid, "lot_id": _id(env, "stock.lot", [("name", "=", "BF-002")]), "scrap_qty": 1,
                                               "location_id": stock, "origin": "Dropped while counting",
                                               "scrap_reason_tag_ids": [(0, 0, {"name": "Damaged"})]})
    _call(env, "stock.scrap", "action_validate", [scrap])
    conflict = env.call("stock.inventory.conflict", "create", {"quant_ids": [(6, 0, [bf2])], "quant_to_fix_ids": [(6, 0, [bf2])]})
    _call(env, "stock.inventory.conflict", "action_keep_difference", [conflict], context=inv)
    coolant = quant([("product_id.name", "=", "Coolant 5L"), ("location_id.complete_name", "=", "LFD/Stock")])
    move = env.call("stock.quant.relocate", "create", {"quant_ids": [(6, 0, [coolant])], "message": "Coolant belongs with the fluids",
                                                       "dest_location_id": _id(env, "stock.location", [("complete_name", "=", "LFD/Stock/Fluids Rack")])})
    _call(env, "stock.quant.relocate", "action_relocate_quants", [move])
    env.call("stock.location", "write", [_id(env, "stock.location", [("complete_name", "=", "LFD/Stock/Shelf A")])], {"cyclic_inventory_frequency": 30})
    _install(env, ["stock_picking_batch"])
    pick_type = _id(env, "stock.picking.type", [("warehouse_id.code", "=", "LFD"), ("sequence_code", "=", "PICK")])
    env.call("stock.picking.type", "write", [pick_type], {"auto_batch": True, "batch_group_by_src_loc": True})
    sud = env.call("res.partner", "create", {"name": "Garage Sud"})
    for partner, qty in ((_id(env, "res.partner", [("name", "=", "Garage Nord")]), 2), (sud, 3)):
        order = env.call("sale.order", "create", {"partner_id": partner, "order_line": [(0, 0, {"product_id": fluid, "product_uom_qty": qty})]})
        _call(env, "sale.order", "action_confirm", [order])
    batch = _id(env, "stock.picking.batch", [("state", "=", "in_progress"), ("picking_type_id", "=", pick_type)])
    _call(env, "stock.picking.batch", "action_done", [batch], context={"skip_sms": True})
    for kind in ("PACK", "OUT"):
        _validate(env, env.call("stock.picking", "search", [("picking_type_id.sequence_code", "=", kind), ("state", "=", "assigned")]))

def seed_inv11(env):
    _install(env, ["stock_delivery", "stock_dropshipping", "mrp_subcontracting"])
    oil = _id(env, "product.template", [("name", "=", "Engine Oil 5W-30 1L")])
    env.call("product.template", "write", [oil], {"weight": 1, "hs_code": "271019", "country_of_origin": _id(env, "res.country", [("code", "=", "DE")])})
    fee = lambda name: env.call("product.product", "create", {"name": name, "type": "service", "sale_ok": False, "purchase_ok": False})
    env.call("delivery.carrier", "create", {"name": "Depot Van", "delivery_type": "fixed", "product_id": fee("Depot Van"),
                                            "fixed_price": 15, "free_over": True, "amount": 100})
    rule = lambda top, base, per: (0, 0, {"variable": "weight", "operator": "<=", "max_value": top, "list_base_price": base,
                                          "list_price": per, "variable_factor": "weight"})
    courier = env.call("delivery.carrier", "create", {"name": "Courier by Weight", "delivery_type": "base_on_rule", "product_id": fee("Courier by Weight"),
                                                      "tracking_url": "https://track.example.com/<shipmenttrackingnumber>",
                                                      "price_rule_ids": [rule(5, 8, 0), rule(30, 5, 1)]})
    oil_p = _id(env, "product.product", [("product_tmpl_id", "=", oil)])
    order = env.call("sale.order", "create", {"partner_id": _id(env, "res.partner", [("name", "=", "Garage Sud")]),
                                              "order_line": [(0, 0, {"product_id": oil_p, "product_uom_qty": 8})]})
    wizard = env.call("choose.delivery.carrier", "create", {"order_id": order, "carrier_id": courier})
    _call(env, "choose.delivery.carrier", "update_price", [wizard])  # Get rate: 5 + 1 x 8
    _call(env, "choose.delivery.carrier", "button_confirm", [wizard])
    _call(env, "sale.order", "action_confirm", [order])
    step = lambda kind: env.call("stock.picking", "search", [("sale_id", "=", order), ("picking_type_id.sequence_code", "=", kind)])
    _validate(env, step("PICK"))
    _validate(env, step("PACK"))
    env.call("stock.picking", "write", step("OUT"), {"carrier_tracking_ref": "LF123456"})
    _validate(env, step("OUT"))
    pneu = env.call("res.partner", "create", {"name": "Pneu Direct"})
    tyre = env.call("product.product", "create", {"name": "Tyre 205/55 R16", "is_storable": True, "list_price": 90, "standard_price": 60,
                                                  "route_ids": [(6, 0, [_xmlid(env, "stock_dropshipping.route_drop_shipping")])],
                                                  "seller_ids": [(0, 0, {"partner_id": pneu, "price": 60, "delay": 3})]})
    order = env.call("sale.order", "create", {"partner_id": _id(env, "res.partner", [("name", "=", "Garage Nord")]),
                                              "order_line": [(0, 0, {"product_id": tyre, "product_uom_qty": 4})]})
    _call(env, "sale.order", "action_confirm", [order])
    po = _id(env, "purchase.order", [("partner_id", "=", pneu)])
    _call(env, "purchase.order", "button_confirm", [po])
    _validate(env, env.call("purchase.order", "read", [po], ["picking_ids"])[0]["picking_ids"])
    atelier = env.call("res.partner", "create", {"name": "Atelier Moteur"})
    engine = env.call("product.product", "create", {"name": "Rebuilt Engine", "is_storable": True, "list_price": 1500,
                                                    "seller_ids": [(0, 0, {"partner_id": atelier, "price": 800, "delay": 5})]})
    env.call("mrp.bom", "create", {"product_tmpl_id": env.call("product.product", "read", [engine], ["product_tmpl_id"])[0]["product_tmpl_id"][0],
                                   "type": "subcontract", "subcontractor_ids": [(6, 0, [atelier])],
                                   "bom_line_ids": [(0, 0, {"product_id": oil_p, "product_qty": 5})]})
    po = env.call("purchase.order", "create", {"partner_id": atelier, "order_line": [(0, 0, {"product_id": engine, "product_qty": 1})]})
    _call(env, "purchase.order", "button_confirm", [po])
    res = env.call("stock.picking", "search", [("picking_type_id.sequence_code", "=", "RES"), ("partner_id", "=", atelier)])
    # the carton still names its pallet as destination: send the oil out loose, as the chapter does
    env.call("stock.move.line", "write", env.call("stock.move.line", "search", [("picking_id", "in", res)]), {"result_package_id": False})
    _validate(env, res)
    receipt = env.call("stock.picking", "search", [("purchase_id", "=", po), ("picking_type_id.code", "=", "incoming")])[0]
    _finish_chain(env, receipt)  # the receipt, then the Storage from Input


def seed_inv12(env):
    oil = _id(env, "product.product", [("name", "=", "Engine Oil 5W-30 1L")])
    env.call("product.product", "write", [oil], {"standard_price": 6})
    goods = _id(env, "product.category", [("complete_name", "=", "Goods")])
    filters = env.call("product.category", "create", {"name": "Filters", "parent_id": goods, "property_cost_method": "fifo"})
    brembo = _id(env, "res.partner", [("name", "=", "Brembo Parts")])
    air = env.call("product.product", "create", {"name": "Air Filter", "is_storable": True, "categ_id": filters, "list_price": 25,
                                                 "seller_ids": [(0, 0, {"partner_id": brembo, "price": 8})]})

    def buy(qty, price):
        po = env.call("purchase.order", "create", {"partner_id": brembo, "order_line": [(0, 0, {"product_id": air, "product_qty": qty, "price_unit": price})]})
        _call(env, "purchase.order", "button_confirm", [po])
        _finish_chain(env, env.call("purchase.order", "read", [po], ["picking_ids"])[0]["picking_ids"][0])  # receipt, then Storage
        return po

    def sell(partner, qty):
        so = env.call("sale.order", "create", {"partner_id": _id(env, "res.partner", [("name", "=", partner)]),
                                               "order_line": [(0, 0, {"product_id": air, "product_uom_qty": qty})]})
        _call(env, "sale.order", "action_confirm", [so])
        _finish_chain(env, env.call("stock.picking", "search", [("sale_id", "=", so), ("picking_type_id.sequence_code", "=", "PICK")])[0])
        return so

    buy(10, 8)
    buy(10, 10)
    sell("Garage Nord", 12)  # FIFO: 10 x 8 + 2 x 10
    env.call("product.category", "write", [filters], {"property_cost_method": "average"})
    po = buy(10, 9)
    _call(env, "purchase.order", "action_create_invoice", [po])
    bill = env.call("purchase.order", "read", [po], ["invoice_ids"])[0]["invoice_ids"]
    line = env.call("account.move.line", "search", [("move_id", "in", bill), ("product_id", "=", air)])
    env.call("account.move", "write", bill, {"invoice_date": env.call("account.move", "read", bill, ["date"])[0]["date"],
                                             "invoice_line_ids": [(1, line[0], {"price_unit": 9.9})]})
    _call(env, "account.move", "action_post", bill)
    _install(env, ["stock_landed_costs"])
    freight = env.call("product.product", "create", {"name": "Freight", "type": "service", "landed_cost_ok": True, "split_method_landed_cost": "by_quantity"})
    receipt = env.call("stock.picking", "search", [("purchase_id", "=", po), ("picking_type_id.code", "=", "incoming")])
    lc = env.call("stock.landed.cost", "create", {"picking_ids": [(6, 0, receipt)],
                                                  "cost_lines": [(0, 0, {"product_id": freight, "price_unit": 18, "split_method": "by_quantity"})]})
    _call(env, "stock.landed.cost", "compute_landed_cost", [lc])
    _call(env, "stock.landed.cost", "button_validate", [lc])
    closing = env.call("res.company", "action_close_stock_valuation", [_id(env, "res.company", [])])
    _call(env, "account.move", "action_post", [closing["res_id"]])
    env.call("product.category", "write", [filters], {"property_valuation": "real_time"})
    so = sell("Garage Sud", 2)
    wizard = env.call("sale.advance.payment.inv", "create", {"advance_payment_method": "delivered", "sale_order_ids": [(6, 0, [so])]})
    _call(env, "sale.advance.payment.inv", "create_invoices", [wizard])
    _call(env, "account.move", "action_post", env.call("sale.order", "read", [so], ["invoice_ids"])[0]["invoice_ids"])


SEEDS = {
    "ch06": seed_ch06, "ch09": seed_ch09, "ch10": seed_ch10, "ch11": seed_ch11,
    "ch12": seed_ch12, "ch15": seed_ch15, "ch32": seed_ch32, "ch33": seed_ch33,
    "ch34": seed_ch34, "ch35": seed_ch35, "ch39": seed_ch39, "ch40": seed_ch40,
    "ch41": seed_ch41,
    "ch21": seed_ch21, "ch22": seed_ch22, "ch23": seed_ch23, "ch24": seed_ch24,
    "ch25": seed_ch25, "ch26": seed_ch26, "ch27": seed_ch27, "ch28": seed_ch28,
    "ch29": seed_ch29, "ch30": seed_ch30, "ch49": seed_ch49,
    "inv01": seed_inv01, "inv02": seed_inv02, "inv03": seed_inv03, "inv04": seed_inv04,
    "inv05": seed_inv05, "inv06": seed_inv06, "inv07": seed_inv07, "inv08": seed_inv08, "inv09": seed_inv09, "inv10": seed_inv10,
    "inv11": seed_inv11, "inv12": seed_inv12,
}
# ponytail: ch42's website order and POS session are not redone; no later chapter reads
# them, so only its installs are replayed and its own checks are skipped
CHECKS_NOT_REPLAYED = {"ch42"}


def _installs(chapter, target, db):
    if db == "tutorial":
        # all code goes in where chapter 8 first installs LibreFleet
        return [m for m in _code_for(target) if m in TUTORIAL_CODE] if chapter == "ch08" else []
    return INSTALLS.get(chapter, [])


def _replay(target, db):
    track = {"tutorial": TUTORIAL, "functional": FUNCTIONAL, "warehouse": WAREHOUSE}[db]
    chapters = [c for c in ORDER[:ORDER.index(target)] if c in track and c not in NOT_REPLAYED]
    if target == "ch53" and db == "functional":
        # ponytail: ch53 only reads Part 4-5 invoices; skipping ch49-51 spares the OCA clones
        chapters = [c for c in chapters if c <= "ch42"]
    return chapters


def _workspace():
    """The reader's workspace when start runs from it: the starter's compose file next to addons/."""
    here = os.getcwd()
    if os.path.isfile(os.path.join(here, "docker-compose.yml")) and os.path.isdir(os.path.join(here, "addons")):
        return here
    return None


def _local_version(ws, module):
    try:
        with open(os.path.join(ws, "addons", module, "__manifest__.py")) as f:
            return ast.literal_eval(f.read()).get("version")
    except (OSError, ValueError, SyntaxError):
        return None


def _fetch(prefixes):
    """Download this repository once; {path under code/checkpoints/: bytes} for the prefixes."""
    wanted = tuple(CHECKPOINT_PREFIX + p for p in prefixes)
    files = {}
    with urllib.request.urlopen(FETCH_URL) as resp, tarfile.open(fileobj=resp, mode="r|gz") as tar:
        for member in tar:
            if member.isfile() and member.name.startswith(wanted) and ".." not in member.name.split("/"):
                files[member.name[len(CHECKPOINT_PREFIX):]] = tar.extractfile(member).read()
    return files


def _write_tree(files, prefix, dest):
    for name, data in files.items():
        if name.startswith(prefix):
            path = os.path.join(dest, *name[len(prefix):].split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)


def _oca_needs(ws, repos):
    """(repos to clone, addons_path entries to add, whether the ./oca mount is missing)."""
    with open(os.path.join(ws, "odoo.conf")) as f:
        conf = f.read()
    with open(os.path.join(ws, "docker-compose.yml")) as f:
        compose = f.read()
    clone = [r for r in repos if not os.path.isdir(os.path.join(ws, "oca", r))]
    paths = [r for r in repos if "/mnt/oca/" + r not in conf]
    return clone, paths, "./oca:/mnt/oca" not in compose


def _oca_setup(ws, clone, paths, mount):
    """What chapter 49 does by hand: clone, mount ./oca, add each repository to addons_path."""
    for repo in clone:
        subprocess.run(["git", "clone", "--depth", "1", "-b", "19.0",
                        "https://github.com/OCA/%s.git" % repo, os.path.join("oca", repo)],
                       cwd=ws, check=True)
    if paths:
        conf_path = os.path.join(ws, "odoo.conf")
        with open(conf_path) as f:
            lines = f.read().split("\n")
        for i, line in enumerate(lines):
            if line.replace(" ", "").startswith("addons_path="):
                lines[i] = line.rstrip() + "".join(",/mnt/oca/" + r for r in paths)
        with open(conf_path, "w") as f:
            f.write("\n".join(lines))
    if mount:
        compose_path = os.path.join(ws, "docker-compose.yml")
        with open(compose_path) as f:
            compose = f.read()
        anchor = "- ./addons:/mnt/extra-addons"
        line = next(l for l in compose.split("\n") if anchor in l)
        with open(compose_path, "w") as f:
            f.write(compose.replace(line, line + "\n" + line.replace(anchor, "- ./oca:/mnt/oca"), 1))
    ignore = os.path.join(ws, ".gitignore")
    current = open(ignore).read() if os.path.exists(ignore) else ""
    if "oca/" not in current.split("\n"):
        with open(ignore, "a") as f:
            f.write(("" if current.endswith("\n") or not current else "\n") + "oca/\n")


def _restart_odoo(a, ws, recreate):
    """Restart the reader's Odoo (recreate it after a compose change) and wait until it answers."""
    if recreate:
        subprocess.run(["docker", "compose", "up", "-d"], cwd=ws, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "compose", "restart", "odoo"], cwd=ws, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    common = xmlrpc.client.ServerProxy(a.url + "/xmlrpc/2/common")
    for _ in range(120):
        try:
            common.version()
            return
        except (OSError, xmlrpc.client.Error):
            time.sleep(1)
    raise RuntimeError("Odoo did not answer within two minutes of the restart")


class MasterPasswordRefused(Exception):
    pass


def _master(a, ws, op, *args):
    """A database-manager call. A reader who created a database in the browser left the
    master password the manager generated in memory, so on a refusal restart Odoo once
    (back to odoo.conf's) and retry."""
    dbs = xmlrpc.client.ServerProxy(a.url + "/xmlrpc/2/db")
    for attempt in (1, 2):
        try:
            return getattr(dbs, op)(a.master_password, *args)
        except xmlrpc.client.Fault as e:
            if e.faultCode != 3 and "Access Denied" not in e.faultString:
                raise
            if attempt == 2 or not ws:
                raise MasterPasswordRefused()
            print("the master password was refused, probably the one the database manager "
                  "generated for you: restarting Odoo, which puts odoo.conf's back ...")
            _restart_odoo(a, ws, recreate=False)


def _missing_code(env, modules, target):
    """Instructions for every module the server cannot see at the version needed."""
    rows = env.call("ir.module.module", "search_read", [("name", "in", modules)],
                    fields=["name", "installed_version", "state"])
    found = {r["name"]: r for r in rows}
    code = _code_for(target)
    fixes, repos = [], []
    for module in modules:
        row = found.get(module)
        if module in code:
            version, checkpoint = code[module]
            if not row or row["installed_version"] != version or row["state"] == "uninstallable":
                have = row["installed_version"] if row else "nothing"
                fixes.append((
                    "%s %s from code/checkpoints/%s (the server sees %s):\n"
                    "    mkdir -p .checkpoints && curl -sL %s \\\n"
                    "      | tar -xz -C .checkpoints --strip-components=3 'odoolings-main/code/checkpoints/%s'\n"
                    "    rm -rf addons/%s && cp -r .checkpoints/%s/%s addons/"
                    % (module, version, checkpoint, have, FETCH_URL, checkpoint, module, checkpoint, module)))
        elif not row or row["state"] == "uninstallable":
            if module in OCA_REPOS:
                repos += [r for r in OCA_REPOS[module] if r not in repos]
            else:
                fixes.append("%s: the server cannot find this module" % module)
    if repos:
        fixes.append(
            "the OCA repositories %s, as chapter 49 sets them up:\n%s\n"
            "    then mount them, under the odoo service's volumes in docker-compose.yml:\n"
            "      - ./oca:/mnt/oca\n"
            "    and append each one to addons_path in odoo.conf: %s"
            % (", ".join(repos),
               "\n".join("    git clone --depth 1 -b 19.0 https://github.com/OCA/%s.git oca/%s" % (r, r)
                         for r in repos),
               ",".join("/mnt/oca/" + r for r in repos)))
    return fixes


def _run_checks(env, chapter):
    for desc, fn, hint in CHAPTERS[chapter]:
        try:
            fn(env)
        except Exception as e:
            msg = e.faultString.strip().splitlines()[-1] if isinstance(e, xmlrpc.client.Fault) else e
            return "%s: %s" % (desc, msg)
    return None


def _build(a, ws, target, db):
    replay = _replay(target, db)
    modules = [m for c in replay for m in _installs(c, target, db)]
    demo = db == "functional"  # tutorial and warehouse are built without demo data
    print("\ncreating %r%s ..." % (db, " with demo data" if demo else ""))
    _master(a, ws, "create_database", db, demo, "en_US", a.password, a.user)
    env = Env(a.url, db, a.user, a.password)
    _call(env, "ir.module.module", "update_list")
    fixes = _missing_code(env, modules, target)
    if fixes:
        _master(a, ws, "drop", db)
        print("\nOdoo cannot see the code chapter %s starts from. Run start from your workspace "
              "folder (the one with docker-compose.yml) and it sets this up itself, or do it by "
              "hand, then run start again:\n" % target)
        for fix in fixes:
            print("  - " + fix)
        print("  - then restart Odoo: it reads addons_path, and leaves out any folder that "
              "holds no module yet, only when it starts:\n    docker compose up -d && docker compose restart odoo")
        return 1
    for chapter in replay:
        steps = []
        mods = _installs(chapter, target, db)
        if mods:
            print("  %s  installing %s ..." % (chapter, ", ".join(mods)))
            _install(env, mods)
            steps.append("installed " + ", ".join(mods))
        if chapter in SEEDS:
            SEEDS[chapter](env)
            steps.append("redid its hands-on")
        if chapter in CHAPTERS and chapter not in CHECKS_NOT_REPLAYED:
            failure = _run_checks(env, chapter)
            if failure:
                print("✘ %s  %s" % (chapter, "; ".join(steps)))
                print("    check failed: %s" % failure)
                print("    This is a bug in odoolings, not in your work: please report it.")
                return 1
            steps.append("%d checks pass" % len(CHAPTERS[chapter]))
        if steps:
            print("✔ %s  %s" % (chapter, "; ".join(steps)))
    return 0


def _confirm(a, lines):
    """Show what start will do; ask only when it moves, renames or edits something you have."""
    print("\nThis will:\n" + "\n".join("  - " + line for line, _ in lines))
    if a.yes or not any(asks for _, asks in lines):
        return True
    if not sys.stdin.isatty():
        print("\nRun it again with --yes to go ahead.")
        return False
    return input("\nGo ahead? [Y/n] ").strip().lower() in ("", "y", "yes")


def cmd_start(a):
    sys.stdout.reconfigure(line_buffering=True)
    target = a.chapter
    if target not in ORDER:
        print("Unknown chapter %r. Use the id on the page, e.g. ch22, boss2 or inv01." % target)
        return 2
    if target in SELF_BUILT:
        print("Chapter %s creates the %r database itself: start it from the top."
              % (target, SELF_BUILT[target]))
        return 0
    targets = [db for db, track in (("tutorial", TUTORIAL), ("functional", FUNCTIONAL), ("warehouse", WAREHOUSE))
               if target in track]
    ws = _workspace()
    plan, stamp = [], time.strftime("%Y%m%d-%H%M%S")

    code = {m: vc for m, vc in _code_for(target).items() if m in TUTORIAL_CODE}
    fetch = []  # (module, version, checkpoint)
    if ws and "tutorial" in targets and "ch08" in _replay(target, "tutorial"):
        for module, (version, checkpoint) in sorted(code.items()):
            have = _local_version(ws, module)
            if have != version:
                fetch.append((module, version, checkpoint))
                plan.append(("put %s %s (code/checkpoints/%s) in addons/%s%s"
                             % (module, version, checkpoint, module,
                                ";\n    your copy (%s) moves to .checkpoints/replaced/%s-%s"
                                % (have or "unreadable", module, stamp)
                                if os.path.isdir(os.path.join(ws, "addons", module)) else ""),
                             os.path.isdir(os.path.join(ws, "addons", module))))
    configs = []
    if target in NEEDS_PRE_COMMIT:
        configs = [f for f in PRE_COMMIT_FILES if not (ws and os.path.exists(os.path.join(ws, f)))]
        if ws and configs:
            plan.append(("add chapter 44's %s to your workspace" % ", ".join(configs), False))
    repos = []
    if "functional" in targets:
        for chapter in _replay(target, "functional"):
            for module in INSTALLS.get(chapter, []):
                repos += [r for r in OCA_REPOS.get(module, []) if r not in repos]
    clone, paths, mount = _oca_needs(ws, repos) if ws and repos else ([], [], False)
    if clone:
        plan.append(("clone OCA/%s into oca/" % ", OCA/".join(clone), False))
    if paths or mount:
        plan.append(("edit %s the way chapter 49 does, so Odoo sees oca/"
                     % " and ".join(n for n, need in (("docker-compose.yml", mount), ("odoo.conf", paths)) if need),
                     True))
    restart = bool(fetch or clone or paths or mount)
    if restart:
        plan.append(("restart Odoo so it sees the new code", False))

    try:
        existing = xmlrpc.client.ServerProxy(a.url + "/xmlrpc/2/db").list() if targets else []
    except OSError:
        print("Odoo is not answering at %s. Start it from your workspace folder with "
              "`docker compose up -d`, then run start again." % a.url)
        return 1
    backups = {}
    for db in targets:
        replay = _replay(target, db)
        if replay and all(c.startswith("ch") for c in replay):
            first, last = int(replay[0][2:]), int(replay[-1][2:])
            span = "chapter %d" % first if first == last else "chapters %d to %d" % (first, last)
        else:
            span = replay[0] if len(replay) == 1 else "%s to %s" % (replay[0], replay[-1]) if replay else ""
        what = ("build %r by replaying %s and checking each (%s)"
                % (db, span, "a few minutes" if db == "functional" else "a minute or two")
                if replay else "create an empty %r" % db)
        if db in existing:
            if a.reset:
                plan.append(("drop your current %r for good (--reset), then %s" % (db, what), True))
            else:
                backups[db] = "%s_before_%s" % (db, target)
                if backups[db] in existing:
                    backups[db] += "_" + stamp.replace("-", "_")
                plan.append(("keep your current %r as %r, then %s" % (db, backups[db], what), True))
        else:
            plan.append((what, False))

    if targets:
        print("Chapter %s starts from %s, as the chapters before it leave %s."
              % (target, " and ".join(repr(db) for db in targets), "them" if len(targets) > 1 else "it"))
    else:
        print("Chapter %s needs no database." % target)
    if not ws and (code and "tutorial" in targets and "ch08" in _replay(target, "tutorial") or repos):
        print("\nRun start from your workspace folder, the one with docker-compose.yml and "
              "addons/: it sets up the %s chapter %s builds on from there."
              % ("LibreFleet code" if not repos else "OCA repositories", target))
        return 1
    if plan and not _confirm(a, plan):
        return 1

    if fetch or (ws and configs):
        print("\nfetching checkpoints ...")
        files = _fetch(["%s/%s/" % (cp, m) for m, _, cp in fetch] + ["ch44/" + f for f in configs if ws])
        for module, version, checkpoint in fetch:
            dest = os.path.join(ws, "addons", module)
            if os.path.isdir(dest):
                keep = os.path.join(ws, ".checkpoints", "replaced", "%s-%s" % (module, stamp))
                os.makedirs(os.path.dirname(keep), exist_ok=True)
                shutil.move(dest, keep)
            _write_tree(files, "%s/%s/" % (checkpoint, module), dest)
        for name in configs if ws else []:
            if "ch44/" + name in files:
                with open(os.path.join(ws, name), "wb") as f:
                    f.write(files["ch44/" + name])
    if clone or paths or mount:
        print("\nsetting up the OCA repositories ...")
        _oca_setup(ws, clone, paths, mount)
    if restart:
        print("restarting Odoo ...")
        try:
            _restart_odoo(a, ws, recreate=mount)
        except (OSError, subprocess.CalledProcessError, RuntimeError) as e:
            print("Could not restart Odoo (%s). Run `docker compose up -d && docker compose "
                  "restart odoo` yourself, then start again: the code is already in place." % e)
            return 1

    try:
        for db in targets:
            if db in existing:
                if a.reset:
                    _master(a, ws, "drop", db)
                else:
                    _master(a, ws, "rename", db, backups[db])
            rc = _build(a, ws, target, db)
            if rc:
                return rc
    except MasterPasswordRefused:
        print("\nThe master password was refused. The starter's is 'admin'; if you changed it "
              "in odoo.conf, pass --master-password. One the database manager generated for "
              "you lasts only until the next restart: `docker compose restart odoo`, then "
              "run start again.")
        return 1

    if targets:
        print("\nReady for chapter %s. Log in at %s as %s / %s." % (target, a.url, a.user, a.password))
    else:
        print("\nNothing else to set up: this chapter needs no database.")
    for db, backup in backups.items():
        print("Your previous %r is kept as %r (drop it in the database manager when you no "
              "longer need it)." % (db, backup))
    if configs and not ws:
        print("\nThis chapter runs chapter 44's pre-commit stack. Put its three config files at "
              "your workspace root:\n    mkdir -p .checkpoints && curl -sL %s \\\n"
              "      | tar -xz -C .checkpoints --strip-components=3 'odoolings-main/code/checkpoints/ch44'\n"
              "    cp .checkpoints/ch44/.pre-commit-config.yaml .checkpoints/ch44/.ruff.toml "
              ".checkpoints/ch44/.pylintrc ." % FETCH_URL)
    if target in NEEDS_PRE_COMMIT:
        print("\n" + PRE_COMMIT_NOTE)
    if target in NEEDS_GH:
        print("\n" + GH_NOTE)
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
    p.add_argument("command", choices=["check", "list", "snapshot", "diff", "start"])
    p.add_argument("chapter", nargs="?", help="e.g. ch05 (not needed by snapshot/diff)")
    p.add_argument("--url", default="http://localhost:8069")
    p.add_argument("--db", default="tutorial")
    p.add_argument("--user", default="admin")
    p.add_argument("--password", default="admin")
    p.add_argument("--master-password", default="admin", help="start: odoo.conf's admin_passwd")
    p.add_argument("--reset", action="store_true",
                   help="start: drop an existing database instead of keeping it as a backup")
    p.add_argument("--yes", "-y", action="store_true", help="start: do not ask before going ahead")
    a = p.parse_args(argv)

    if a.command == "start":
        if not a.chapter:
            p.error("start needs a chapter, e.g.: odoolings.py start ch22")
        return cmd_start(a)
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
