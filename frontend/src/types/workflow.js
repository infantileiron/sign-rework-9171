/** @typedef {{code: string, title: string, crew: string, minutes: number, shots: number, switches: number, hours: number}} Order */
/** @typedef {{id: number, name: string, alpha: number, features: string[]}} Plan */
/** @typedef {{id: number, plan_id: number, plan_name: string, holdout: string, fingerprint: string, status: 'queued'|'succeeded'|'failed'|'published'}} Report */
/** @typedef {{serial: string, allocated: number, ledger: number|null, shared_with: string[], reason: 'matched'|'missing'|'unbalanced'}} SerialShare */
/** @typedef {{order: string, state: 'aligned'|'waiting'|'unsettled', pending_hours: number|null, sample_hours: number|null, committed_hours: number|null, serials: SerialShare[], missing: string[], unbalanced: string[], waiting_on: string[], component: string[], component_waiting: {serial: string, reason: string, orders: string[]}[]}} OrderSettlement */
/** @typedef {{serial: string, allocated: number, ledger: number|null, reason: 'matched'|'missing'|'unbalanced', orders: string[]}} SerialState */
/** @typedef {{orders: Record<string, OrderSettlement>, serials: Record<string, SerialState>, components: {orders: string[], state: string, waiting_on: string[]}[], waiting_orders: string[], missing_serials: string[], unbalanced_serials: string[], switched?: string[][], sheet_no?: string}} SettlementState */
