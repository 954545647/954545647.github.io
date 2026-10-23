// Show a recoverable entry screen while the mirrored module graph is loading.
const panel = document.querySelector('#site-startup');
const message = panel?.querySelector('[role="status"]');
const retry = panel?.querySelector('button');
if (retry) retry.onclick = () => location.reload();
const timer = setTimeout(() => {
  if (panel?.isConnected && message) {
    message.textContent = '连接较慢，仍在加载景区。也可以重新打开。';
    retry.hidden = false;
  }
}, 20000);
try {
  await import('./app.js?v=qijiang-v1');
} catch (error) {
  if (panel?.isConnected && message) {
    message.textContent = '景区页面暂时未能加载，请重试。';
    retry.hidden = false;
  }
  console.error('Site startup failed', error);
} finally {
  clearTimeout(timer);
}
