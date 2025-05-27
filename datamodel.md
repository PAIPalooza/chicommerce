## Entity-Relationship Overview

```
Product --< Template --< CustomizationZone
Product --< OptionSet --< Option
CustomizationSession --< SessionItem >-- Product (via Template)
Order --< OrderItem >-- CustomizationSession

Product ---< Inventory

WebhookLog (independent)
```

---

## 1. `Product`

Stores base product information.

| Column        | Type              | Constraints                     | Description               |
| ------------- | ----------------- | ------------------------------- | ------------------------- |
| `id`          | UUID              | PK, default `gen_random_uuid()` | Unique identifier         |
| `name`        | VARCHAR(255)      | NOT NULL                        | Product name              |
| `description` | TEXT              |                                 | Product description       |
| `base_price`  | DECIMAL(10,2)     | NOT NULL, ≥ 0                   | Base price                |
| `is_active`   | BOOLEAN           | NOT NULL, default TRUE          | Availability flag         |
| `created_at`  | TIMESTAMP WITH TZ | NOT NULL, default now()         | Record creation timestamp |
| `updated_at`  | TIMESTAMP WITH TZ | NOT NULL, default now()         | Last update timestamp     |

Indexes:

* PK on `id`
* Index on `is_active` for filtering

---

## 2. `Template`

Defines customization template for each product.

| Column       | Type              | Constraints                          | Description                                      |
| ------------ | ----------------- | ------------------------------------ | ------------------------------------------------ |
| `id`         | UUID              | PK, default `gen_random_uuid()`      | Template ID                                      |
| `product_id` | UUID              | FK → `product.id`, ON DELETE CASCADE | Associated product                               |
| `version`    | INT               | NOT NULL                             | Template version (incremental)                   |
| `definition` | JSONB             | NOT NULL                             | JSON schema for zones (text, image, color, etc.) |
| `is_default` | BOOLEAN           | NOT NULL, default FALSE              | Flag for default template per product            |
| `created_at` | TIMESTAMP WITH TZ | NOT NULL, default now()              | Creation timestamp                               |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, default now()              | Last update timestamp                            |

Indexes:

* Unique on (`product_id`, `version`)
* Partial unique on (`product_id`) where `is_default` = TRUE

---

## 3. `CustomizationZone`

Stores individual zones within a template for granular validation.

| Column        | Type         | Constraints                           | Description                                 |
| ------------- | ------------ | ------------------------------------- | ------------------------------------------- |
| `id`          | UUID         | PK, default `gen_random_uuid()`       | Zone ID                                     |
| `template_id` | UUID         | FK → `template.id`, ON DELETE CASCADE | Parent template                             |
| `key`         | VARCHAR(100) | NOT NULL                              | Zone identifier (e.g., "text\_line1")       |
| `type`        | VARCHAR(50)  | NOT NULL                              | Enum: 'text', 'image', 'color', 'shape'     |
| `config`      | JSONB        |                                       | Zone-specific settings (maxLength, formats) |
| `order_index` | INT          | NOT NULL                              | Determines rendering order                  |

Indexes:

* Unique on (`template_id`, `key`)
* Index on (`template_id`, `order_index`)

---

## 4. `OptionSet`

Groups related options (e.g., sizes, finishes).

| Column       | Type         | Constraints                          | Description               |
| ------------ | ------------ | ------------------------------------ | ------------------------- |
| `id`         | UUID         | PK, default `gen_random_uuid()`      | Option set ID             |
| `product_id` | UUID         | FK → `product.id`, ON DELETE CASCADE | Associated product        |
| `name`       | VARCHAR(100) | NOT NULL                             | Set name (e.g., "Size")   |
| `multiple`   | BOOLEAN      | NOT NULL, default FALSE              | Allow multiple selections |

Indexes:

* Index on `product_id`

---

## 5. `Option`

Individual selectable option within a set.

| Column          | Type          | Constraints                            | Description                   |
| --------------- | ------------- | -------------------------------------- | ----------------------------- |
| `id`            | UUID          | PK, default `gen_random_uuid()`        | Option ID                     |
| `option_set_id` | UUID          | FK → `optionset.id`, ON DELETE CASCADE | Parent option set             |
| `label`         | VARCHAR(100)  | NOT NULL                               | Display label (e.g., "Large") |
| `value`         | VARCHAR(100)  | NOT NULL                               | Internal value                |
| `price_delta`   | DECIMAL(10,2) | NOT NULL, default 0                    | Surcharge for this option     |

Indexes:

* Unique on (`option_set_id`, `value`)

---

## 6. `CustomizationSession`

Temporary storage for user customization progress.

