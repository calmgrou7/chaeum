const siteUrl = new URL('/', location.href).href;
const notice = document.getElementById('notice');
const dialog = document.getElementById('copy-dialog');
let hideTimer;
function notify(message) {
  clearTimeout(hideTimer);
  notice.textContent = message;
  notice.classList.add('visible');
  hideTimer = setTimeout(() => notice.classList.remove('visible'), 2700);
}
async function copy(text, success, title) {
  try {
    await navigator.clipboard.writeText(text);
    notify(success);
  } catch {
    const box = dialog.querySelector('textarea');
    dialog.querySelector('h2').textContent = title;
    box.value = text;
    dialog.showModal();
    box.focus();
    box.select();
  }
}
document.querySelector('[data-share]').addEventListener('click', async () => {
  if (navigator.share) {
    try {
      await navigator.share({ title: document.title, url: siteUrl });
      return;
    } catch (error) {
      if (error.name === 'AbortError') return;
    }
  }
  await copy(siteUrl, '소개 페이지 링크를 복사했습니다.', '소개 페이지 링크');
});
document.getElementById('copy-intro').addEventListener('click', () => {
  const referral = document.getElementById('referral-text').textContent.trim();
  copy(referral, '소개 문구를 복사했습니다.', '소개 문구');
});
dialog.querySelector('button').addEventListener('click', () => dialog.close());
