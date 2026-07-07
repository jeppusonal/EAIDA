# Synthetic dataset generation plan (MVP)

## Design goal

Generate a retail dataset small enough to run entirely on a laptop in minutes, but realistic enough that a "why did revenue drop in Sydney" investigation produces a genuine, traceable answer rather than random noise.

## Scale (MVP — deliberately smaller than the full-platform target)

| Entity | MVP row count | Full-platform target (later) |
|---|---|---|
| Customers | 5,000 | 100,000 |
| Stores | 8 | 100 warehouses/stores |
| Products | 200 | 10,000 |
| Orders | ~50,000 | 1,000,000 |
| Order items | ~120,000 | proportional |
| Returns | ~2,500 | 50,000 |
| Marketing campaigns | ~30 | proportional |

Scaling up later is a config change (row-count constants), not a rewrite — the generation logic is written to be size-agnostic.

## Geography

8 stores across 5 Australian cities: Sydney (x2 stores), Melbourne (x2), Brisbane, Perth, Adelaide, Canberra. Sydney gets two stores deliberately, since it's the city under investigation.

## The engineered anomaly

Order history spans 18 months. For the **final 2 months** of that window, Sydney stores get:
- Order volume reduced by ~35–40% relative to their trend (via a lower per-day order-generation probability)
- A mild uptick in returns rate
- Marketing spend targeted at Sydney reduced in the same window

This isn't randomly injected noise — it's a deterministic rule (seeded RNG) so the "investigation" later has a real, reproducible root cause to find: less marketing spend → fewer orders → lower revenue, compounded slightly by returns. Other cities follow normal seasonal variation with no engineered drop.

## Generation order and dependencies

Generation must respect foreign key dependencies:

1. `customers` — no dependencies
2. `products` — no dependencies
3. `stores` — no dependencies
4. `orders` — depends on customers, stores
5. `order_items` — depends on orders, products
6. `inventory` — depends on stores, products
7. `returns` — depends on orders, order_items, products
8. `marketing_campaigns` — no hard dependency, but city_target should match store cities

This is also the notebook execution order.

## Validation checks (notebook 08)

- Row counts match expected ranges
- No null primary/foreign keys
- Referential integrity: every `order.customer_id` exists in `customers`, every `order_item.order_id` exists in `orders`, etc.
- Date ranges are sane (no orders before store `open_date`)
- The Sydney anomaly is visible in a monthly revenue-by-city aggregation — this is our sanity check that the synthetic data will actually support the MVP's target question
