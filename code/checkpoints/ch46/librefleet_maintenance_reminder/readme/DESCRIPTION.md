Schedules a "Schedule maintenance" activity on any LibreFleet vehicle that hasn't
had a completed service order in the last 180 days, checked daily by a scheduled
action and runnable on demand from the Vehicles list.

The reminder clears itself automatically the moment a service order on that
vehicle reaches the Done stage, and running the check twice never creates a
second reminder for the same vehicle.

This module extends `librefleet.vehicle`; it has no models or views of its own.
