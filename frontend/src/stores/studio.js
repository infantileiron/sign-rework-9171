export const studio = {
  user: null,
  /** @type {import('../types/workflow.js').Order[]} */
  orders: [],
  /** @type {import('../types/workflow.js').Plan[]} */
  plans: [],
  /** @type {import('../types/workflow.js').Report[]} */
  reports: [],
  /** @type {import('../types/workflow.js').SettlementState} */
  settlement: {orders: {}, serials: {}, components: [], waiting_orders: [], missing_serials: [], unbalanced_serials: []},
  crews: [],
  orderFilter: '',
};

export const crewName = code => studio.crews.find(crew => crew.code === code)?.name ?? code;
export const canEdit = () => studio.user.role === 'analyst';
export const settlementOf = code => studio.settlement.orders[code] ?? null;
