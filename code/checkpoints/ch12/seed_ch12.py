# ch12 seed data: paste into `odoo shell` (docker compose exec -T odoo odoo shell
# -c /etc/odoo/odoo.conf -d tutorial --no-http). Assumes the ch06-ch11 state:
# vehicles ZH 468 202 / BE 30 447, the three service types, and user tina.
anna, beat = env["res.partner"].create([
    {"name": "Anna Keller"}, {"name": "Beat Muster"},
])
zh = env["librefleet.vehicle"].search([("license_plate", "=", "ZH 468 202")])
be = env["librefleet.vehicle"].search([("license_plate", "=", "BE 30 447")])
zh.owner_id, be.owner_id = anna, beat

oil_filter, oil, pads = env["librefleet.part"].create([
    {"name": "Oil filter", "code": "OF-102", "standard_cost": 12.0, "list_price": 24.5},
    {"name": "Engine oil 5W30 (1l)", "code": "OIL-5W30", "standard_cost": 9.5, "list_price": 18.9},
    {"name": "Brake pads, front", "code": "BP-201", "standard_cost": 35.0, "list_price": 79.0},
])

tina = env["res.users"].search([("login", "=", "tina")])
oil_change = env["librefleet.service.type"].search([("name", "=", "Oil change")])
brake_insp = env["librefleet.service.type"].search([("name", "=", "Brake inspection")])

o1 = env["librefleet.service.order"].create({
    "vehicle_id": zh.id,
    "service_type_id": oil_change.id,
    "technician_ids": [(4, tina.id)],
    "scheduled_start": "2026-07-16 08:00:00",
    "scheduled_end": "2026-07-16 09:00:00",
    "line_ids": [
        (0, 0, {"part_id": oil_filter.id, "qty": 1, "price_unit": 24.5}),
        (0, 0, {"part_id": oil.id, "qty": 4, "price_unit": 18.9}),
    ],
})
o2 = env["librefleet.service.order"].create({
    "vehicle_id": be.id,
    "service_type_id": brake_insp.id,
    "scheduled_start": "2026-07-17 09:00:00",
    "scheduled_end": "2026-07-17 10:30:00",
})
env.cr.commit()
print("seeded:", o1.display_name, "/", o2.display_name)
