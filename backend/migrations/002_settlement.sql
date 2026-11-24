-- 结算补录：记工流水 -> 按工单分摊 -> 整组对齐后切换比选样本。
--
-- 1. work_logs 是记工台账，以流水号为主键；补传同一流水只会覆盖原数，
--    不会重复计入工时。
-- 2. settlement_lines 按结算单保存，(sheet_id, order_code, serial) 为主键。
--    重传同一结算单只替换它自己的行；同一 (工单, 流水) 出现在多张单时，
--    取最近上传的那张的分摊。因此补传重试不会重复累计，也不会误删别单的行。
-- 3. 结算单上的流水号若不在 work_logs（少一笔 / 没到），或同一流水各单分摊
--    合计对不上原数，共用该流水的工单（含间接相连）一起等待切换。
-- 4. orders.hours 是比选实际使用的样本；未对齐的组保持原值，整组对齐后
--    在同一事务内一次性写回。order_settlements 记录最近一次切换，便于复核。

CREATE TABLE IF NOT EXISTS work_logs (
    serial varchar(40) PRIMARY KEY,
    hours double precision NOT NULL CHECK (hours > 0 AND hours <= 100000),
    received_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS settlement_sheets (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sheet_no varchar(64) NOT NULL UNIQUE,
    uploaded_by varchar(100) NOT NULL REFERENCES accounts(email),
    first_uploaded_at timestamptz NOT NULL DEFAULT now(),
    last_uploaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS settlement_lines (
    sheet_id bigint NOT NULL REFERENCES settlement_sheets(id) ON DELETE CASCADE,
    order_code varchar(20) NOT NULL REFERENCES orders(code) ON DELETE CASCADE,
    serial varchar(40) NOT NULL,
    hours double precision NOT NULL CHECK (hours >= 0 AND hours <= 200),
    PRIMARY KEY (sheet_id, order_code, serial)
);

CREATE INDEX IF NOT EXISTS settlement_lines_serial ON settlement_lines (serial);
CREATE INDEX IF NOT EXISTS settlement_lines_order ON settlement_lines (order_code);

CREATE TABLE IF NOT EXISTS order_settlements (
    order_code varchar(20) PRIMARY KEY REFERENCES orders(code) ON DELETE CASCADE,
    committed_hours double precision NOT NULL CHECK (committed_hours >= 0 AND committed_hours <= 200),
    switched_at timestamptz NOT NULL DEFAULT now()
);
