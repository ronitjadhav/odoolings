Refuses a fixed discount larger than the line unit price.

sale_fixed_discount converts a fixed amount into a percentage and does not cap
it, so a discount above the unit price silently produces a negative subtotal.
That is a reasonable default upstream and the wrong one for us, so this module
adds the constraint without changing theirs.
