document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn  = document.getElementById('sidebarToggle');
  const toggleIcon = document.getElementById('sidebarToggleIcon');
  const sidebar    = document.querySelector('.sidebar');

  if (!toggleBtn || !toggleIcon || !sidebar) return;

  // Initialize the correct icon based on sidebar state
  if (sidebar.classList.contains('collapsed')) {
    toggleIcon.textContent = '☰';        // show “open” if collapsed
    toggleBtn.setAttribute('aria-label','Open sidebar');
  } else {
    toggleIcon.textContent = '✖';        // show “close” if open
    toggleBtn.setAttribute('aria-label','Close sidebar');
  }

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');

    if (sidebar.classList.contains('collapsed')) {
      toggleIcon.textContent = '☰';
      toggleBtn.setAttribute('aria-label','Open sidebar');
    } else {
      toggleIcon.textContent = '✖';
      toggleBtn.setAttribute('aria-label','Close sidebar');
    }
  });
});