| Column        | Type              | Constraints                            | Description                       |
| ------------- | ----------------- | -------------------------------------- | --------------------------------- |
| `id`          | UUID              | PK, default `gen_random_uuid()`        | Session ID                        |
| `session_key` | VARCHAR(255)      | NOT NULL, unique                       | Public key stored in cookie       |
| `product_id`  | UUID              | FK → `product.id`, ON DELETE SET NULL  | Product being customized          |
| `template_id` | UUID              | FK → `template.id`, ON DELETE SET NULL | Template version used             |
| `options`     | JSONB             | NOT NULL                               | User inputs for zones and options |
| `status`      | VARCHAR(50)       | NOT NULL, default 'in\_progress'       | Enum: 'in\_progress','completed'  |
| `created_at`  | TIMESTAMP WITH TZ | NOT NULL, default now()                | Timestamp                         |
| `updated_at`  | TIMESTAMP WITH TZ | NOT NULL, default now()                | Timestamp                         |

Indexes:

* Unique on `session_key`
* Index on `status`

---

## 7. `SessionItem`

Links session to finalized cart items (snapshot).

| Column              | Type          | Constraints                             | Description                     |
| ------------------- | ------------- | --------------------------------------- | ------------------------------- |
| `id`                | UUID          | PK, default `gen_random_uuid()`         | Item ID                         |
| `session_id`        | UUID          | FK → `customizationsession.id`, CASCADE | Parent session                  |
| `template_version`  | INT           | NOT NULL                                | Version at snapshot             |
| `options_snapshot`  | JSONB         | NOT NULL                                | Immutable customization payload |
| `price_at_snapshot` | DECIMAL(10,2) | NOT NULL                                | Price calculated at snapshot    |

Indexes:

* Index on `session_id`

---

## 8. `Cart`

Stores session-bound cart info.

| Column        | Type              | Constraints             | Description                    |
| ------------- | ----------------- | ----------------------- | ------------------------------ |
| `session_key` | VARCHAR(255)      | PK                      | Matches `CustomizationSession` |
| `items`       | JSONB             | NOT NULL                | List of `SessionItem.id`s      |
| `updated_at`  | TIMESTAMP WITH TZ | NOT NULL, default now() | Timestamp                      |

---

## 9. `Order`

Permanent record of checkout.

| Column          | Type              | Constraints                     | Description                                       |
| --------------- | ----------------- | ------------------------------- | ------------------------------------------------- |
| `id`            | UUID              | PK, default `gen_random_uuid()` | Order ID                                          |
| `session_key`   | VARCHAR(255)      | NOT NULL                        | References `Cart.session_key`                     |
| `cart_snapshot` | JSONB             | NOT NULL                        | Full cart content at time of order                |
| `total_amount`  | DECIMAL(10,2)     | NOT NULL                        | Final amount paid                                 |
| `status`        | VARCHAR(50)       | NOT NULL, default 'created'     | Enum: created, paid, produced, shipped, delivered |
| `payment_id`    | VARCHAR(255)      |                                 | Gateway transaction reference                     |
| `created_at`    | TIMESTAMP WITH TZ | NOT NULL, default now()         | Timestamp                                         |

Indexes:

* Index on `status`

---

## 10. `OrderItem`

Breaks down order into individual items.

| Column     | Type          | Constraints                               | Description                  |
| ---------- | ------------- | ----------------------------------------- | ---------------------------- |
| `id`       | UUID          | PK, default `gen_random_uuid()`           | Order item ID                |
| `order_id` | UUID          | FK → `order.id`, ON DELETE CASCADE        | Parent order                 |
| `item_id`  | UUID          | FK → `sessionitem.id`, ON DELETE SET NULL | References session snapshot  |
| `quantity` | INT           | NOT NULL, default 1                       | Quantity ordered             |
| `price`    | DECIMAL(10,2) | NOT NULL                                  | Price per unit at order time |

Indexes:

* Index on `order_id`

---

## 11. `Inventory`

Tracks stock levels per product.

| Column       | Type              | Constraints                              | Description       |
| ------------ | ----------------- | ---------------------------------------- | ----------------- |
| `product_id` | UUID              | PK, FK → `product.id`, ON DELETE CASCADE | Product reference |
| `quantity`   | INT               | NOT NULL, default 0                      | Units available   |
| `updated_at` | TIMESTAMP WITH TZ | NOT NULL, default now()                  | Last stock update |

---

## 12. `WebhookLog`

Audits outbound webhook calls.

| Column            | Type              | Constraints                     | Description               |
| ----------------- | ----------------- | ------------------------------- | ------------------------- |
| `id`              | UUID              | PK, default `gen_random_uuid()` | Log ID                    |
| `event_type`      | VARCHAR(100)      | NOT NULL                        | e.g., 'order.created'     |
| `endpoint`        | VARCHAR(255)      | NOT NULL                        | Target URL                |
| `payload`         | JSONB             | NOT NULL                        | Sent data                 |
| `response_status` | INT               |                                 | HTTP status code received |
| `response_body`   | TEXT              |                                 | Response content          |
| `sent_at`         | TIMESTAMP WITH TZ | NOT NULL, default now()         | Timestamp                 |

Indexes:

* Index on `event_type`
* Index on `sent_at`

---

