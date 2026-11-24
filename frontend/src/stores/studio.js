export const studio = {
  user: null,
  /** @type {import('../types/workflow.js').Order[]} */
  orders: [],
  /** @type {import('../types/workflow.js').Plan[]} */
  plans: [],
  /** @type {import('../types/workflow.js').Report[]} */
  reports: [],
  crews: [],
  orderFilter: '',
};

export const crewName = code => studio.crews.find(crew => crew.code === code)?.name ?? code;
export const canEdit = () => studio.user.role === 'analyst';
