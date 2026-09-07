LibreFleet manages a vehicle workshop's day to day: customers and their vehicles,
service orders that move through a kanban of stages, parts consumption and margin
tracking per order, technician assignment, and a small OWL dashboard summarizing
jobs per technician.

Booking conflicts are enforced at the model level: two service orders cannot claim
the same vehicle over an overlapping window. Orders with a negative margin require
manager approval through a wizard before they can be confirmed.

Customers can follow their vehicle's service history from the portal, and get a
QWeb-generated PDF report once a job completes.
