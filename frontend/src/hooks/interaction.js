export function formSubmit(form, handler) {
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('[type="submit"]');
    const message = form.querySelector('[role="alert"]');
    button.disabled = true;
    if (message) message.textContent = '';
    try {
      await handler(new FormData(form));
    } catch (error) {
      if (message) message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

export async function buttonAction(button, message, job) {
  button.disabled = true;
  message.textContent = '';
  try { await job(); }
  catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; }
}
