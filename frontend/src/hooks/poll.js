export function waitForReport(fetchReport, onUpdate, onError) {
  const controller = new AbortController();
  let timer;
  async function update() {
    try {
      const report = await fetchReport(controller.signal);
      if (controller.signal.aborted) return;
      onUpdate(report);
      if (report.status === 'queued') timer = setTimeout(update, 750);
    } catch (error) {
      if (!controller.signal.aborted) onError(error);
    }
  }
  update();
  return () => { controller.abort(); clearTimeout(timer); };
}
