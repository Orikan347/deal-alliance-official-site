document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-local-waitlist]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const result = form.querySelector('.local-result');
      result.classList.add('show');
      result.textContent = '這是本機候選站示意：未送出任何資料，也沒有建立候補名單。';
    });
  });
});
