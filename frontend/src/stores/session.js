const key = 'sign-rework-session';
export const session = {
  get: () => sessionStorage.getItem(key),
  set: token => sessionStorage.setItem(key, token),
  clear: () => sessionStorage.removeItem(key),
};
